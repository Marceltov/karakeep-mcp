"""Tags: the labels on bookmarks, by the person or by Karakeep's AI."""

from typing import Annotated, Literal

from fastmcp import FastMCP
from pydantic import Field

from ..karakeep import KarakeepClient
from ..links import Links, Result, page_guidance, slim_bookmark, slim_tag
from ._common import DELETE, READ, WRITE, BookmarkId, Cursor, Limit, caller

TagId = Annotated[str, Field(description="The tag's id, from get-tags or a bookmark's tags.")]
TagNames = Annotated[list[str], Field(min_length=1, description="Tag names; a name that doesn't exist yet becomes a new tag.")]


def register(mcp: FastMCP, client: KarakeepClient) -> None:
    links = Links(client.settings)
    api = caller(client)

    @mcp.tool(name="get-tags", annotations=READ)
    async def get_tags(
        name_contains: str | None = None,
        sort: Literal["name", "usage", "relevance"] | None = None,
        limit: Limit = 50,
        cursor: Cursor = None,
    ) -> Result:
        """The person's tags with how many bookmarks carry each."""
        data = await api("GET", "/tags", params={"nameContains": name_contains, "sort": sort, "limit": limit, "cursor": cursor})
        found = [slim_tag(t, links) for t in data["tags"]]
        return Result(tags=found, nextCursor=data.get("nextCursor"), guidance=page_guidance(len(found), data.get("nextCursor"), "tags"))

    @mcp.tool(name="get-tag", annotations=READ)
    async def get_tag(tag_id: TagId) -> Result:
        """One tag."""
        return Result(tag=slim_tag(await api("GET", f"/tags/{tag_id}"), links), guidance=["get-tag-bookmarks shows its bookmarks."])

    @mcp.tool(name="get-tag-bookmarks", annotations=READ)
    async def get_tag_bookmarks(tag_id: TagId, limit: Limit = 20, cursor: Cursor = None) -> Result:
        """The bookmarks carrying a tag."""
        data = await api("GET", f"/tags/{tag_id}/bookmarks", params={"limit": limit, "cursor": cursor, "includeContent": "false"})
        found = [slim_bookmark(b, links) for b in data["bookmarks"]]
        return Result(
            bookmarks=found, nextCursor=data.get("nextCursor"), url=links.tag(tag_id), guidance=page_guidance(len(found), data.get("nextCursor"), "bookmarks")
        )

    @mcp.tool(name="update-tag", annotations=WRITE)
    async def update_tag(tag_id: TagId, name: str) -> Result:
        """Rename a tag on every bookmark that carries it."""
        return Result(tag=slim_tag(await api("PATCH", f"/tags/{tag_id}", json={"name": name}), links), guidance=[f"Renamed to {name}."])

    @mcp.tool(name="delete-tag", annotations=DELETE)
    async def delete_tag(tag_id: TagId) -> Result:
        """Delete a tag. Ask the person first."""
        await api("DELETE", f"/tags/{tag_id}")
        return Result(deleted=tag_id, guidance=["The tag is gone from every bookmark; the bookmarks are kept."])

    @mcp.tool(name="attach-tag-to-bookmark", annotations=WRITE)
    async def attach_tag_to_bookmark(bookmark_id: BookmarkId, tags: TagNames) -> Result:
        """Tag a bookmark."""
        data = await api("POST", f"/bookmarks/{bookmark_id}/tags", json={"tags": [{"tagName": t} for t in tags]})
        return Result(attached=data.get("attached", []), url=links.bookmark(bookmark_id), guidance=[f"Tagged with {', '.join(tags)}."])

    @mcp.tool(name="detach-tag-from-bookmark", annotations=WRITE)
    async def detach_tag_from_bookmark(bookmark_id: BookmarkId, tags: TagNames) -> Result:
        """Take tags off a bookmark; the tags themselves stay."""
        data = await api("DELETE", f"/bookmarks/{bookmark_id}/tags", json={"tags": [{"tagName": t} for t in tags]})
        return Result(detached=(data or {}).get("detached", []), url=links.bookmark(bookmark_id), guidance=[f"Removed {', '.join(tags)}."])
