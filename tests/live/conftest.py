"""Live tests against a real Karakeep: only with KARAKEEP_LIVE_URL and KARAKEEP_LIVE_KEY set (a key of a test account,
or one made for these tests). They create and delete their own bookmark, tagged karakeep-mcp-test."""

import os
from types import SimpleNamespace

import pytest

from karakeep_mcp import karakeep

LIVE_URL = os.environ.get("KARAKEEP_LIVE_URL", "")
LIVE_KEY = os.environ.get("KARAKEEP_LIVE_KEY", "")


def pytest_collection_modifyitems(items):
    if LIVE_URL and LIVE_KEY:
        return
    skip = pytest.mark.skip(reason="set KARAKEEP_LIVE_URL and KARAKEEP_LIVE_KEY to run the live tests")
    for item in items:
        if "tests/live" in str(item.fspath):
            item.add_marker(skip)


@pytest.fixture
def live_signed_in(monkeypatch):
    token = SimpleNamespace(claims={"grant": {"api_key": LIVE_KEY, "key_id": None}})
    monkeypatch.setattr(karakeep, "get_access_token", lambda: token)
