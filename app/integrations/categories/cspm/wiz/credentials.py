"""Resolve Wiz API URL, client credentials, and tokens from tool_integrations.configuration_data."""

from __future__ import annotations

from typing import Any

from app.config import get_settings


def resolve_graphql_url(cfg: dict[str, Any]) -> str:
    raw = cfg.get("graphql_url") or cfg.get("api_endpoint_url") or cfg.get("wiz_api_url")
    if not raw or not str(raw).strip():
        raise ValueError(
            "Missing graphql_url: set configuration_data.graphql_url to your tenant GraphQL endpoint "
            "(Profile → Tenant info → API Endpoint URL, e.g. https://api.us1.app.wiz.io/graphql)."
        )
    u = str(raw).strip().rstrip("/")
    if not u.lower().endswith("/graphql"):
        u = f"{u}/graphql"
    return u


def resolve_auth_url(cfg: dict[str, Any]) -> str:
    s = get_settings()
    return str(cfg.get("auth_url") or getattr(s, "wiz_auth_url", None) or "https://auth.app.wiz.io/oauth/token").strip()


def resolve_audience(cfg: dict[str, Any]) -> str:
    s = get_settings()
    return str(cfg.get("audience") or getattr(s, "wiz_audience", None) or "wiz-api").strip()


def resolve_client_credentials(cfg: dict[str, Any]) -> tuple[str, str]:
    cid = cfg.get("client_id") or cfg.get("wiz_client_id")
    sec = cfg.get("client_secret") or cfg.get("wiz_client_secret")
    if not cid or not str(cid).strip():
        raise ValueError("Missing client_id in configuration_data (Wiz service account client ID).")
    if not sec or not str(sec).strip():
        raise ValueError("Missing client_secret in configuration_data (Wiz service account secret).")
    return str(cid).strip(), str(sec).strip()


def has_access_token(cfg: dict[str, Any]) -> bool:
    t = cfg.get("access_token")
    return bool(t and str(t).strip())


def ready_for_collection(cfg: dict[str, Any]) -> bool:
    try:
        resolve_graphql_url(cfg)
        resolve_client_credentials(cfg)
    except ValueError:
        return False
    return has_access_token(cfg)


def merge_token_into_config(cfg: dict[str, Any], token_payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(cfg)
    out["access_token"] = token_payload.get("access_token")
    exp = token_payload.get("expires_in")
    if isinstance(exp, (int, float)):
        out["token_expires_in_seconds"] = int(exp)
    return out
