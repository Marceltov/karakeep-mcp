"""Every setting, read from the environment in this one module."""

import os
import ssl
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

import truststore


@dataclass(frozen=True)
class Settings:
    karakeep_url: str
    public_url: str
    base_url: str | None
    oauth_secret: str | None
    data_dir: Path
    verify_tls: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    allowed_hosts: list[str] = field(default_factory=list)


def _clean(value: str | None) -> str | None:
    value = (value or "").strip().rstrip("/")
    return value or None


def load_settings(env: Mapping[str, str] = os.environ) -> Settings:
    karakeep_url = _clean(env.get("KARAKEEP_URL"))
    if not karakeep_url:
        raise RuntimeError("KARAKEEP_URL is not set: the address of your Karakeep, e.g. https://karakeep.example.com")
    return Settings(
        karakeep_url=karakeep_url,
        public_url=_clean(env.get("KARAKEEP_PUBLIC_URL")) or karakeep_url,
        base_url=_clean(env.get("MCP_BASE_URL")),
        oauth_secret=(env.get("MCP_OAUTH_SECRET") or "").strip() or None,
        data_dir=Path(env.get("DATA_DIR") or "/data"),
        verify_tls=(env.get("VERIFY_TLS") or "true").strip().lower() not in ("false", "0", "no", "off"),
        host=(env.get("MCP_HOST") or "0.0.0.0").strip(),
        port=int(env.get("MCP_PORT") or 8000),
        allowed_hosts=[h.strip() for h in (env.get("MCP_ALLOWED_HOSTS") or "").split(",") if h.strip()],
    )


def ssl_context(settings: Settings) -> ssl.SSLContext | bool:
    """The OS trust store (conventions: HTTPS clients); VERIFY_TLS=false is the explicit off switch."""
    if not settings.verify_tls:
        return False
    return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
