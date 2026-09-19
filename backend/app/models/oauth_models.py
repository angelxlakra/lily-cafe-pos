"""OAuth 2.1 storage for the MCP server.

Rows live in the POS database so that registrations and tokens survive a
restart or redeploy — an assistant that has been connected once should stay
connected. Everything here is written and read only by app.mcp.oauth.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from app.db.session import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class OAuthClient(Base):
    """An assistant registered through Dynamic Client Registration (RFC 7591)."""

    __tablename__ = "oauth_clients"

    client_id = Column(String(64), primary_key=True)
    # The full OAuthClientInformationFull document as issued, including the
    # client secret. The secret is stored in the clear because the token
    # endpoint compares it directly against what the client presents
    # (mcp.server.auth.middleware.client_auth), so a hash would never match.
    client_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)


class OAuthPendingAuthorization(Base):
    """An /authorize request parked while the owner signs in and consents."""

    __tablename__ = "oauth_pending_authorizations"

    txn_id = Column(String(64), primary_key=True)
    client_id = Column(String(64), nullable=False)
    params_json = Column(Text, nullable=False)
    # Failed sign-in attempts against this transaction; caps password guessing.
    attempts = Column(Integer, default=0, nullable=False)
    expires_at = Column(Float, nullable=False)


class OAuthAuthorizationCode(Base):
    """A one-time code handed back to the assistant's redirect URI."""

    __tablename__ = "oauth_authorization_codes"

    code_hash = Column(String(64), primary_key=True)
    client_id = Column(String(64), nullable=False, index=True)
    scopes = Column(String(500), nullable=False, default="")
    code_challenge = Column(String(255), nullable=False)
    redirect_uri = Column(String(2000), nullable=False)
    redirect_uri_provided_explicitly = Column(Boolean, nullable=False)
    resource = Column(String(500), nullable=True)
    subject = Column(String(100), nullable=True)
    expires_at = Column(Float, nullable=False)


class OAuthGrantToken(Base):
    """An issued access or refresh token.

    Only the SHA-256 of the token is kept, so the table cannot be used to
    impersonate a connected assistant. Tokens minted from the same
    authorization share a grant_id, which lets revoking either one drop the
    whole grant as RFC 7009 recommends.
    """

    __tablename__ = "oauth_tokens"

    token_hash = Column(String(64), primary_key=True)
    token_type = Column(String(10), nullable=False)  # "access" or "refresh"
    grant_id = Column(String(64), nullable=False, index=True)
    client_id = Column(String(64), nullable=False, index=True)
    scopes = Column(String(500), nullable=False, default="")
    resource = Column(String(500), nullable=True)
    subject = Column(String(100), nullable=True)
    expires_at = Column(Integer, nullable=True)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
