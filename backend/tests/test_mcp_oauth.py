"""End-to-end tests for the MCP OAuth authorization server.

These drive the real HTTP surface the way ChatGPT or Gemini would: discover
the server, register, send the owner to consent, exchange the code, call the
protected endpoint, refresh, revoke.
"""

import base64
import hashlib
import secrets
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings

ISSUER = "http://localhost"
RESOURCE = f"{ISSUER}/mcp"
REDIRECT_URI = "http://localhost:9999/callback"


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def client(db_session, monkeypatch):
    """A test client for the MCP app with OAuth switched on."""
    monkeypatch.setattr(settings, "MCP_ENABLED", True)
    monkeypatch.setattr(settings, "MCP_PUBLIC_URL", ISSUER)
    monkeypatch.setattr("app.mcp.oauth.SessionLocal", lambda: db_session)
    monkeypatch.setattr("app.mcp.tools.SessionLocal", lambda: db_session)

    from app.mcp.server import create_mcp_http_app, create_mcp_server

    app = create_mcp_http_app(create_mcp_server())
    # base_url sets the Host header; the transport rejects hosts it was not
    # configured for, exactly as it would on the real domain.
    with TestClient(app, base_url=ISSUER) as test_client:
        yield test_client


def _pkce():
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def _register(client, name="Test Assistant"):
    response = client.post(
        "/register",
        json={
            "client_name": name,
            "redirect_uris": [REDIRECT_URI],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _start_authorization(client, client_id, challenge, state="xyz"):
    """Send the assistant to /authorize; returns the consent transaction id."""
    response = client.get(
        "/authorize",
        params={
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": REDIRECT_URI,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": state,
            "resource": RESOURCE,
        },
        follow_redirects=False,
    )
    assert response.status_code == 302, response.text
    location = response.headers["location"]
    assert location.startswith(f"{ISSUER}/oauth/consent?txn=")
    return parse_qs(urlparse(location).query)["txn"][0]


def _approve(client, txn, username, password):
    return client.post(
        "/oauth/consent",
        data={
            "txn": txn,
            "username": username,
            "password": password,
            "decision": "approve",
        },
        follow_redirects=False,
    )


def _owner_credentials():
    return settings.OWNER_USERNAME, settings.OWNER_PASSWORD


def _grant(client):
    """Run the whole flow and return (client_id, verifier, code)."""
    registration = _register(client)
    verifier, challenge = _pkce()
    txn = _start_authorization(client, registration["client_id"], challenge)
    response = _approve(client, txn, *_owner_credentials())
    assert response.status_code == 302, response.text
    query = parse_qs(urlparse(response.headers["location"]).query)
    return registration["client_id"], verifier, query["code"][0]


def _exchange(client, client_id, verifier, code):
    return client.post(
        "/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "code_verifier": verifier,
            "client_id": client_id,
            "redirect_uri": REDIRECT_URI,
            "resource": RESOURCE,
        },
    )


def _tokens(client):
    client_id, verifier, code = _grant(client)
    response = _exchange(client, client_id, verifier, code)
    assert response.status_code == 200, response.text
    return client_id, response.json()


def _call_mcp(client, token=None):
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return client.post(
        "/mcp",
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "0"},
            },
        },
    )


# ============================================================================
# Discovery
# ============================================================================


def test_authorization_server_metadata(client):
    data = client.get("/.well-known/oauth-authorization-server").json()

    assert data["issuer"] == f"{ISSUER}/"
    assert data["authorization_endpoint"] == f"{ISSUER}/authorize"
    assert data["token_endpoint"] == f"{ISSUER}/token"
    assert data["registration_endpoint"] == f"{ISSUER}/register"
    assert "S256" in data["code_challenge_methods_supported"]
    assert data["scopes_supported"] == ["cafe:read"]


def test_protected_resource_metadata_points_at_this_server(client):
    data = client.get("/.well-known/oauth-protected-resource/mcp").json()

    assert data["resource"] == RESOURCE
    assert data["authorization_servers"] == [f"{ISSUER}/"]


# ============================================================================
# The happy path
# ============================================================================


def test_full_flow_reaches_the_protected_endpoint(client):
    _, tokens = _tokens(client)

    assert tokens["token_type"].lower() == "bearer"
    assert tokens["scope"] == "cafe:read"
    assert tokens["refresh_token"]

    response = _call_mcp(client, tokens["access_token"])
    assert response.status_code == 200, response.text


def test_state_is_returned_to_the_assistant(client):
    registration = _register(client)
    _, challenge = _pkce()
    txn = _start_authorization(client, registration["client_id"], challenge, state="s-42")

    response = _approve(client, txn, *_owner_credentials())

    assert parse_qs(urlparse(response.headers["location"]).query)["state"] == ["s-42"]


# ============================================================================
# Access control
# ============================================================================


