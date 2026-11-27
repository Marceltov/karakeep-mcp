"""Lists: the person's folders of bookmarks."""

from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from ..karakeep import KarakeepClient
from ..links import Links, Result, page_guidance, slim_bookmark, slim_list
from ._common import DELETE, READ, WRITE, BookmarkId, Cursor, Limit, caller, given

ListId = Annotated[str, Field(description="The list's id, from get-lists.")]


def register(mcp: FastMCP, client: KarakeepClient) -> None:
    links = Links(client.settings)
    api = caller(client)

    @mcp.tool(name="get-lists", annotations=READ)
    async def get_lists() -> Result:
        """All of the person's lists, with their parents (lists nest)."""
        found = [slim_list(item, links) for item in (await api("GET", "/lists"))["lists"]]
        return Result(lists=found, guidance=[f"{len(found)} lists." if found else "No lists yet; create-list makes one."])

    @mcp.tool(name="get-list", annotations=READ)
    async def get_list(list_id: ListId) -> Result:
        """One list."""
        return Result(list=slim_list(await api("GET", f"/lists/{list_id}"), links), guidance=["get-list-bookmarks shows what is in it."])

    @mcp.tool(name="get-list-bookmarks", annotations=READ)
    async def get_list_bookmarks(list_id: ListId, limit: Limit = 20, cursor: Cursor = None) -> Result:
        """The bookmarks in a list, newest first."""
        data = await api("GET", f"/lists/{list_id}/bookmarks", params={"limit": limit, "cursor": cursor, "includeContent": "false"})
        found = [slim_bookmark(b, links) for b in data["bookmarks"]]
        return Result(
            bookmarks=found, nextCursor=data.get("nextCursor"), url=links.list(list_id), guidance=page_guidance(len(found), data.get("nextCursor"), "bookmarks")
        )

    @mcp.tool(name="create-list", annotations=WRITE)
    async def create_list(
        name: str,
        icon: Annotated[str, Field(description="One emoji.")] = "🔖",
        parent_id: Annotated[str | None, Field(description="To nest it inside another list.")] = None,
        description: str | None = None,
    ) -> Result:
        """Make a new list (a manual one: bookmarks are added to it by hand)."""
        body = given(name=name, icon=icon, type="manual", parentId=parent_id, description=description)
        created = slim_list(await api("POST", "/lists", json=body), links)
        return Result(list=created, guidance=["Created. add-bookmark-to-list fills it; give the person its url."])

    @mcp.tool(name="update-list", annotations=WRITE)
    async def update_list(
        list_id: ListId, name: str | None = None, icon: str | None = None, parent_id: str | None = None, description: str | None = None
    ) -> Result:
        """Rename a list, change its icon or description, or move it under another list."""
        body = given(name=name, icon=icon, parentId=parent_id, description=description)
        if not body:
            raise ToolError("Nothing to change: give at least one field.")
        return Result(list=slim_list(await api("PATCH", f"/lists/{list_id}", json=body), links), guidance=[f"Changed: {', '.join(body)}."])

    @mcp.tool(name="delete-list", annotations=DELETE)
    async def delete_list(list_id: ListId) -> Result:
        """Delete a list. Ask the person first."""
        await api("DELETE", f"/lists/{list_id}")
        return Result(deleted=list_id, guidance=["The list is gone. Bookmarks in it are kept; they are only no longer in this list."])

    @mcp.tool(name="add-bookmark-to-list", annotations=WRITE)
    async def add_bookmark_to_list(list_id: ListId, bookmark_id: BookmarkId) -> Result:
        """Put a bookmark into a list."""
        await api("PUT", f"/lists/{list_id}/bookmarks/{bookmark_id}")
        return Result(list_id=list_id, bookmark_id=bookmark_id, url=links.list(list_id), guidance=["Added."])

    @mcp.tool(name="remove-bookmark-from-list", annotations=WRITE)
    async def remove_bookmark_from_list(list_id: ListId, bookmark_id: BookmarkId) -> Result:
        """Take a bookmark out of a list; the bookmark itself stays."""
        await api("DELETE", f"/lists/{list_id}/bookmarks/{bookmark_id}")
        return Result(list_id=list_id, bookmark_id=bookmark_id, url=links.list(list_id), guidance=["Removed from the list; the bookmark is kept."])
