"""Build evidence payloads per evidence_masters.code for Prisma Cloud CSPM REST."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.cspm.prisma_cloud import api_client
from app.integrations.categories.cspm.prisma_cloud.credentials import resolve_api_base_url
from app.integrations.categories.cspm.prisma_cloud.evidence_map import EVIDENCE_CODE_STRATEGY, PrismaStrategy


def _mask_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    m = dict(cfg)
    for k in ("secret_key", "password", "prisma_jwt"):
        if k in m and m[k]:
            m[k] = "***"
    return m


def collect_for_master(
    master: dict[str, Any],
    cfg: dict[str, Any],
    *,
    jwt: str,
) -> dict[str, Any]:
    code = str(master.get("code") or "")
    strategy: PrismaStrategy = EVIDENCE_CODE_STRATEGY.get(code, "partial_metadata")  # type: ignore[assignment]
    base_url = resolve_api_base_url(cfg)
    base: dict[str, Any] = {
        "evidence_code": code,
        "integration": "prisma_cloud",
        "api_base_url": base_url,
        "strategy": strategy,
    }

    if strategy == "cloud_accounts":
        data = api_client.get_cloud_accounts(base_url, jwt)
        return {**base, "collectable_via_prisma_api": True, "data": data}

    if strategy == "alerts_v2":
        data = api_client.get_alerts_v2(base_url, jwt)
        return {
            **base,
            "collectable_via_prisma_api": True,
            "data": data,
            "note": "GET /v2/alert — rate limits per Palo Alto docs: 2/sec, burst 10/sec.",
        }

    if strategy == "compliance_posture_v2":
        data = api_client.get_compliance_posture_v2(base_url, jwt)
        return {**base, "collectable_via_prisma_api": True, "data": data}

    if strategy == "partial_metadata":
        return {
            **base,
            "collectable_via_prisma_api": True,
            "message": "JWT session validated during collection (POST /login or GET /auth_token/extend).",
            "integration_configuration_masked": _mask_cfg(cfg),
        }

    return {
        **base,
        "collectable_via_prisma_api": False,
        "integration_configuration_masked": _mask_cfg(cfg),
        "message": "Unknown strategy for Prisma Cloud.",
    }


def prisma_evidence_for_storage(payload: dict[str, Any]) -> dict[str, Any]:
    return payload
