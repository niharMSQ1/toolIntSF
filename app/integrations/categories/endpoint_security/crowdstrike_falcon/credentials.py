"""CrowdStrike API client credentials + optional MSSP member CID."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.endpoint_security.crowdstrike_falcon.constants import DEFAULT_API_BASE_URL


def resolve_api_base_url(cfg: dict[str, Any]) -> str:
    v = cfg.get("api_base_url") or cfg.get("falcon_base_url") or cfg.get("crowdstrike_base_url")
    if v and str(v).strip():
        return str(v).strip().rstrip("/")
    return DEFAULT_API_BASE_URL


def resolve_client_id(cfg: dict[str, Any]) -> str | None:
    v = cfg.get("client_id") or cfg.get("falcon_client_id")
    if v is None or not str(v).strip():
        return None
    return str(v).strip()


def resolve_client_secret(cfg: dict[str, Any]) -> str | None:
    v = cfg.get("client_secret") or cfg.get("falcon_client_secret")
    if v is None or not str(v).strip():
        return None
    return str(v).strip()


def resolve_member_cid(cfg: dict[str, Any]) -> str | None:
    """Optional child tenant CID (MSSP)."""
    v = cfg.get("member_cid") or cfg.get("falcon_member_cid")
    if v is None or not str(v).strip():
        return None
    return str(v).strip()


def resolve_verify_tls(cfg: dict[str, Any]) -> bool:
    v = cfg.get("verify_tls")
    if v is None:
        return True
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in ("1", "true", "yes", "y")


def credentials_valid_shape(cfg: dict[str, Any]) -> bool:
    return bool(resolve_client_id(cfg)) and bool(resolve_client_secret(cfg)) and bool(resolve_api_base_url(cfg))


def resolve_spotlight_filter_fql(cfg: dict[str, Any]) -> str:
    """FQL filter for Spotlight combined; required by API — default ``status:'open'``."""
    v = cfg.get("spotlight_filter") or cfg.get("spotlight_fql")
    if v and str(v).strip():
        return str(v).strip()
    return "status:'open'"


def ready_for_collection(cfg: dict[str, Any]) -> bool:
    return credentials_valid_shape(cfg)
