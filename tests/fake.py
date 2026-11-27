"""Test helpers: a FastMCP server with the tools registered, a signed-in person, and sample Karakeep objects."""

from types import SimpleNamespace

import pytest
from fastmcp import Client, FastMCP

from karakeep_mcp import karakeep
from karakeep_mcp.config import load_settings
from karakeep_mcp.karakeep import KarakeepClient

URL = "https://karakeep.example"
API = f"{URL}/api/v1"


def bookmark(id="b1", **over):
    return {
        "id": id,
        "createdAt": "2026-11-27T10:00:00.000Z",
        "modifiedAt": "2026-11-27T10:00:00.000Z",
        "title": None,
        "archived": False,
        "favourited": False,
        "taggingStatus": "success",
        "note": None,
        "summary": None,
        "userId": "u1",
        "tags": [{"id": "t1", "name": "python", "attachedBy": "ai"}],
        "content": {"type": "link", "url": "https://example.org/a", "title": "An article", "description": "About things"},
        "assets": [],
        **over,
    }


LIST = {"id": "l1", "name": "Reading", "description": None, "icon": "📚", "parentId": None, "type": "manual", "query": None, "public": False}
TAG = {"id": "t1", "name": "python", "numBookmarks": 3, "numBookmarksByAttachedType": {"ai": 2, "human": 1}}
HIGHLIGHT = {
    "id": "h1",
    "bookmarkId": "b1",
    "startOffset": 0,
    "endOffset": 5,
    "color": "yellow",
    "text": "Hello",
    "note": None,
    "createdAt": "2026-11-27T10:00:00.000Z",
}


@pytest.fixture
def signed_in(monkeypatch):
    token = SimpleNamespace(claims={"grant": {"api_key": "test-key", "key_id": None}})
    monkeypatch.setattr(karakeep, "get_access_token", lambda: token)


def server(*modules) -> FastMCP:
    mcp = FastMCP("test")
    client = KarakeepClient(load_settings({"KARAKEEP_URL": URL}))
    for module in modules:
        module.register(mcp, client)
    return mcp


async def call(mcp: FastMCP, tool: str, /, **args) -> dict:
    async with Client(mcp) as c:
        result = await c.call_tool(tool, args)
    return result.structured_content


async def tools(mcp: FastMCP) -> list:
    async with Client(mcp) as c:
        return await c.list_tools()
