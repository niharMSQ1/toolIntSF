"""Argo CD: server base URL + bearer token (e.g. `argocd account generate-token`)."""

from __future__ import annotations

from typing import Any


def resolve_base_url(cfg: dict[str, Any]) -> str:
    u = cfg.get("argocd_base_url") or cfg.get("base_url") or cfg.get("server_url")
    if not u or not str(u).strip():
        raise ValueError("Missing argocd_base_url in configuration_data (e.g. https://argocd.example.com).")
    return str(u).strip().rstrip("/")


def resolve_token(cfg: dict[str, Any]) -> str | None:
    for key in ("argocd_token", "token", "bearer_token", "access_token"):
        t = cfg.get(key)
        if t and str(t).strip():
            return str(t).strip()
    return None


def has_token(cfg: dict[str, Any]) -> bool:
    return bool(resolve_token(cfg))


def ready_for_api_calls(cfg: dict[str, Any]) -> bool:
    try:
        resolve_base_url(cfg)
    except ValueError:
        return False
    return has_token(cfg)
