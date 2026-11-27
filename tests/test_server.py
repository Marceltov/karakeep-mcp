import re
from pathlib import Path

import respx
from fastmcp import Client
from starlette.testclient import TestClient

from karakeep_mcp.config import load_settings
from karakeep_mcp.server import asgi_app, build_server

URL = "https://karakeep.example"
OAUTH = {"KARAKEEP_URL": URL, "MCP_BASE_URL": "https://mcp.example", "MCP_OAUTH_SECRET": "s" * 32}


def settings(env, tmp_path):
    return load_settings({**env, "DATA_DIR": str(tmp_path)})


def test_healthz(tmp_path):
    with TestClient(asgi_app(build_server(s := settings({"KARAKEEP_URL": URL}, tmp_path)), s)) as http:
        response = http.get("/healthz")
    assert (response.status_code, response.json()) == (200, {"status": "ok"})


async def test_lists_30_tools(tmp_path):
    async with Client(build_server(settings({"KARAKEEP_URL": URL}, tmp_path))) as c:
        assert len(await c.list_tools()) == 30


def test_instructions_mention_guidance(tmp_path):
    assert "guidance" in build_server(settings({"KARAKEEP_URL": URL}, tmp_path)).instructions


def test_oauth_metadata_served_when_configured(tmp_path):
    with TestClient(asgi_app(build_server(s := settings(OAUTH, tmp_path)), s)) as http:
        response = http.get("/.well-known/oauth-authorization-server")
    assert response.status_code == 200
    assert response.json()["issuer"].rstrip("/") == "https://mcp.example"
    assert (tmp_path / "oauth").is_dir()


def test_mcp_needs_a_token(tmp_path):
    with TestClient(asgi_app(build_server(s := settings(OAUTH, tmp_path)), s)) as http:
        assert http.post("/mcp", json={}).status_code == 401


@respx.mock
def test_static_only_without_oauth_env(tmp_path):
    respx.get(f"{URL}/api/v1/users/me").mock(side_effect=lambda r: respx.MockResponse(200 if r.headers["authorization"] == "Bearer good" else 401, json={}))
    respx.route(host="testserver").pass_through()
    with TestClient(asgi_app(build_server(s := settings({"KARAKEEP_URL": URL}, tmp_path)), s)) as http:
        assert http.get("/.well-known/oauth-authorization-server").status_code == 404
        headers = {"Accept": "application/json, text/event-stream"}
        init = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}},
        }
        assert http.post("/mcp", json=init, headers={**headers, "Authorization": "Bearer bad"}).status_code == 401
        assert http.post("/mcp", json=init, headers={**headers, "Authorization": "good"}).status_code == 200


def test_env_example_lists_every_setting():
    root = Path(__file__).parent.parent
    read = set(re.findall(r'env\.get\("([A-Z_]+)"\)', (root / "src/karakeep_mcp/config.py").read_text()))
    example = (root / ".env.example").read_text()
    assert read and all(re.search(rf"^#? ?{name}=", example, re.M) for name in read), read
