import os
import uuid

import pytest
from fastmcp import Client

from karakeep_mcp.auth import KarakeepLogin
from karakeep_mcp.config import load_settings
from karakeep_mcp.karakeep import KarakeepClient
from karakeep_mcp.server import build_server

from .conftest import LIVE_KEY, LIVE_URL


def settings(tmp_path):
    return load_settings({"KARAKEEP_URL": LIVE_URL, "DATA_DIR": str(tmp_path)})


async def call(c, tool, **args):
    return (await c.call_tool(tool, args)).structured_content


@pytest.mark.usefixtures("live_signed_in")
async def test_round_trip(tmp_path):
    marker = f"karakeep-mcp live test {uuid.uuid4().hex[:8]}"
    async with Client(build_server(settings(tmp_path))) as c:
        created = (await call(c, "create-bookmark", type="text", text=marker, title=marker))["bookmark"]
        try:
            assert created["url"].endswith(f"/dashboard/preview/{created['id']}")
            await call(c, "attach-tag-to-bookmark", bookmark_id=created["id"], tags=["karakeep-mcp-test"])
            got = (await call(c, "get-bookmark", bookmark_id=created["id"]))["bookmark"]
            assert "karakeep-mcp-test" in [t["name"] for t in got["tags"]]
            content = await call(c, "get-bookmark-content", bookmark_id=created["id"])
            assert marker in content["content"]
            await call(c, "detach-tag-from-bookmark", bookmark_id=created["id"], tags=["karakeep-mcp-test"])
            lists = await call(c, "get-lists")
            assert "lists" in lists and lists["guidance"]
        finally:
            await call(c, "delete-bookmark", bookmark_id=created["id"])


async def test_key_check(tmp_path):
    login = KarakeepLogin(KarakeepClient(settings(tmp_path)))
    assert await login.verify_static(LIVE_KEY) == {"api_key": LIVE_KEY, "key_id": None}
    assert await login.verify_static("ak2_not_a_key") is None


@pytest.mark.skipif(not os.environ.get("KARAKEEP_LIVE_PASSWORD"), reason="set KARAKEEP_LIVE_EMAIL and KARAKEEP_LIVE_PASSWORD")
async def test_exchange_and_revoke(tmp_path):
    login = KarakeepLogin(KarakeepClient(settings(tmp_path)))
    grant = await login.check_login({"api_key": "", "email": os.environ["KARAKEEP_LIVE_EMAIL"], "password": os.environ["KARAKEEP_LIVE_PASSWORD"]})
    assert grant["key_id"] and await login.verify_static(grant["api_key"])
    await login.on_revoke(grant)
    assert await login.verify_static(grant["api_key"]) is None, "apiKeys.revoke did not delete the minted key"
