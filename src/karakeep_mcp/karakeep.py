"""The one HTTP client to Karakeep: REST (`/api/v1`) and the two tRPC calls the login needs."""

import json as jsonlib
from typing import Any

import httpx
from fastmcp.server.dependencies import get_access_token

from .config import Settings, ssl_context

RECONNECT = "Your Karakeep API key no longer works (revoked or expired): disconnect and connect the connector again."


class KarakeepError(Exception):
    """A failure Claude should read: the message says what happened and what to do."""


class KarakeepUnauthorized(KarakeepError):
    """Karakeep answered 401: the key is wrong, revoked or expired."""


class TrpcError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _message(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return response.text.strip()[:300] or response.reason_phrase
    if isinstance(body, dict):
        return str(body.get("message") or body.get("error") or body)
    return str(body)


class KarakeepClient:
    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None):
        self.settings = settings
        self._http = httpx.AsyncClient(base_url=settings.karakeep_url, verify=ssl_context(settings), timeout=30, transport=transport)

    async def _send(self, method: str, url: str, **kwargs) -> httpx.Response:
        try:
            return await self._http.request(method, url, **kwargs)
        except httpx.TimeoutException as e:
            raise KarakeepError(f"Karakeep did not answer within 30 seconds ({method} {url}).") from e
        except httpx.HTTPError as e:
            raise KarakeepError(f"Karakeep is not reachable at {self.settings.karakeep_url}: {e}") from e

    async def request(self, method: str, path: str, *, key: str, params: dict | None = None, json: Any = None) -> Any:
        return (await self.request_status(method, path, key=key, params=params, json=json))[1]

    async def request_status(self, method: str, path: str, *, key: str, params: dict | None = None, json: Any = None) -> tuple[int, Any]:
        """Like `request`, with the HTTP status: Karakeep answers 200 instead of 201 for a link it already has."""
        headers = {"Authorization": f"Bearer {key}"}
        if params:
            params = {k: v for k, v in params.items() if v is not None}
        response = await self._send(method, f"/api/v1{path}", headers=headers, params=params, json=json)
        if response.status_code == 401:
            raise KarakeepUnauthorized(RECONNECT)
        if response.is_error:
            raise KarakeepError(f"Karakeep refused {method} {path} (HTTP {response.status_code}): {_message(response)}")
        if response.status_code == 204 or not response.content:
            return response.status_code, None
        return response.status_code, response.json()

    async def trpc(self, procedure: str, input: dict, *, key: str | None = None) -> Any:
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        body = jsonlib.dumps({"json": input}, separators=(",", ":"))
        response = await self._send("POST", f"/api/trpc/{procedure}", headers=headers, content=body)
        try:
            data = response.json()
        except ValueError as e:
            raise TrpcError("INTERNAL_SERVER_ERROR", f"HTTP {response.status_code}: {response.text[:300]}") from e
        if "error" in data:
            err = data["error"].get("json", data["error"])
            return_code = (err.get("data") or {}).get("code") or "INTERNAL_SERVER_ERROR"
            raise TrpcError(return_code, err.get("message") or return_code)
        return data["result"]["data"].get("json")


def current_key() -> str:
    """The signed-in person's Karakeep API key, from the grant of this request's access token."""
    token = get_access_token()
    if token is None:
        raise KarakeepError("Not signed in.")
    return token.claims["grant"]["api_key"]
