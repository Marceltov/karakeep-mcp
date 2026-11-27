import json
import re

import pytest
import respx
from mcp_login_oauth import LoginRejected

from karakeep_mcp.auth import LOGIN_FIELDS, KarakeepLogin
from karakeep_mcp.config import load_settings
from karakeep_mcp.karakeep import KarakeepClient

URL = "https://karakeep.example"
ME = f"{URL}/api/v1/users/me"
EXCHANGE = f"{URL}/api/trpc/apiKeys.exchange"
REVOKE = f"{URL}/api/trpc/apiKeys.revoke"


def form(api_key="", email="", password=""):
    return {"api_key": api_key, "email": email, "password": password}


def trpc_error(code, message, status):
    return {"status_code": status, "json": {"error": {"json": {"message": message, "data": {"code": code, "httpStatus": status}}}}}


@pytest.fixture
def login():
    return KarakeepLogin(KarakeepClient(load_settings({"KARAKEEP_URL": URL})))


def test_fields_put_email_and_password_in_one_collapsed_group():
    assert [f.name for f in LOGIN_FIELDS] == ["api_key", "email", "password"]
    assert LOGIN_FIELDS[0].group is None
    assert LOGIN_FIELDS[1].group == LOGIN_FIELDS[2].group == "No API key at hand? Sign in with your Karakeep email and password"


@respx.mock
async def test_api_key_checked_against_users_me(login):
    route = respx.get(ME).respond(json={"id": "u1"})
    assert await login.check_login(form(api_key="ak2_x")) == {"api_key": "ak2_x", "key_id": None}
    assert route.calls.last.request.headers["authorization"] == "Bearer ak2_x"


@respx.mock
async def test_wrong_key_is_rejected(login):
    respx.get(ME).respond(401)
    with pytest.raises(LoginRejected, match=re.escape("Karakeep does not accept this API key.")):
        await login.check_login(form(api_key="bad"))


@respx.mock
async def test_pasted_key_is_trimmed(login):
    route = respx.get(ME).respond(json={"id": "u1"})
    assert (await login.check_login(form(api_key="  Bearer ak2_x \n")))["api_key"] == "ak2_x"
    assert route.calls.last.request.headers["authorization"] == "Bearer ak2_x"


@respx.mock
async def test_key_wins_over_email(login):
    respx.get(ME).respond(json={"id": "u1"})
    exchange = respx.post(EXCHANGE)
    await login.check_login(form(api_key="ak", email="a@b.c", password="pw"))
    assert not exchange.called


@respx.mock
async def test_exchange_mints_claude_key(login):
    route = respx.post(EXCHANGE).respond(json={"result": {"data": {"json": {"id": "kid", "key": "ak2_new", "name": "Claude"}}}})
    assert await login.check_login(form(email=" a@b.c ", password="pw")) == {"api_key": "ak2_new", "key_id": "kid"}
    assert json.loads(route.calls.last.request.content) == {"json": {"keyName": "Claude", "email": "a@b.c", "password": "pw"}}


@respx.mock
async def test_exchange_wrong_password(login):
    respx.post(EXCHANGE).respond(**trpc_error("UNAUTHORIZED", "UNAUTHORIZED", 401))
    with pytest.raises(LoginRejected, match=re.escape("Wrong email or password.")):
        await login.check_login(form(email="a@b.c", password="no"))


@respx.mock
async def test_exchange_password_auth_disabled(login):
    respx.post(EXCHANGE).respond(**trpc_error("FORBIDDEN", "Password authentication is currently disabled", 403))
    with pytest.raises(LoginRejected, match="Password authentication is currently disabled"):
        await login.check_login(form(email="a@b.c", password="pw"))


@respx.mock
async def test_exchange_rate_limited(login):
    respx.post(EXCHANGE).respond(**trpc_error("TOO_MANY_REQUESTS", "Rate limit exceeded", 429))
    with pytest.raises(LoginRejected, match=re.escape("Too many attempts: Karakeep allows 10 in 15 minutes. Try again later.")):
        await login.check_login(form(email="a@b.c", password="pw"))


@pytest.mark.parametrize("values", [form(), form(email="a@b.c"), form(password="pw"), form(api_key="   ")])
async def test_empty_form_is_rejected_with_a_message(login, values):
    with pytest.raises(LoginRejected, match=re.escape("Enter an API key, or your email and password.")):
        await login.check_login(values)


@respx.mock
async def test_verify_static_checks_the_key(login):
    respx.get(ME).mock(side_effect=lambda r: respx.MockResponse(200 if r.headers["authorization"] == "Bearer good" else 401, json={}))
    assert await login.verify_static("good") == {"api_key": "good", "key_id": None}
    assert await login.verify_static("bad") is None


@respx.mock
async def test_on_revoke_revokes_only_minted_keys(login):
    route = respx.post(REVOKE).respond(json={"result": {"data": {"json": None}}})
    await login.on_revoke({"api_key": "pasted", "key_id": None})
    assert not route.called
    await login.on_revoke({"api_key": "ak2_new", "key_id": "kid"})
    assert json.loads(route.calls.last.request.content) == {"json": {"id": "kid"}}
    assert route.calls.last.request.headers["authorization"] == "Bearer ak2_new"


@respx.mock
async def test_on_revoke_failure_is_swallowed(login):
    respx.post(REVOKE).respond(**trpc_error("UNAUTHORIZED", "UNAUTHORIZED", 401))
    await login.on_revoke({"api_key": "ak2_new", "key_id": "kid"})
