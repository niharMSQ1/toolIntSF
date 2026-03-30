"""JumpCloud Directory API — API key (x-api-key)."""

from __future__ import annotations

from typing import Any

JUMPCLOUD_API_ORIGIN = "https://api.jumpcloud.com"


def resolve_api_key(cfg: dict[str, Any]) -> str:
    k = cfg.get("jumpcloud_api_key") or cfg.get("api_key")
    if not k or not str(k).strip():
        raise ValueError("Missing jumpcloud_api_key.")
    return str(k).strip()


def resolve_users_path(cfg: dict[str, Any]) -> str:
    p = cfg.get("jumpcloud_users_path") or cfg.get("users_path")
    if p and str(p).strip():
        return str(p).strip()
    return "/api/v2/systemusers"


def ready_for_collection(cfg: dict[str, Any]) -> bool:
    if not isinstance(cfg, dict):
        return False
    try:
        resolve_api_key(cfg)
    except ValueError:
        return False
    return True
