"""Build and serve the Karakeep MCP server: streamable HTTP at /mcp, /healthz, and the OAuth login when configured."""

import logging
import sys

import uvicorn
from fastmcp import FastMCP
from fastmcp.server.auth import AccessToken, TokenVerifier
from mcp_login_oauth import BearerPrefixMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from .auth import KarakeepLogin, build_provider
from .config import Settings, load_settings
from .karakeep import KarakeepClient
from .tools import ALL

INSTRUCTIONS = (
    "Karakeep is the person's own bookmark and read-it-later collection: links, text notes, lists, tags and highlights. "
    "Every tool acts as the signed-in person and sees only their bookmarks. Search with search-bookmarks before saving a link "
    "twice. Every result carries `guidance`, what to do next given what the call did, and a `url` into Karakeep for each "
    "bookmark, list and tag: give the person those links. Ask before deleting anything; Karakeep has no trash."
)


class KarakeepKeyVerifier(TokenVerifier):
    """Without OAuth: the bearer is a Karakeep API key, checked against Karakeep."""

    def __init__(self, login: KarakeepLogin):
        super().__init__()
        self.login = login

    async def verify_token(self, token: str) -> AccessToken | None:
        grant = await self.login.verify_static(token)
        return AccessToken(token=token, client_id="karakeep-api-key", scopes=[], claims={"grant": grant}) if grant else None


def build_server(settings: Settings, client: KarakeepClient | None = None) -> FastMCP:
    client = client or KarakeepClient(settings)
    if settings.base_url and settings.oauth_secret:
        auth = build_provider(settings, client)
    else:
        print("OAuth off (MCP_BASE_URL or MCP_OAUTH_SECRET not set): only Karakeep API keys in the Authorization header.", file=sys.stderr)
        auth = KarakeepKeyVerifier(KarakeepLogin(client))
    mcp = FastMCP(name="Karakeep", instructions=INSTRUCTIONS, auth=auth)

    @mcp.custom_route("/healthz", methods=["GET"])
    async def healthz(_request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    for module in ALL:
        module.register(mcp, client)
    return mcp


def asgi_app(mcp: FastMCP, settings: Settings):
    if settings.allowed_hosts:
        inner = mcp.http_app(path="/mcp", allowed_hosts=settings.allowed_hosts)
    else:
        # Reached by LAN address or through a reverse proxy's public name; the token is the gate.
        inner = mcp.http_app(path="/mcp", host_origin_protection=False)
    # A raw key without "Bearer " (some clients send just the key) becomes a bearer token.
    return BearerPrefixMiddleware(inner)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = load_settings()
    app = asgi_app(build_server(settings), settings)
    print(f"Karakeep MCP on http://{settings.host}:{settings.port}/mcp, for {settings.karakeep_url}", file=sys.stderr)
    uvicorn.run(app, host=settings.host, port=settings.port)
