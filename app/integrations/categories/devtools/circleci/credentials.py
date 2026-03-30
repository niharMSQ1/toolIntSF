"""CircleCI: API token + project slug (org/project for GitHub)."""

from __future__ import annotations

from typing import Any


def resolve_token(cfg: dict[str, Any]) -> str | None:
    for key in ("circleci_token", "token", "api_token", "personal_access_token"):
        t = cfg.get(key)
        if t and str(t).strip():
            return str(t).strip()
    return None


def has_token(cfg: dict[str, Any]) -> bool:
    return bool(resolve_token(cfg))


def resolve_project_slug(cfg: dict[str, Any]) -> str | None:
    s = cfg.get("project_slug") or cfg.get("project") or cfg.get("circleci_project_slug")
    if s and str(s).strip():
        return str(s).strip()
    return None


def resolve_base_url(cfg: dict[str, Any]) -> str:
    u = cfg.get("circleci_base_url") or cfg.get("base_url")
    if u and str(u).strip():
        return str(u).strip().rstrip("/")
    from app.integrations.categories.devtools.circleci.constants import CIRCLECI_API_V2_BASE

    return CIRCLECI_API_V2_BASE


def ready_for_api_calls(cfg: dict[str, Any]) -> bool:
    return has_token(cfg) and bool(resolve_project_slug(cfg))
