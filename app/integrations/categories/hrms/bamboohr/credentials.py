"""BambooHR: subdomain + API key (Basic auth)."""

from __future__ import annotations

import base64
from typing import Any


def resolve_subdomain(cfg: dict[str, Any]) -> str:
    s = cfg.get("bamboohr_subdomain") or cfg.get("subdomain")
    if not s or not str(s).strip():
        raise ValueError("Missing bamboohr_subdomain (e.g. yourcompany from yourcompany.bamboohr.com).")
    return str(s).strip().lower().rstrip("/")


def resolve_api_key(cfg: dict[str, Any]) -> str:
    k = cfg.get("bamboohr_api_key") or cfg.get("api_key")
    if not k or not str(k).strip():
        raise ValueError("Missing bamboohr_api_key.")
    return str(k).strip()


def basic_auth_header(api_key: str) -> str:
    token = base64.b64encode(f"{api_key}:x".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def ready_for_api_calls(cfg: dict[str, Any]) -> bool:
    try:
        resolve_subdomain(cfg)
        resolve_api_key(cfg)
        return True
    except ValueError:
        return False
