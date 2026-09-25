"""OAuth 2.1 authorization server for the MCP endpoint.

ChatGPT and Gemini cannot be handed a long-lived API token — they register
themselves and run an authorization code flow. The MCP SDK supplies the
protocol surface (metadata, dynamic registration, PKCE checks, the token
endpoint); this module supplies storage and the one step the SDK leaves to
the application: deciding who the resource owner is and getting their consent.

The resource owner here is the cafe owner. The MCP tools expose the full
financial history, which the REST API already restricts to the owner login,
so a sign-in on the consent screen must be the owner — the admin login is
refused.

Tokens are persisted as SHA-256 hashes, and every issued token is scoped to a
single read-only scope. Nothing in the MCP surface can write to the POS.
"""

import secrets
import time
from contextlib import contextmanager
from hashlib import sha256
from typing import Any

from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    OAuthAuthorizationServerProvider,
    RefreshToken,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.oauth_models import (
    OAuthAuthorizationCode,
    OAuthClient,
    OAuthGrantToken,
    OAuthPendingAuthorization,
)

READ_SCOPE = "cafe:read"

AUTHORIZATION_CODE_TTL = 60  # seconds; the code is redeemed immediately
ACCESS_TOKEN_TTL = 60 * 60
REFRESH_TOKEN_TTL = 60 * 60 * 24 * 30
CONSENT_TTL = 60 * 10
MAX_CONSENT_ATTEMPTS = 5


def _hash(token: str) -> str:
    return sha256(token.encode()).hexdigest()


def _new_secret() -> str:
    """A 256-bit URL-safe token, well above the 128 bits RFC 6749 requires."""
    return secrets.token_urlsafe(32)


@contextmanager
def _session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CafeOAuthProvider(
    OAuthAuthorizationServerProvider[AuthorizationCode, RefreshToken, AccessToken]
):
    """Authorization server backed by the POS database."""

    def __init__(self, consent_url: str, resource_url: str):
        # Where the owner is sent to sign in and approve a connection.
        self._consent_url = consent_url
        # The one resource this server protects. Tokens are bound to it
        # (RFC 8707), and a client that never names a resource — Gemini's
        # connector form has no field for it — gets bound to it by default.
        self.resource_url = resource_url

    # ------------------------------------------------------------------
    # Client registration
    # ------------------------------------------------------------------

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        with _session() as db:
            row = db.get(OAuthClient, client_id)
            if row is None:
                return None
            return OAuthClientInformationFull.model_validate_json(row.client_json)

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        with _session() as db:
            db.merge(
                OAuthClient(
                    client_id=client_info.client_id,
                    client_json=client_info.model_dump_json(),
                )
            )
            db.commit()

    # ------------------------------------------------------------------
    # Authorization
    # ------------------------------------------------------------------

    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        """Park the request and send the owner to the consent screen.

        The code is only minted once the owner has signed in, in
        complete_authorization below.
        """
        txn_id = _new_secret()
        with _session() as db:
            db.add(
                OAuthPendingAuthorization(
                    txn_id=txn_id,
                    client_id=client.client_id,
                    params_json=params.model_dump_json(),
                    expires_at=time.time() + CONSENT_TTL,
                )
            )
            db.commit()
        return f"{self._consent_url}?txn={txn_id}"

    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> AuthorizationCode | None:
        with _session() as db:
            row = db.get(OAuthAuthorizationCode, _hash(authorization_code))
            if row is None or row.client_id != client.client_id:
                return None
            if row.expires_at < time.time():
                db.delete(row)
                db.commit()
                return None
            return AuthorizationCode(
                code=authorization_code,
                scopes=_split_scopes(row.scopes),
                expires_at=row.expires_at,
                client_id=row.client_id,
                code_challenge=row.code_challenge,
                redirect_uri=row.redirect_uri,
                redirect_uri_provided_explicitly=row.redirect_uri_provided_explicitly,
                resource=row.resource,
                subject=row.subject,
            )

    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode
    ) -> OAuthToken:
        with _session() as db:
            # Deleting first makes the code single use: a replay finds nothing.
            row = db.get(OAuthAuthorizationCode, _hash(authorization_code.code))
            if row is None:
                raise ValueError("Authorization code has already been used")
            db.delete(row)

            token = _issue_grant(
                db,
                grant_id=_new_secret(),
                client_id=client.client_id,
                scopes=authorization_code.scopes,
                resource=authorization_code.resource,
                subject=authorization_code.subject,
            )
            db.commit()
        return token

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> RefreshToken | None:
        with _session() as db:
            row = _live_token(db, refresh_token, "refresh")
            if row is None or row.client_id != client.client_id:
                return None
            return RefreshToken(
                token=refresh_token,
                client_id=row.client_id,
                scopes=_split_scopes(row.scopes),
                expires_at=row.expires_at,
                resource=row.resource,
                subject=row.subject,
            )

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        requested = scopes or refresh_token.scopes
        if not set(requested) <= set(refresh_token.scopes):
            raise ValueError("Cannot widen scopes on refresh")

        with _session() as db:
            row = _live_token(db, refresh_token.token, "refresh")
            if row is None:
                raise ValueError("Refresh token is no longer valid")

            # Rotate: the whole previous grant goes, including the access
            # token it was issued alongside.
            _revoke_grant(db, row.grant_id)

            token = _issue_grant(
                db,
                grant_id=_new_secret(),
                client_id=client.client_id,
                scopes=requested,
                resource=refresh_token.resource,
                subject=refresh_token.subject,
            )
            db.commit()
        return token

    # ------------------------------------------------------------------
    # Access tokens
    # ------------------------------------------------------------------

    async def load_access_token(self, token: str) -> AccessToken | None:
        with _session() as db:
            row = _live_token(db, token, "access")
            if row is None:
                return None
            return AccessToken(
                token=token,
                client_id=row.client_id,
                scopes=_split_scopes(row.scopes),
                expires_at=row.expires_at,
                resource=row.resource,
                subject=row.subject,
            )

    async def revoke_token(self, token: AccessToken | RefreshToken) -> None:
        with _session() as db:
            row = db.get(OAuthGrantToken, _hash(token.token))
            if row is None:
                return
            _revoke_grant(db, row.grant_id)
            db.commit()


