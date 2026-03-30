"""SAP SuccessFactors: OAuth 2.0 + OData base URLs (tenant-specific; from SAP admin)."""

from __future__ import annotations

from typing import Any


def resolve_token_url(cfg: dict[str, Any]) -> str:
    u = cfg.get("sf_token_url") or cfg.get("oauth_token_url") or cfg.get("successfactors_token_url")
    if not u or not str(u).strip():
        raise ValueError(
            "Missing sf_token_url (OAuth 2.0 token endpoint URL from your SAP SuccessFactors data center).",
        )
    return str(u).strip().rstrip("/")


def resolve_odata_base(cfg: dict[str, Any]) -> str:
    u = cfg.get("sf_odata_base_url") or cfg.get("odata_base_url") or cfg.get("successfactors_api_base")
    if not u or not str(u).strip():
        raise ValueError(
            "Missing sf_odata_base_url (OData v2 base, e.g. https://<host>/odata/v2).",
        )
    return str(u).strip().rstrip("/")


def resolve_oauth_client(cfg: dict[str, Any]) -> tuple[str, str]:
    cid = cfg.get("client_id") or cfg.get("sf_client_id")
    sec = cfg.get("client_secret") or cfg.get("sf_client_secret")
    if not cid or not str(cid).strip():
        raise ValueError("Missing client_id for OAuth 2.0.")
    if not sec or not str(sec).strip():
        raise ValueError("Missing client_secret for OAuth 2.0.")
    return str(cid).strip(), str(sec).strip()


def resolve_access_token(cfg: dict[str, Any]) -> str | None:
    t = cfg.get("access_token")
    if t and str(t).strip():
        return str(t).strip()
    return None


def has_access_token(cfg: dict[str, Any]) -> bool:
    return bool(resolve_access_token(cfg))


def has_oauth_client(cfg: dict[str, Any]) -> bool:
    try:
        resolve_oauth_client(cfg)
        return True
    except ValueError:
        return False


def ready_for_api_calls(cfg: dict[str, Any]) -> bool:
    try:
        resolve_odata_base(cfg)
    except ValueError:
        return False
    return bool(resolve_access_token(cfg))
