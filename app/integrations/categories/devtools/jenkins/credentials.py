"""Jenkins: base URL + user API token (HTTP Basic)."""

from __future__ import annotations

from typing import Any


def resolve_base_url(cfg: dict[str, Any]) -> str:
    u = cfg.get("jenkins_url") or cfg.get("base_url") or cfg.get("url")
    if not u or not str(u).strip():
        raise ValueError("Missing jenkins_url in configuration_data (e.g. https://jenkins.example.com).")
    return str(u).strip().rstrip("/")


def resolve_username(cfg: dict[str, Any]) -> str:
    u = cfg.get("username") or cfg.get("user")
    if not u or not str(u).strip():
        raise ValueError("Missing username in configuration_data (Jenkins user id).")
    return str(u).strip()


def resolve_api_token(cfg: dict[str, Any]) -> str | None:
    for key in ("api_token", "jenkins_token", "token", "password"):
        t = cfg.get(key)
        if t and str(t).strip():
            return str(t).strip()
    return None


def has_credentials(cfg: dict[str, Any]) -> bool:
    try:
        resolve_base_url(cfg)
        resolve_username(cfg)
    except ValueError:
        return False
    return bool(resolve_api_token(cfg))


def ready_for_api_calls(cfg: dict[str, Any]) -> bool:
    return has_credentials(cfg)
