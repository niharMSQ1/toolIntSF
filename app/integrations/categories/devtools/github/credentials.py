"""GitHub credentials from tool_integrations.configuration_data."""

from __future__ import annotations

from typing import Any


def resolve_bearer_token(cfg: dict[str, Any]) -> str | None:
    for key in ("access_token", "personal_access_token", "github_token", "token"):
        t = cfg.get(key)
        if t and str(t).strip():
            return str(t).strip()
    return None


def has_bearer_token(cfg: dict[str, Any]) -> bool:
    return bool(resolve_bearer_token(cfg))


def oauth_app_configured(cfg: dict[str, Any]) -> bool:
    try:
        resolve_oauth_credentials(cfg)
        resolve_redirect_uri(cfg)
        return True
    except ValueError:
        return False


def ready_for_api_calls(cfg: dict[str, Any]) -> bool:
    return has_bearer_token(cfg)


def resolve_oauth_credentials(cfg: dict[str, Any]) -> tuple[str, str]:
    cid = cfg.get("client_id")
    sec = cfg.get("client_secret")
    if not cid or not str(cid).strip():
        raise ValueError("Missing client_id in configuration_data (GitHub OAuth app).")
    if not sec or not str(sec).strip():
        raise ValueError("Missing client_secret in configuration_data.")
    return str(cid).strip(), str(sec).strip()


def resolve_redirect_uri(cfg: dict[str, Any]) -> str:
    u = cfg.get("redirect_uri")
    if not u or not str(u).strip():
        raise ValueError("Missing redirect_uri in configuration_data (must match GitHub OAuth app callback URL).")
    return str(u).strip()
