import json

import pytest
import respx

from karakeep_mcp.tools import bookmarks

from .fake import API, URL, bookmark, call, server, signed_in, tools  # noqa: F401

pytestmark = pytest.mark.usefixtures("signed_in")
PREVIEW = f"{URL}/dashboard/preview"


@pytest.fixture
def mcp():
    return server(bookmarks)


def assert_guided(result):
    assert result["guidance"] and all(isinstance(g, str) and g for g in result["guidance"])


@respx.mock
async def test_search_bookmarks(mcp):
    route = respx.get(f"{API}/bookmarks/search").respond(json={"bookmarks": [bookmark()], "nextCursor": None})
    result = await call(mcp, "search-bookmarks", query="python")
    params = route.calls.last.request.url.params
    assert (params["q"], params["limit"], "cursor" in params) == ("python", "10", False)
    assert route.calls.last.request.headers["authorization"] == "Bearer test-key"
    b = result["bookmarks"][0]
    assert (b["url"], b["link"], b["title"], b["type"]) == (f"{PREVIEW}/b1", "https://example.org/a", "An article", "link")
    assert b["tags"] == [{"id": "t1", "name": "python"}]
    assert_guided(result)
    assert not any("nextCursor" in g for g in result["guidance"])


@respx.mock
async def test_search_pages_with_cursor(mcp):
    route = respx.get(f"{API}/bookmarks/search").respond(json={"bookmarks": [bookmark()], "nextCursor": "c2"})
    result = await call(mcp, "search-bookmarks", query="python", cursor="c1", limit=5)
    assert route.calls.last.request.url.params["cursor"] == "c1"
    assert result["nextCursor"] == "c2"
    assert any("nextCursor" in g for g in result["guidance"])


@respx.mock
async def test_search_without_hits_says_so(mcp):
    respx.get(f"{API}/bookmarks/search").respond(json={"bookmarks": [], "nextCursor": None})
    result = await call(mcp, "search-bookmarks", query="nothing")
    assert result["bookmarks"] == []
    assert any("No bookmark" in g for g in result["guidance"])


@respx.mock
async def test_get_bookmark(mcp):
    respx.get(f"{API}/bookmarks/b1").respond(json=bookmark(note="mine", summary="short"))
    result = await call(mcp, "get-bookmark", bookmark_id="b1")
    assert (result["bookmark"]["url"], result["bookmark"]["note"], result["bookmark"]["summary"]) == (f"{PREVIEW}/b1", "mine", "short")
    assert_guided(result)


@respx.mock
async def test_text_bookmark_keeps_its_text(mcp):
    respx.get(f"{API}/bookmarks/b2").respond(json=bookmark("b2", title="Note", content={"type": "text", "text": "Remember this"}))
    b = (await call(mcp, "get-bookmark", bookmark_id="b2"))["bookmark"]
    assert (b["type"], b["text"], b["title"], b.get("link")) == ("text", "Remember this", "Note", None)


@respx.mock
async def test_get_bookmark_content(mcp):
    body = {"bookmarkId": "b1", "content": "# Hi", "range": {"start": 0, "end": 4, "total": 4}, "nextCursor": None, "truncated": False}
    route = respx.get(f"{API}/bookmarks/b1/content").respond(json=body)
    result = await call(mcp, "get-bookmark-content", bookmark_id="b1")
    params = route.calls.last.request.url.params
    assert (params["format"], params["maxChars"]) == ("markdown", "8000")
    assert (result["content"], result["url"]) == ("# Hi", f"{PREVIEW}/b1")
    assert_guided(result)


@respx.mock
async def test_truncated_content_says_how_to_read_on(mcp):
    body = {"bookmarkId": "b1", "content": "x" * 10, "range": {"start": 0, "end": 10, "total": 50}, "nextCursor": "n1", "truncated": True}
    respx.get(f"{API}/bookmarks/b1/content").respond(json=body)
    result = await call(mcp, "get-bookmark-content", bookmark_id="b1", max_chars=1000)
    assert result["nextCursor"] == "n1"
    assert any("cursor" in g and "10 of 50" in g for g in result["guidance"])


