"""Azure AD app registration + subscription scope for Defender for Cloud ARM APIs."""

from __future__ import annotations

import re
from typing import Any

_UUID = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def resolve_tenant_id(cfg: dict[str, Any]) -> str | None:
    v = cfg.get("tenant_id") or cfg.get("azure_tenant_id")
    if v is None or not str(v).strip():
        return None
    return str(v).strip()


def resolve_client_id(cfg: dict[str, Any]) -> str | None:
    v = cfg.get("client_id") or cfg.get("azure_client_id")
    if v is None or not str(v).strip():
        return None
    return str(v).strip()


def resolve_client_secret(cfg: dict[str, Any]) -> str | None:
    v = cfg.get("client_secret") or cfg.get("azure_client_secret")
    if v is None or not str(v).strip():
        return None
    return str(v).strip()


def resolve_subscription_id(cfg: dict[str, Any]) -> str | None:
    v = cfg.get("subscription_id") or cfg.get("azure_subscription_id")
    if v is None or not str(v).strip():
        return None
    s = str(v).strip()
    return s if _UUID.match(s) else None


def credentials_valid_shape(cfg: dict[str, Any]) -> bool:
    if not resolve_tenant_id(cfg) or not resolve_client_id(cfg) or not resolve_client_secret(cfg):
        return False
    if not resolve_subscription_id(cfg):
        return False
    return True


def ready_for_collection(cfg: dict[str, Any]) -> bool:
    return credentials_valid_shape(cfg)
