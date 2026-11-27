import json

import pytest
import respx

from karakeep_mcp.tools import assets, highlights, lists, tags

from .fake import API, HIGHLIGHT, LIST, TAG, URL, bookmark, call, server, signed_in, tools  # noqa: F401

pytestmark = pytest.mark.usefixtures("signed_in")


@pytest.fixture
def mcp():
    return server(lists, tags, highlights, assets)


def body(route):
    return json.loads(route.calls.last.request.content)


def guided(result):
    return bool(result["guidance"]) and all(isinstance(g, str) and g for g in result["guidance"])


# Lists


@respx.mock
async def test_get_lists(mcp):
    respx.get(f"{API}/lists").respond(json={"lists": [LIST]})
    result = await call(mcp, "get-lists")
    assert result["lists"][0]["url"] == f"{URL}/dashboard/lists/l1"
    assert guided(result)


@respx.mock
async def test_get_list(mcp):
    respx.get(f"{API}/lists/l1").respond(json=LIST)
    result = await call(mcp, "get-list", list_id="l1")
    assert (result["list"]["name"], result["list"]["url"]) == ("Reading", f"{URL}/dashboard/lists/l1")


@respx.mock
async def test_get_list_bookmarks_pages(mcp):
    route = respx.get(f"{API}/lists/l1/bookmarks").respond(json={"bookmarks": [bookmark()], "nextCursor": "c2"})
    result = await call(mcp, "get-list-bookmarks", list_id="l1", cursor="c1")
    assert (route.calls.last.request.url.params["cursor"], route.calls.last.request.url.params["limit"]) == ("c1", "20")
    assert result["bookmarks"][0]["url"] == f"{URL}/dashboard/preview/b1"
    assert result["nextCursor"] == "c2" and any("nextCursor" in g for g in result["guidance"])


@respx.mock
async def test_create_list(mcp):
    route = respx.post(f"{API}/lists").respond(201, json=LIST)
    result = await call(mcp, "create-list", name="Reading")
    assert body(route) == {"name": "Reading", "icon": "🔖", "type": "manual"}
    assert result["list"]["url"] == f"{URL}/dashboard/lists/l1"


@respx.mock
async def test_create_list_with_parent(mcp):
    route = respx.post(f"{API}/lists").respond(201, json=LIST)
    await call(mcp, "create-list", name="Sub", icon="📁", parent_id="l0")
    assert body(route) == {"name": "Sub", "icon": "📁", "type": "manual", "parentId": "l0"}


@respx.mock
async def test_update_list(mcp):
    route = respx.patch(f"{API}/lists/l1").respond(json={**LIST, "name": "Later"})
    result = await call(mcp, "update-list", list_id="l1", name="Later")
    assert body(route) == {"name": "Later"}
    assert result["list"]["name"] == "Later"


@respx.mock
async def test_delete_list_keeps_bookmarks_guidance(mcp):
    route = respx.delete(f"{API}/lists/l1").respond(204)
    result = await call(mcp, "delete-list", list_id="l1")
    assert route.called
    assert any("Bookmarks in it are kept" in g for g in result["guidance"])


@respx.mock
async def test_add_and_remove_bookmark_in_list(mcp):
    add = respx.put(f"{API}/lists/l1/bookmarks/b1").respond(204)
    remove = respx.delete(f"{API}/lists/l1/bookmarks/b1").respond(204)
    added = await call(mcp, "add-bookmark-to-list", list_id="l1", bookmark_id="b1")
    removed = await call(mcp, "remove-bookmark-from-list", list_id="l1", bookmark_id="b1")
    assert add.called and remove.called
    assert added["url"] == removed["url"] == f"{URL}/dashboard/lists/l1"
    assert guided(added) and guided(removed)


# Tags


@respx.mock
async def test_get_tags(mcp):
    route = respx.get(f"{API}/tags").respond(json={"tags": [TAG], "nextCursor": None})
    result = await call(mcp, "get-tags", name_contains="py")
    assert route.calls.last.request.url.params["nameContains"] == "py"
    assert (result["tags"][0]["url"], result["tags"][0]["numBookmarks"]) == (f"{URL}/dashboard/tags/t1", 3)
    assert guided(result)


@respx.mock
async def test_get_tag(mcp):
    respx.get(f"{API}/tags/t1").respond(json=TAG)
    assert (await call(mcp, "get-tag", tag_id="t1"))["tag"]["url"] == f"{URL}/dashboard/tags/t1"


