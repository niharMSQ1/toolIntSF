"""Resolve Monday personal API token from configuration_data."""

from __future__ import annotations

from typing import Any


def resolve_api_token(cfg: dict[str, Any]) -> str | None:
    """Personal V2 API token — https://developer.monday.com/api-reference/docs/authentication"""
    for key in ("api_token", "monday_api_token", "personal_api_token"):
        t = cfg.get(key)
        if t and str(t).strip():
            return str(t).strip()
    return None


def has_api_token(cfg: dict[str, Any]) -> bool:
    return bool(resolve_api_token(cfg))
