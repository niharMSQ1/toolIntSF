"""Rippling: API base URL + Bearer token (API key or OAuth access_token per Rippling developer docs)."""

from __future__ import annotations

from typing import Any

DEFAULT_RIPPLING_API_BASE = "https://api.rippling.com"


def resolve_api_base(cfg: dict[str, Any]) -> str:
    u = cfg.get("rippling_api_base") or cfg.get("api_base_url")
    if u and str(u).strip():
        return str(u).strip().rstrip("/")
    return DEFAULT_RIPPLING_API_BASE


def resolve_employees_path(cfg: dict[str, Any]) -> str:
    p = cfg.get("rippling_employees_path") or cfg.get("employees_path")
    if p and str(p).strip():
        return str(p).strip()
    return "/platform/api/v1/employees"


def resolve_bearer_token(cfg: dict[str, Any]) -> str | None:
    t = cfg.get("access_token") or cfg.get("rippling_api_key") or cfg.get("api_key")
    if t and str(t).strip():
        return str(t).strip()
    return None


def has_bearer(cfg: dict[str, Any]) -> bool:
    return bool(resolve_bearer_token(cfg))


def ready_for_api_calls(cfg: dict[str, Any]) -> bool:
    return has_bearer(cfg)
