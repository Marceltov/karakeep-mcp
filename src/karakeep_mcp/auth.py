"""The login form: a Karakeep API key, or email and password that Karakeep exchanges for a key named Claude.

The grant is `{"api_key": str, "key_id": str | None}`; `key_id` is set only for a key this server minted, so a
revoked connector deletes that key and never one a person pasted.
"""

import logging
from collections.abc import Mapping

from mcp_login_oauth import LoginField, LoginOAuthProvider, LoginRejected, build_store

from .config import Settings
from .karakeep import KarakeepClient, KarakeepError, KarakeepUnauthorized, TrpcError

log = logging.getLogger(__name__)

KEY_NAME = "Claude"
PASSWORD_GROUP = "No API key at hand? Sign in with your Karakeep email and password"

LOGIN_FIELDS = [
    LoginField("api_key", "Karakeep API key", type="password", autocomplete="off", hint="In Karakeep: Settings, API Keys, New API key."),
    LoginField("email", "Email", autocomplete="username", group=PASSWORD_GROUP),
    LoginField(
        "password",
        "Password",
        type="password",
        autocomplete="current-password",
        group=PASSWORD_GROUP,
        hint="Creates an API key named Claude in your account. Accounts that sign in only through Authentik have no password: use an API key.",
    ),
]


def _clean_key(value: str) -> str:
    value = value.strip()
    if value.lower().startswith("bearer "):
        value = value[len("bearer ") :].strip()
    return value


class KarakeepLogin:
    """The provider's callbacks; they need the Karakeep client, so they live on one object."""

    def __init__(self, client: KarakeepClient):
        self.client = client

    async def _key_works(self, key: str) -> bool:
        try:
            await self.client.request("GET", "/users/me", key=key)
        except KarakeepUnauthorized:
            return False
        return True

    async def check_login(self, form: Mapping[str, str]) -> dict:
        key = _clean_key(form.get("api_key", ""))
        if key:
            if not await self._key_works(key):
                raise LoginRejected("Karakeep does not accept this API key.")
            return {"api_key": key, "key_id": None}
        email, password = form.get("email", "").strip(), form.get("password", "")
        if not email or not password:
            raise LoginRejected("Enter an API key, or your email and password.")
        try:
            minted = await self.client.trpc("apiKeys.exchange", {"keyName": KEY_NAME, "email": email, "password": password})
        except TrpcError as e:
            if e.code == "UNAUTHORIZED":
                raise LoginRejected("Wrong email or password.") from e
            if e.code == "TOO_MANY_REQUESTS":
                raise LoginRejected("Too many attempts: Karakeep allows 10 in 15 minutes. Try again later.") from e
            if e.code in ("FORBIDDEN", "BAD_REQUEST"):
                raise LoginRejected(e.message) from e
            raise
        return {"api_key": minted["key"], "key_id": minted["id"]}

    async def verify_static(self, token: str) -> dict | None:
        key = _clean_key(token)
        return {"api_key": key, "key_id": None} if key and await self._key_works(key) else None

    async def on_revoke(self, grant: dict) -> None:
        if not grant.get("key_id"):
            return
        try:
            await self.client.trpc("apiKeys.revoke", {"id": grant["key_id"]}, key=grant["api_key"])
        except (TrpcError, KarakeepError):
            log.warning("Could not revoke the Karakeep API key %s minted at login; it stays in the person's settings.", grant["key_id"])


def build_provider(settings: Settings, client: KarakeepClient) -> LoginOAuthProvider:
    if not settings.base_url or not settings.oauth_secret:
        raise RuntimeError("OAuth needs MCP_BASE_URL and MCP_OAUTH_SECRET.")
    login = KarakeepLogin(client)
    return LoginOAuthProvider(
        base_url=settings.base_url,
        store=build_store(settings.data_dir / "oauth", settings.oauth_secret, "karakeep-mcp-oauth"),
        service_name="Karakeep",
        fields=LOGIN_FIELDS,
        check_login=login.check_login,
        verify_static=login.verify_static,
        on_revoke=login.on_revoke,
        token_prefix="kkmcp_",
    )
