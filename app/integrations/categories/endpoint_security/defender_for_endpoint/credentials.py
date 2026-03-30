"""Microsoft Entra app registration (tenant, client id/secret) + Defender API base URL."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.endpoint_security.defender_for_endpoint.constants import DEFAULT_API_BASE_URL


def resolve_tenant_id(cfg: dict[str, Any]) -> str | None:
    v = cfg.get("tenant_id") or cfg.get("azure_tenant_id") or cfg.get("defender_tenant_id")
    if v is None or not str(v).strip():
        return None
    return str(v).strip()


def resolve_client_id(cfg: dict[str, Any]) -> str | None:
    v = cfg.get("client_id") or cfg.get("application_id") or cfg.get("defender_client_id")
    if v is None or not str(v).strip():
        return None
    return str(v).strip()


def resolve_client_secret(cfg: dict[str, Any]) -> str | None:
    v = cfg.get("client_secret") or cfg.get("defender_client_secret")
    if v is None or not str(v).strip():
        return None
    return str(v).strip()


def resolve_api_base_url(cfg: dict[str, Any]) -> str:
    v = cfg.get("api_base_url") or cfg.get("defender_endpoint_api_base_url") or cfg.get("mdatp_api_base_url")
    if v and str(v).strip():
        return str(v).strip().rstrip("/")
    return DEFAULT_API_BASE_URL


def resolve_verify_tls(cfg: dict[str, Any]) -> bool:
    v = cfg.get("verify_tls")
    if v is None:
        return True
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in ("1", "true", "yes", "y")


def credentials_valid_shape(cfg: dict[str, Any]) -> bool:
    return bool(resolve_tenant_id(cfg)) and bool(resolve_client_id(cfg)) and bool(resolve_client_secret(cfg))


def ready_for_collection(cfg: dict[str, Any]) -> bool:
    return credentials_valid_shape(cfg) and bool(resolve_api_base_url(cfg))
