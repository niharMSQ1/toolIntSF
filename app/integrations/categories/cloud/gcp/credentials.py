"""GCP integration credential helpers."""

from __future__ import annotations

import json
from typing import Any


def resolve_project_id(cfg: dict[str, Any]) -> str | None:
    p = cfg.get("project_id") or cfg.get("gcp_project_id")
    if p is None or not str(p).strip():
        return None
    return str(p).strip()


def resolve_service_account_info(cfg: dict[str, Any]) -> dict[str, Any] | None:
    raw = cfg.get("service_account_json") or cfg.get("gcp_service_account_json")
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return None
    return None


def credentials_valid_shape(cfg: dict[str, Any]) -> bool:
    info = resolve_service_account_info(cfg)
    pid = resolve_project_id(cfg)
    if not info or not pid:
        return False
    # Basic service-account keys.
    required = ("type", "client_email", "private_key", "token_uri")
    if any(not info.get(k) for k in required):
        return False
    return str(info.get("type", "")).strip() == "service_account"


def ready_for_collection(cfg: dict[str, Any]) -> bool:
    return credentials_valid_shape(cfg)

