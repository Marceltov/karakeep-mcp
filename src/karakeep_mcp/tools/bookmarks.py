"""Bookmarks: search, read, create, change and delete."""

from typing import Annotated, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from ..karakeep import KarakeepClient, current_key
from ..links import Links, Result, page_guidance, slim_bookmark, slim_list

READ = ToolAnnotations(readOnlyHint=True, openWorldHint=True)
WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True)
DELETE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=True)

QUERY = "Words to find, plus Karakeep's qualifiers: #tag, list:name, is:fav, is:archived, after:2026-01-01, before:…, url:example.com."
BookmarkId = Annotated[str, Field(description="The bookmark's id, from search-bookmarks or another bookmark result.")]


def register(mcp: FastMCP, client: KarakeepClient) -> None:
    links = Links(client.settings)

    async def api(method: str, path: str, **kwargs):
        return await client.request(method, path, key=current_key(), **kwargs)

    @mcp.tool(name="search-bookmarks", annotations=READ)
    async def search_bookmarks(
        query: Annotated[str, Field(description=QUERY)],
        limit: Annotated[int, Field(ge=1, le=100)] = 10,
        cursor: Annotated[str | None, Field(description="nextCursor of the previous page.")] = None,
    ) -> Result:
        """Search the signed-in person's bookmarks (full text, titles, notes, tags)."""
        data = await api("GET", "/bookmarks/search", params={"q": query, "limit": limit, "cursor": cursor, "includeContent": "false"})
        found = [slim_bookmark(b, links) for b in data["bookmarks"]]
        guidance = page_guidance(len(found), data.get("nextCursor"), "bookmarks") if found else ["No bookmark matches; try fewer or other words."]
        if found:
            guidance.append("Give the person each bookmark's url; get-bookmark-content reads one.")
        return Result(bookmarks=found, nextCursor=data.get("nextCursor"), guidance=guidance)

    @mcp.tool(name="get-bookmark", annotations=READ)
    async def get_bookmark(bookmark_id: BookmarkId) -> Result:
        """One bookmark: title, link, note, AI summary, tags."""
        b = slim_bookmark(await api("GET", f"/bookmarks/{bookmark_id}", params={"includeContent": "false"}), links)
        return Result(bookmark=b, guidance=["get-bookmark-content reads the saved page itself."])

    @mcp.tool(name="get-bookmark-content", annotations=READ)
    async def get_bookmark_content(
        bookmark_id: BookmarkId,
        max_chars: Annotated[int, Field(ge=500, le=50000)] = 8000,
        cursor: Annotated[str | None, Field(description="nextCursor of the previous call, to read on.")] = None,
    ) -> Result:
        """The saved page as Markdown (or a text bookmark's text), in chunks."""
        params = {"format": None if cursor else "markdown", "maxChars": max_chars, "cursor": cursor}
        data = await api("GET", f"/bookmarks/{bookmark_id}/content", params=params)
        rng = data.get("range") or {}
        if data.get("nextCursor"):
            guidance = [f"Read characters {rng.get('end')} of {rng.get('total')}; call again with nextCursor as cursor to read on."]
        else:
            guidance = ["That is the whole content."]
        return Result(content=data.get("content", ""), range=rng, nextCursor=data.get("nextCursor"), url=links.bookmark(bookmark_id), guidance=guidance)

    @mcp.tool(name="create-bookmark", annotations=WRITE)
    async def create_bookmark(
        type: Literal["link", "text"],
        url: Annotated[str | None, Field(description="For a link: the address to save.")] = None,
        text: Annotated[str | None, Field(description="For a text bookmark: its text.")] = None,
        title: str | None = None,
        note: str | None = None,
    ) -> Result:
        """Save a link or a text note in the person's Karakeep."""
        if type == "link" and not url:
            raise ToolError("A link bookmark needs its url.")
        if type == "text" and not text:
            raise ToolError("A text bookmark needs its text.")
        body = {"type": type, "url": url if type == "link" else None, "text": text if type == "text" else None, "title": title, "note": note}
        status, data = await client.request_status("POST", "/bookmarks", key=current_key(), json={k: v for k, v in body.items() if v is not None})
        b = slim_bookmark(data, links)
        if status == 200:
            return Result(bookmark=b, already_saved=True, guidance=["This link was already saved; nothing new was created. Give the person its url."])
        guidance = ["Saved. Give the person its url."]
        if type == "link":
            guidance.append("Karakeep fetches, summarises and tags the page in the background; get-bookmark shows the title in a minute.")
        return Result(bookmark=b, already_saved=False, guidance=guidance)

    @mcp.tool(name="update-bookmark", annotations=WRITE)
    async def update_bookmark(
        bookmark_id: BookmarkId,
        title: str | None = None,
        note: str | None = None,
        summary: str | None = None,
        archived: bool | None = None,
        favourited: bool | None = None,
    ) -> Result:
        """Change a bookmark's title, note, summary, or archived and favourite flags. Only given fields change."""
        body = {k: v for k, v in {"title": title, "note": note, "summary": summary, "archived": archived, "favourited": favourited}.items() if v is not None}
        if not body:
            raise ToolError("Nothing to change: give at least one field.")
        await api("PATCH", f"/bookmarks/{bookmark_id}", json=body)
        b = slim_bookmark(await api("GET", f"/bookmarks/{bookmark_id}", params={"includeContent": "false"}), links)
        return Result(bookmark=b, guidance=[f"Changed: {', '.join(body)}."])

    @mcp.tool(name="delete-bookmark", annotations=DELETE)
    async def delete_bookmark(bookmark_id: BookmarkId) -> Result:
        """Delete a bookmark for good. Ask the person first."""
        await api("DELETE", f"/bookmarks/{bookmark_id}")
        return Result(deleted=bookmark_id, guidance=["Deleted for good; Karakeep has no trash. To keep it out of sight instead, archive it (update-bookmark)."])

    @mcp.tool(name="check-url", annotations=READ)
    async def check_url(url: Annotated[str, Field(description="The address to look for.")]) -> Result:
        """Whether the person already saved this link."""
        data = await api("GET", "/bookmarks/check-url", params={"url": url})
        found = data.get("bookmarkId")
        if found:
            return Result(bookmark_id=found, url=links.bookmark(found), guidance=["Already saved; get-bookmark shows it."])
        return Result(bookmark_id=None, guidance=["Not saved yet; create-bookmark saves it."])

    @mcp.tool(name="get-bookmark-lists", annotations=READ)
    async def get_bookmark_lists(bookmark_id: BookmarkId) -> Result:
        """The lists a bookmark is in."""
        data = await api("GET", f"/bookmarks/{bookmark_id}/lists")
        found = [slim_list(item, links) for item in data["lists"]]
        return Result(lists=found, guidance=[f"In {len(found)} lists." if found else "In no list; add-bookmark-to-list adds it to one."])
