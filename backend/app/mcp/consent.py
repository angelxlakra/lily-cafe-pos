"""The sign-in and consent screen for connecting an AI assistant.

This is the only human-facing part of the OAuth flow. The owner lands here
after an assistant sends them to /authorize, sees which assistant is asking
and what it will be able to read, and either signs in to approve or declines.
"""

import html

from mcp.server.auth.provider import construct_redirect_uri
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response

from app.core.security import authenticate_user
from app.mcp.oauth import (
    CafeOAuthProvider,
    complete_authorization,
    discard_pending_authorization,
    record_failed_consent_attempt,
    take_pending_authorization,
)
from app.schemas import UserRole

CONSENT_PATH = "/oauth/consent"


def _page(client_name: str, txn: str, error: str | None = None) -> str:
    # client_name arrives from dynamic client registration, so it is
    # attacker-controlled and has to be escaped before it reaches the page.
    safe_name = html.escape(client_name)
    banner = (
        f'<p class="error">{html.escape(error)}</p>' if error else ""
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Connect {safe_name}</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{
    font-family: system-ui, -apple-system, sans-serif;
    margin: 0; padding: 24px;
    display: flex; justify-content: center; align-items: center;
    min-height: 100vh; background: #f6f7f9; color: #14161a;
  }}
  .card {{
    background: #fff; border-radius: 12px; padding: 28px;
    max-width: 380px; width: 100%;
    box-shadow: 0 1px 3px rgba(0,0,0,.12), 0 8px 24px rgba(0,0,0,.08);
  }}
  h1 {{ font-size: 1.15rem; margin: 0 0 4px; }}
  .sub {{ color: #5b6472; font-size: .9rem; margin: 0 0 20px; }}
  ul {{ font-size: .9rem; color: #2b3240; padding-left: 20px; margin: 0 0 20px; }}
  li {{ margin-bottom: 4px; }}
  label {{ display: block; font-size: .85rem; font-weight: 600; margin-bottom: 6px; }}
  input {{
    width: 100%; box-sizing: border-box; padding: 10px 12px; font-size: 1rem;
    border: 1px solid #ccd2db; border-radius: 8px; margin-bottom: 14px;
    background: #fff; color: #14161a;
  }}
  .row {{ display: flex; gap: 10px; margin-top: 4px; }}
  button {{
    flex: 1; padding: 11px; font-size: .95rem; font-weight: 600;
    border-radius: 8px; cursor: pointer; border: 1px solid transparent;
  }}
  .approve {{ background: #1668dc; color: #fff; }}
  .deny {{ background: #fff; border-color: #ccd2db; color: #2b3240; }}
  .error {{
    background: #fdeced; color: #a3161f; font-size: .85rem;
    padding: 10px 12px; border-radius: 8px; margin: 0 0 16px;
  }}
  .note {{ color: #7a8494; font-size: .78rem; margin: 18px 0 0; }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #14161a; color: #e8eaed; }}
    .card {{ background: #1e2126; box-shadow: none; }}
    input {{ background: #14161a; border-color: #333842; color: #e8eaed; }}
    .deny {{ background: #1e2126; border-color: #333842; color: #e8eaed; }}
    ul {{ color: #c3c8d1; }}
    .error {{ background: #3b1519; color: #ff9ba2; }}
  }}
</style>
</head>
<body>
  <div class="card">
    <h1>Connect {safe_name}?</h1>
    <p class="sub">It is asking to read your cafe's data.</p>
    {banner}
    <ul>
      <li>Sales, revenue and payment history</li>
      <li>Menu items and category performance</li>
      <li>Stock levels and cash counter records</li>
    </ul>
    <form method="post" action="{CONSENT_PATH}">
      <input type="hidden" name="txn" value="{html.escape(txn)}">
      <label for="username">Owner username</label>
      <input id="username" name="username" autocomplete="username" required autofocus>
      <label for="password">Password</label>
      <input id="password" name="password" type="password"
             autocomplete="current-password" required>
      <div class="row">
        <button class="deny" type="submit" name="decision" value="deny">Cancel</button>
        <button class="approve" type="submit" name="decision" value="approve">Approve</button>
      </div>
    </form>
    <p class="note">It can only read. Nothing it does can change orders,
       prices or stock. You can disconnect it at any time.</p>
  </div>
</body>
</html>"""


def _expired() -> HTMLResponse:
    return HTMLResponse(
        "<h1>This request has expired</h1>"
        "<p>Start the connection again from the assistant.</p>",
        status_code=400,
    )


def register_consent_routes(mcp, provider: CafeOAuthProvider) -> None:
    """Attach the consent screen to the MCP app."""

    @mcp.custom_route(CONSENT_PATH, methods=["GET"])
    async def consent_form(request: Request) -> Response:
        txn = request.query_params.get("txn", "")
        pending = take_pending_authorization(txn) if txn else None
        if pending is None:
            return _expired()
        client_id, _ = pending
        return HTMLResponse(_page(await _display_name(provider, client_id), txn))

    @mcp.custom_route(CONSENT_PATH, methods=["POST"])
    async def consent_submit(request: Request) -> Response:
        form = await request.form()
        txn = str(form.get("txn", ""))

        pending = take_pending_authorization(txn)
        if pending is None:
            return _expired()
        client_id, params = pending

        if str(form.get("decision")) != "approve":
            discard_pending_authorization(txn)
            return RedirectResponse(
                construct_redirect_uri(
                    str(params.redirect_uri),
                    error="access_denied",
                    error_description="The owner declined the request",
                    state=params.state,
                ),
                status_code=302,
            )

        username = str(form.get("username", ""))
        password = str(form.get("password", ""))
        role = authenticate_user(username, password)

        # The MCP tools expose the full financial history, which the REST API
        # restricts to the owner, so the admin login is refused here too. The
        # message stays the same either way so it does not reveal which login
        # exists.
        if role != UserRole.OWNER:
            still_open = record_failed_consent_attempt(txn)
            if not still_open:
                return _expired()
            return HTMLResponse(
                _page(
                    await _display_name(provider, client_id),
                    txn,
                    error="Those owner credentials were not recognised.",
                ),
                status_code=401,
            )

        result = complete_authorization(
            txn, subject=username, default_resource=provider.resource_url
        )
        if result is None:
            return _expired()
        code, state = result

        return RedirectResponse(
            construct_redirect_uri(str(params.redirect_uri), code=code, state=state),
            status_code=302,
        )


async def _display_name(provider: CafeOAuthProvider, client_id: str) -> str:
    """The assistant's registered name, for the consent prompt."""
    client = await provider.get_client(client_id)
    if client is None or not client.client_name:
        return "An assistant"
    return client.client_name
