"""Assets: the files Karakeep keeps for a bookmark (screenshots, PDFs, images)."""

from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from ..karakeep import KarakeepClient
from ..links import Result
from ._common import READ, caller


def register(mcp: FastMCP, client: KarakeepClient) -> None:
    api = caller(client)

    @mcp.tool(name="get-asset", annotations=READ)
    async def get_asset(asset_id: Annotated[str, Field(description="An asset id from a bookmark.")]) -> Result:
        """A temporary download link for one of a bookmark's files."""
        data = await api("GET", f"/assets/{asset_id}/signed-url")
        return Result(
            asset_id=asset_id,
            signedUrl=data["signedUrl"],
            expiresAt=data.get("expiresAt"),
            guidance=[f"The link works for a limited time (until {data.get('expiresAt')}); give it to the person, don't store it."],
        )
