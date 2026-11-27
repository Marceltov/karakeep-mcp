import httpx
import pytest
import respx
import truststore

from karakeep_mcp.config import load_settings
from karakeep_mcp.karakeep import KarakeepClient, KarakeepError, TrpcError

URL = "https://karakeep.example"


@pytest.fixture
def client():
    return KarakeepClient(load_settings({"KARAKEEP_URL": URL}))


@respx.mock
async def test_sends_bearer_key(client):
    route = respx.get(f"{URL}/api/v1/users/me").respond(json={"id": "u1"})
    assert await client.request("GET", "/users/me", key="k1") == {"id": "u1"}
    assert route.calls.last.request.headers["authorization"] == "Bearer k1"


@respx.mock
async def test_204_returns_none(client):
    respx.delete(f"{URL}/api/v1/bookmarks/b1").respond(204)
    assert await client.request("DELETE", "/bookmarks/b1", key="k") is None


@respx.mock
async def test_401_says_reconnect(client):
    respx.get(f"{URL}/api/v1/bookmarks").respond(401, json={"code": "UNAUTHORIZED", "message": "Unauthorized"})
    with pytest.raises(KarakeepError, match="disconnect and connect the connector again"):
        await client.request("GET", "/bookmarks", key="k")


@respx.mock
async def test_404_names_the_path(client):
    respx.get(f"{URL}/api/v1/bookmarks/nope").respond(404, json={"code": "NOT_FOUND", "message": "Bookmark not found"})
    with pytest.raises(KarakeepError, match="Bookmark not found") as e:
        await client.request("GET", "/bookmarks/nope", key="k")
    assert "/bookmarks/nope" in str(e.value)


@respx.mock
async def test_4xx_passes_karakeep_message(client):
    respx.post(f"{URL}/api/v1/lists").respond(400, json={"code": "BAD_REQUEST", "message": "Name is too long"})
    with pytest.raises(KarakeepError, match="Name is too long"):
        await client.request("POST", "/lists", key="k", json={"name": "x"})


@respx.mock
async def test_unreachable_is_reported(client):
    respx.get(f"{URL}/api/v1/tags").mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(KarakeepError, match="Karakeep is not reachable"):
        await client.request("GET", "/tags", key="k")


@respx.mock
async def test_trpc_unwraps_superjson(client):
    route = respx.post(f"{URL}/api/trpc/apiKeys.exchange").respond(json={"result": {"data": {"json": {"id": "i", "key": "ak"}}}})
    assert await client.trpc("apiKeys.exchange", {"email": "e"}) == {"id": "i", "key": "ak"}
    assert route.calls.last.request.content == b'{"json":{"email":"e"}}'
    assert "authorization" not in route.calls.last.request.headers


@respx.mock
async def test_trpc_sends_key_when_given(client):
    route = respx.post(f"{URL}/api/trpc/apiKeys.revoke").respond(json={"result": {"data": {"json": None}}})
    await client.trpc("apiKeys.revoke", {"id": "i"}, key="ak")
    assert route.calls.last.request.headers["authorization"] == "Bearer ak"


@respx.mock
async def test_trpc_error_carries_code(client):
    body = {"error": {"json": {"message": "UNAUTHORIZED", "code": -32001, "data": {"code": "UNAUTHORIZED", "httpStatus": 401}}}}
    respx.post(f"{URL}/api/trpc/apiKeys.exchange").respond(401, json=body)
    with pytest.raises(TrpcError) as e:
        await client.trpc("apiKeys.exchange", {})
    assert (e.value.code, e.value.message) == ("UNAUTHORIZED", "UNAUTHORIZED")


def test_client_uses_truststore(client):
    assert isinstance(client._http._transport._pool._ssl_context, truststore.SSLContext)
