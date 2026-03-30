"""Persist Prisma Cloud JWT; login or extend before collection."""

from __future__ import annotations

import time
from typing import Any

from sqlalchemy.orm import Session

from app.integrations.categories.cspm.prisma_cloud import api_client
from app.integrations.categories.cspm.prisma_cloud.credentials import (
    resolve_access_key_id,
    resolve_api_base_url,
    resolve_secret_key,
)
from app.integrations.core.persistence import tool_integration_service as persistence


def _epoch(cfg: dict[str, Any]) -> float | None:
    v = cfg.get("prisma_jwt_obtained_at")
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def ensure_prisma_jwt(session: Session, integration_row: dict[str, Any]) -> dict[str, Any]:
    """
    Return configuration_data with a fresh prisma_jwt when possible.

    Order: valid cached JWT → GET /auth_token/extend → POST /login.
    """
    cfg = dict(integration_row.get("configuration_data") or {})
    base = resolve_api_base_url(cfg)
    ak = resolve_access_key_id(cfg)
    sk = resolve_secret_key(cfg)
    if not base or not ak or not sk:
        return cfg

    jwt = cfg.get("prisma_jwt")
    epoch = _epoch(cfg)
    if jwt and str(jwt).strip() and epoch is not None and not api_client.jwt_needs_refresh(epoch):
        return cfg

    try:
        if jwt and str(jwt).strip():
            new_tok = api_client.extend_session(base, str(jwt))
        else:
            raise api_client.PrismaCloudApiError("no cached jwt")
    except api_client.PrismaCloudApiError:
        new_tok = api_client.login(base, ak, sk)

    new_cfg = dict(cfg)
    new_cfg["prisma_jwt"] = new_tok
    new_cfg["prisma_jwt_obtained_at"] = time.time()
    persistence.save_tool_integration_config(session, integration_row["id"], new_cfg)
    return new_cfg