def test_unauthenticated_call_is_refused_with_discovery_hint(client):
    response = _call_mcp(client)

    assert response.status_code == 401
    challenge = response.headers["www-authenticate"]
    assert "resource_metadata=" in challenge
    assert "/.well-known/oauth-protected-resource/mcp" in challenge


def test_garbage_token_is_refused(client):
    assert _call_mcp(client, "not-a-real-token").status_code == 401


def test_admin_login_cannot_approve(client):
    """The tools expose the full financial history, which is owner-only."""
    registration = _register(client)
    _, challenge = _pkce()
    txn = _start_authorization(client, registration["client_id"], challenge)

    response = _approve(client, txn, settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD)

    assert response.status_code == 401
    assert "not recognised" in response.text


def test_failure_response_does_not_reveal_which_login_exists(client):
    """A wrong owner password and an admin login must be indistinguishable."""
    registration = _register(client)
    _, challenge = _pkce()
    txn = _start_authorization(client, registration["client_id"], challenge)

    wrong_owner = _approve(client, txn, settings.OWNER_USERNAME, "wrong")
    as_admin = _approve(client, txn, settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD)

    assert wrong_owner.status_code == as_admin.status_code == 401
    assert wrong_owner.text == as_admin.text


def test_repeated_bad_passwords_burn_the_transaction(client):
    from app.mcp.oauth import MAX_CONSENT_ATTEMPTS

    registration = _register(client)
    _, challenge = _pkce()
    txn = _start_authorization(client, registration["client_id"], challenge)

    for _ in range(MAX_CONSENT_ATTEMPTS - 1):
        assert _approve(client, txn, "owner", "wrong").status_code == 401

    # The attempt that hits the cap, and every one after, gets "expired".
    assert _approve(client, txn, "owner", "wrong").status_code == 400
    assert _approve(client, txn, *_owner_credentials()).status_code == 400


def test_owner_can_decline(client):
    registration = _register(client)
    _, challenge = _pkce()
    txn = _start_authorization(client, registration["client_id"], challenge, state="s1")

    response = client.post(
        "/oauth/consent",
        data={"txn": txn, "decision": "deny", "username": "", "password": ""},
        follow_redirects=False,
    )

    assert response.status_code == 302
    query = parse_qs(urlparse(response.headers["location"]).query)
    assert query["error"] == ["access_denied"]
    assert query["state"] == ["s1"]
    # The transaction is gone: approving afterwards no longer works.
    assert _approve(client, txn, *_owner_credentials()).status_code == 400


def test_consent_page_escapes_the_client_name(client):
    """The name comes from registration, so a hostile client could inject HTML."""
    registration = _register(client, name="<script>alert(1)</script>")
    _, challenge = _pkce()
    txn = _start_authorization(client, registration["client_id"], challenge)

    page = client.get("/oauth/consent", params={"txn": txn}).text

    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page


def test_unknown_transaction_is_rejected(client):
    assert client.get("/oauth/consent", params={"txn": "nope"}).status_code == 400


# ============================================================================
# Token endpoint hardening
# ============================================================================


def test_code_cannot_be_replayed(client):
    client_id, verifier, code = _grant(client)

    assert _exchange(client, client_id, verifier, code).status_code == 200
    assert _exchange(client, client_id, verifier, code).status_code == 400


def test_wrong_pkce_verifier_is_rejected(client):
    client_id, _, code = _grant(client)

    response = _exchange(client, client_id, "not-the-verifier", code)

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_grant"


def test_code_is_bound_to_the_client_that_requested_it(client):
    client_id, verifier, code = _grant(client)
    other = _register(client, name="Other Assistant")["client_id"]

    assert _exchange(client, other, verifier, code).status_code == 400


# ============================================================================
# Refresh and revoke
# ============================================================================


def test_refresh_rotates_and_retires_the_old_grant(client):
    client_id, first = _tokens(client)

    response = client.post(
        "/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": first["refresh_token"],
            "client_id": client_id,
        },
    )
    assert response.status_code == 200, response.text
    second = response.json()

    assert second["access_token"] != first["access_token"]
    assert second["refresh_token"] != first["refresh_token"]
    # The new grant works and the old one is dead in both halves.
    assert _call_mcp(client, second["access_token"]).status_code == 200
    assert _call_mcp(client, first["access_token"]).status_code == 401
    replay = client.post(
        "/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": first["refresh_token"],
            "client_id": client_id,
        },
    )
    assert replay.status_code == 400


def test_revoking_the_refresh_token_kills_the_access_token_too(client):
    client_id, tokens = _tokens(client)

    # The SDK's revocation model declares client_secret as required-but-
    # nullable, so a public client has to send it empty.
    response = client.post(
        "/revoke",
        data={"token": tokens["refresh_token"], "client_id": client_id, "client_secret": ""},
    )
    assert response.status_code == 200, response.text

    assert _call_mcp(client, tokens["access_token"]).status_code == 401