@respx.mock
async def test_get_tag_bookmarks(mcp):
    respx.get(f"{API}/tags/t1/bookmarks").respond(json={"bookmarks": [bookmark()], "nextCursor": None})
    result = await call(mcp, "get-tag-bookmarks", tag_id="t1")
    assert result["bookmarks"][0]["url"] == f"{URL}/dashboard/preview/b1"


@respx.mock
async def test_update_tag(mcp):
    route = respx.patch(f"{API}/tags/t1").respond(json={"id": "t1", "name": "py"})
    result = await call(mcp, "update-tag", tag_id="t1", name="py")
    assert body(route) == {"name": "py"}
    assert result["tag"]["url"] == f"{URL}/dashboard/tags/t1"


@respx.mock
async def test_delete_tag(mcp):
    respx.delete(f"{API}/tags/t1").respond(204)
    result = await call(mcp, "delete-tag", tag_id="t1")
    assert any("bookmarks" in g for g in result["guidance"])


@respx.mock
async def test_tag_attach_body_uses_tag_names(mcp):
    route = respx.post(f"{API}/bookmarks/b1/tags").respond(json={"attached": ["t1", "t2"]})
    result = await call(mcp, "attach-tag-to-bookmark", bookmark_id="b1", tags=["python", "later"])
    assert body(route) == {"tags": [{"tagName": "python"}, {"tagName": "later"}]}
    assert result["url"] == f"{URL}/dashboard/preview/b1"
    assert guided(result)


@respx.mock
async def test_tag_detach(mcp):
    route = respx.delete(f"{API}/bookmarks/b1/tags").respond(json={"detached": ["t1"]})
    await call(mcp, "detach-tag-from-bookmark", bookmark_id="b1", tags=["python"])
    assert body(route) == {"tags": [{"tagName": "python"}]}


# Highlights


@respx.mock
async def test_list_highlights(mcp):
    respx.get(f"{API}/highlights").respond(json={"highlights": [HIGHLIGHT], "nextCursor": None})
    result = await call(mcp, "list-highlights")
    assert result["highlights"][0]["url"] == f"{URL}/dashboard/preview/b1"
    assert guided(result)


@respx.mock
async def test_get_bookmark_highlights(mcp):
    respx.get(f"{API}/bookmarks/b1/highlights").respond(json={"highlights": [HIGHLIGHT]})
    result = await call(mcp, "get-bookmark-highlights", bookmark_id="b1")
    assert result["highlights"][0]["text"] == "Hello"


@respx.mock
async def test_get_highlight(mcp):
    respx.get(f"{API}/highlights/h1").respond(json=HIGHLIGHT)
    assert (await call(mcp, "get-highlight", highlight_id="h1"))["highlight"]["url"] == f"{URL}/dashboard/preview/b1"


@respx.mock
async def test_create_highlight(mcp):
    route = respx.post(f"{API}/highlights").respond(201, json=HIGHLIGHT)
    await call(mcp, "create-highlight", bookmark_id="b1", text="Hello", start_offset=0, end_offset=5)
    assert body(route) == {"bookmarkId": "b1", "text": "Hello", "startOffset": 0, "endOffset": 5, "color": "yellow"}


@respx.mock
async def test_update_and_delete_highlight(mcp):
    upd = respx.patch(f"{API}/highlights/h1").respond(json={**HIGHLIGHT, "note": "n"})
    respx.delete(f"{API}/highlights/h1").respond(json=HIGHLIGHT)
    updated = await call(mcp, "update-highlight", highlight_id="h1", note="n")
    deleted = await call(mcp, "delete-highlight", highlight_id="h1")
    assert body(upd) == {"note": "n"}
    assert updated["highlight"]["note"] == "n" and guided(deleted)


# Assets


@respx.mock
async def test_get_asset(mcp):
    respx.get(f"{API}/assets/a1/signed-url").respond(json={"assetId": "a1", "signedUrl": "https://k/s?sig", "expiresAt": "2026-11-27T11:00:00Z"})
    result = await call(mcp, "get-asset", asset_id="a1")
    assert (result["signedUrl"], result["expiresAt"]) == ("https://k/s?sig", "2026-11-27T11:00:00Z")
    assert any("limited time" in g for g in result["guidance"])


async def test_destructive_tools_are_marked(mcp):
    by_name = {t.name: t for t in await tools(mcp)}
    for name in ("delete-list", "delete-tag", "delete-highlight"):
        assert by_name[name].annotations.destructive_hint is True, name
