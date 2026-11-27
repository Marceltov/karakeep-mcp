"""Highlights: passages the person marked in a saved page."""

from typing import Annotated, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from ..karakeep import KarakeepClient
from ..links import Links, Result, page_guidance, slim_highlight
from ._common import DELETE, READ, WRITE, BookmarkId, Cursor, Limit, caller, given

HighlightId = Annotated[str, Field(description="The highlight's id.")]
Color = Literal["yellow", "red", "green", "blue"]


def register(mcp: FastMCP, client: KarakeepClient) -> None:
    links = Links(client.settings)
    api = caller(client)

    @mcp.tool(name="list-highlights", annotations=READ)
    async def list_highlights(limit: Limit = 20, cursor: Cursor = None) -> Result:
        """All of the person's highlights, newest first."""
        data = await api("GET", "/highlights", params={"limit": limit, "cursor": cursor})
        found = [slim_highlight(h, links) for h in data["highlights"]]
        return Result(highlights=found, nextCursor=data.get("nextCursor"), guidance=page_guidance(len(found), data.get("nextCursor"), "highlights"))

    @mcp.tool(name="get-bookmark-highlights", annotations=READ)
    async def get_bookmark_highlights(bookmark_id: BookmarkId) -> Result:
        """The highlights in one bookmark."""
        found = [slim_highlight(h, links) for h in (await api("GET", f"/bookmarks/{bookmark_id}/highlights"))["highlights"]]
        return Result(highlights=found, url=links.bookmark(bookmark_id), guidance=[f"{len(found)} highlights." if found else "No highlights in it."])

    @mcp.tool(name="get-highlight", annotations=READ)
    async def get_highlight(highlight_id: HighlightId) -> Result:
        """One highlight."""
        return Result(highlight=slim_highlight(await api("GET", f"/highlights/{highlight_id}"), links), guidance=["Its url opens the bookmark."])

    @mcp.tool(name="create-highlight", annotations=WRITE)
    async def create_highlight(
        bookmark_id: BookmarkId,
        text: Annotated[str, Field(description="The highlighted passage, exactly as in the content.")],
        start_offset: Annotated[int, Field(ge=0, description="Where the passage starts in get-bookmark-content's text.")],
        end_offset: Annotated[int, Field(ge=0)],
        color: Color = "yellow",
        note: str | None = None,
    ) -> Result:
        """Mark a passage of a saved page."""
        body = given(bookmarkId=bookmark_id, text=text, startOffset=start_offset, endOffset=end_offset, color=color, note=note)
        return Result(
            highlight=slim_highlight(await api("POST", "/highlights", json=body), links), guidance=["Highlighted; it shows in the bookmark's reader view."]
        )

    @mcp.tool(name="update-highlight", annotations=WRITE)
    async def update_highlight(highlight_id: HighlightId, color: Color | None = None, note: str | None = None) -> Result:
        """Change a highlight's colour or note."""
        body = given(color=color, note=note)
        if not body:
            raise ToolError("Nothing to change: give a color or a note.")
        return Result(highlight=slim_highlight(await api("PATCH", f"/highlights/{highlight_id}", json=body), links), guidance=[f"Changed: {', '.join(body)}."])

    @mcp.tool(name="delete-highlight", annotations=DELETE)
    async def delete_highlight(highlight_id: HighlightId) -> Result:
        """Delete a highlight. Ask the person first."""
        await api("DELETE", f"/highlights/{highlight_id}")
        return Result(deleted=highlight_id, guidance=["The highlight is gone; the bookmark is kept."])
