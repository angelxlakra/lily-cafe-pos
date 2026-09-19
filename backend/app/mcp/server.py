"""The MCP server: transport configuration and OAuth wiring.

The tools themselves live in app.mcp.tools; the authorization server lives in
app.mcp.oauth. This module assembles them.

Enabling MCP publishes an OAuth authorization server and a read-only data
endpoint on the public origin, so it stays off until a deployment sets
MCP_ENABLED and MCP_PUBLIC_URL.
"""

from mcp.server.auth.settings import (
    AuthSettings,
    ClientRegistrationOptions,
    RevocationOptions,
)
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import AnyHttpUrl
from starlette.applications import Starlette

from app.core.config import settings
from app.mcp.consent import CONSENT_PATH, register_consent_routes
from app.mcp.oauth import READ_SCOPE, CafeOAuthProvider
from app.mcp.tools import register_tools

MCP_PATH = "/mcp"

INSTRUCTIONS = """Read-only analytics for a single cafe running the Lily Cafe POS.

All monetary values returned by these tools are in Indian Rupees (INR, ₹)
already converted — do not divide or multiply them further. Dates are
interpreted in IST (UTC+05:30). Report figures as they are returned, and if a
period has no data, say so rather than estimating.
"""


def create_mcp_server() -> MCPServer:
    """Build the MCP server, with OAuth when the deployment has enabled it."""
    provider = None
    auth_settings = None

    if settings.MCP_ENABLED:
        if not settings.MCP_PUBLIC_URL:
            raise RuntimeError(
                "MCP_ENABLED is set but MCP_PUBLIC_URL is empty. It is the OAuth "
                "issuer identifier and must be the public HTTPS origin of this "
                "backend, e.g. https://lily-cafe-pos.fly.dev"
            )

        base = settings.MCP_PUBLIC_URL
        provider = CafeOAuthProvider(consent_url=f"{base}{CONSENT_PATH}")
        auth_settings = AuthSettings(
            issuer_url=AnyHttpUrl(base),
            # Binds tokens to this endpoint (RFC 8707), so a token minted for
            # this cafe cannot be replayed against another deployment.
            resource_server_url=AnyHttpUrl(f"{base}{MCP_PATH}"),
            validate_token_resource=True,
            required_scopes=[READ_SCOPE],
            # ChatGPT and Gemini have no way to pre-register with each cafe,
            # so they register themselves (RFC 7591) on first connection.
            client_registration_options=ClientRegistrationOptions(
                enabled=True,
                valid_scopes=[READ_SCOPE],
                default_scopes=[READ_SCOPE],
            ),
            revocation_options=RevocationOptions(enabled=True),
        )

    server = MCPServer(
        name="lily-cafe-pos",
        instructions=INSTRUCTIONS,
        auth_server_provider=provider,
        auth=auth_settings,
    )
    register_tools(server)
    if provider is not None:
        register_consent_routes(server, provider)
    return server


def create_mcp_http_app(server: MCPServer) -> Starlette:
    """The ASGI app for the server, locked to the public host.

    The transport's DNS-rebinding protection rejects any Host header it was
    not told about. The SDK default only admits localhost, which would turn
    every request on the real domain into a 421.
    """
    public = AnyHttpUrl(settings.MCP_PUBLIC_URL)
    host = public.host or ""
    return server.streamable_http_app(
        streamable_http_path=MCP_PATH,
        transport_security=TransportSecuritySettings(
            allowed_hosts=[host, f"{host}:*"],
            allowed_origins=[settings.MCP_PUBLIC_URL],
        ),
    )


mcp = create_mcp_server()
