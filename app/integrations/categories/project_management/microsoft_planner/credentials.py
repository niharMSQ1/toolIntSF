"""Microsoft Graph Planner — credentials from configuration_data."""

from __future__ import annotations

from typing import Any


def resolve_access_token(cfg: dict[str, Any]) -> str | None:
    t = cfg.get("access_token")
    if t and str(t).strip():
        return str(t).strip()
    return None


def has_graph_auth(cfg: dict[str, Any]) -> bool:
    if resolve_access_token(cfg):
        return True
    return bool(
        str(cfg.get("tenant_id") or "").strip()
        and str(cfg.get("client_id") or "").strip()
        and str(cfg.get("client_secret") or "").strip()
    )


def resolve_refresh_token(cfg: dict[str, Any]) -> str | None:
    t = cfg.get("refresh_token")
    if t and str(t).strip():
        return str(t).strip()
    return None
