"""What every tools module shares: the annotations and the call as the signed-in person."""

from typing import Annotated

from mcp.types import ToolAnnotations
from pydantic import Field

from ..karakeep import KarakeepClient, current_key

READ = ToolAnnotations(readOnlyHint=True, openWorldHint=True)
WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True)
DELETE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=True)

BookmarkId = Annotated[str, Field(description="The bookmark's id, from search-bookmarks or another bookmark result.")]
Limit = Annotated[int, Field(ge=1, le=100)]
Cursor = Annotated[str | None, Field(description="nextCursor of the previous page.")]


def caller(client: KarakeepClient):
    async def api(method: str, path: str, **kwargs):
        return await client.request(method, path, key=current_key(), **kwargs)

    return api


def given(**fields) -> dict:
    """The fields the caller set; None means 'leave as it is'."""
    return {k: v for k, v in fields.items() if v is not None}