@respx.mock
async def test_create_link_bookmark(mcp):
    route = respx.post(f"{API}/bookmarks").respond(201, json=bookmark("b9"))
    result = await call(mcp, "create-bookmark", type="link", url="https://example.org/a", note="for later")
    assert json.loads(route.calls.last.request.content) == {"type": "link", "url": "https://example.org/a", "note": "for later"}
    assert result["bookmark"]["url"] == f"{PREVIEW}/b9"
    assert any("background" in g for g in result["guidance"])


@respx.mock
async def test_create_link_returns_existing_instead_of_duplicate(mcp):
    respx.post(f"{API}/bookmarks").respond(200, json=bookmark("b1"))
    result = await call(mcp, "create-bookmark", type="link", url="https://example.org/a")
    assert result["already_saved"] is True
    assert any("already saved" in g for g in result["guidance"])


@respx.mock
async def test_create_text_bookmark(mcp):
    route = respx.post(f"{API}/bookmarks").respond(201, json=bookmark("b3", content={"type": "text", "text": "hi"}))
    await call(mcp, "create-bookmark", type="text", text="hi", title="T")
    assert json.loads(route.calls.last.request.content) == {"type": "text", "text": "hi", "title": "T"}


async def test_create_link_without_url_is_refused(mcp):
    with pytest.raises(Exception, match="url"):
        await call(mcp, "create-bookmark", type="link")


@respx.mock
async def test_update_bookmark_sends_only_given_fields(mcp):
    route = respx.patch(f"{API}/bookmarks/b1").respond(json=bookmark(archived=True))
    respx.get(f"{API}/bookmarks/b1").respond(json=bookmark(archived=True))
    result = await call(mcp, "update-bookmark", bookmark_id="b1", archived=True)
    assert json.loads(route.calls.last.request.content) == {"archived": True}
    assert (result["bookmark"]["archived"], result["bookmark"]["url"]) == (True, f"{PREVIEW}/b1")


@respx.mock
async def test_delete_bookmark(mcp):
    route = respx.delete(f"{API}/bookmarks/b1").respond(204)
    result = await call(mcp, "delete-bookmark", bookmark_id="b1")
    assert route.called
    assert any("no trash" in g for g in result["guidance"])


@respx.mock
async def test_check_url(mcp):
    respx.get(f"{API}/bookmarks/check-url").respond(json={"bookmarkId": "b1"})
    result = await call(mcp, "check-url", url="https://example.org/a")
    assert (result["bookmark_id"], result["url"]) == ("b1", f"{PREVIEW}/b1")
    respx.get(f"{API}/bookmarks/check-url").respond(json={"bookmarkId": None})
    result = await call(mcp, "check-url", url="https://example.org/new")
    assert (result["bookmark_id"], result.get("url")) == (None, None)
    assert_guided(result)


@respx.mock
async def test_get_bookmark_lists(mcp):
    from .fake import LIST

    respx.get(f"{API}/bookmarks/b1/lists").respond(json={"lists": [LIST]})
    result = await call(mcp, "get-bookmark-lists", bookmark_id="b1")
    assert result["lists"][0]["url"] == f"{URL}/dashboard/lists/l1"
    assert_guided(result)


async def test_delete_is_destructive(mcp):
    by_name = {t.name: t for t in await tools(mcp)}
    assert by_name["delete-bookmark"].annotations.destructive_hint is True
    assert by_name["search-bookmarks"].annotations.read_only_hint is True


async def test_every_tool_declares_guidance_in_output_schema():
    from karakeep_mcp.tools import ALL

    registered = await tools(server(*ALL))
    for t in registered:
        assert "guidance" in t.output_schema["required"], t.name
    assert len(registered) == 30