# ----------------------------------------------------------------------
# Consent, called by the sign-in screen once the owner approves
# ----------------------------------------------------------------------


def take_pending_authorization(
    txn_id: str,
) -> tuple[str, AuthorizationParams] | None:
    """Read a parked request without consuming it: (client_id, params)."""
    with _session() as db:
        row = _live_pending(db, txn_id)
        if row is None:
            return None
        return row.client_id, AuthorizationParams.model_validate_json(row.params_json)


def record_failed_consent_attempt(txn_id: str) -> bool:
    """Count a bad sign-in. Returns False once the transaction is burnt."""
    with _session() as db:
        row = _live_pending(db, txn_id)
        if row is None:
            return False
        row.attempts += 1
        exhausted = row.attempts >= MAX_CONSENT_ATTEMPTS
        if exhausted:
            db.delete(row)
        db.commit()
        return not exhausted


def discard_pending_authorization(txn_id: str) -> None:
    with _session() as db:
        row = db.get(OAuthPendingAuthorization, txn_id)
        if row is not None:
            db.delete(row)
            db.commit()


def complete_authorization(
    txn_id: str, subject: str, default_resource: str
) -> tuple[str, str | None] | None:
    """Mint an authorization code for an approved request.

    Returns the code and the state to hand back, or None if the transaction
    has expired or was already used. A request that named no resource is
    bound to default_resource, the only one this server has.
    """
    with _session() as db:
        pending = _live_pending(db, txn_id)
        if pending is None:
            return None

        params = AuthorizationParams.model_validate_json(pending.params_json)
        code = _new_secret()
        db.add(
            OAuthAuthorizationCode(
                code_hash=_hash(code),
                client_id=pending.client_id,
                scopes=" ".join(params.scopes or [READ_SCOPE]),
                code_challenge=params.code_challenge,
                redirect_uri=str(params.redirect_uri),
                redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
                resource=params.resource or default_resource,
                subject=subject,
                expires_at=time.time() + AUTHORIZATION_CODE_TTL,
            )
        )
        db.delete(pending)
        db.commit()
        return code, params.state


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _split_scopes(scopes: str) -> list[str]:
    return [s for s in (scopes or "").split(" ") if s]


def _live_pending(db: Session, txn_id: str) -> OAuthPendingAuthorization | None:
    row = db.get(OAuthPendingAuthorization, txn_id)
    if row is None:
        return None
    if row.expires_at < time.time():
        db.delete(row)
        db.commit()
        return None
    return row


def _live_token(db: Session, token: str, token_type: str) -> OAuthGrantToken | None:
    row = db.get(OAuthGrantToken, _hash(token))
    if row is None or row.revoked or row.token_type != token_type:
        return None
    if row.expires_at is not None and row.expires_at < int(time.time()):
        return None
    return row


def _revoke_grant(db: Session, grant_id: str) -> None:
    rows = (
        db.query(OAuthGrantToken).filter(OAuthGrantToken.grant_id == grant_id).all()
    )
    for row in rows:
        row.revoked = True


def _issue_grant(
    db: Session,
    grant_id: str,
    client_id: str,
    scopes: list[str],
    resource: str | None,
    subject: str | None,
) -> OAuthToken:
    access_token = _new_secret()
    refresh_token = _new_secret()
    now = int(time.time())
    scope_text = " ".join(scopes)

    common: dict[str, Any] = {
        "grant_id": grant_id,
        "client_id": client_id,
        "scopes": scope_text,
        "resource": resource,
        "subject": subject,
    }
    db.add(
        OAuthGrantToken(
            token_hash=_hash(access_token),
            token_type="access",
            expires_at=now + ACCESS_TOKEN_TTL,
            **common,
        )
    )
    db.add(
        OAuthGrantToken(
            token_hash=_hash(refresh_token),
            token_type="refresh",
            expires_at=now + REFRESH_TOKEN_TTL,
            **common,
        )
    )

    return OAuthToken(
        access_token=access_token,
        token_type="Bearer",
        expires_in=ACCESS_TOKEN_TTL,
        refresh_token=refresh_token,
        scope=scope_text,
    )
