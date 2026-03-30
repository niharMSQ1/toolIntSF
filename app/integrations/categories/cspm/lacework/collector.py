"""Evidence payloads for Lacework."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.cspm.lacework import api_client
from app.integrations.categories.cspm.lacework.credentials import (
    resolve_api_base_url,
    resolve_key_id,
    resolve_secret,
)
from app.integrations.categories.cspm.lacework.evidence_map import EVIDENCE_CODE_STRATEGY, LaceworkStrategy


def _mask_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    m = dict(cfg)
    for k in ("secret", "api_secret", "lacework_secret"):
        if k in m and m[k]:
            m[k] = "***"
    return m


def collect_for_master(master: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    code = str(master.get("code") or "")
    strategy: LaceworkStrategy = EVIDENCE_CODE_STRATEGY.get(code, "partial_metadata")  # type: ignore[assignment]
    base_url = resolve_api_base_url(cfg)
    kid = resolve_key_id(cfg) or ""
    sec = resolve_secret(cfg) or ""
    token = api_client.generate_access_token(base_url, kid, sec)
    base: dict[str, Any] = {
        "evidence_code": code,
        "integration": "lacework",
        "api_base_url": base_url,
        "strategy": strategy,
    }

    if strategy == "alerts_list":
        data = api_client.list_alerts(base_url, token)
        return {**base, "collectable_via_lacework_api": True, "data": data}

    if strategy == "org_info_minimal":
        data = api_client.get_organization_info(base_url, token)
        return {
            **base,
            "collectable_via_lacework_api": True,
            "data": data,
            "note": "OrganizationInfo for tenant connectivity.",
        }

    if strategy == "partial_metadata":
        return {
            **base,
            "collectable_via_lacework_api": True,
            "message": "Lacework uses API v2 key id + secret (see README).",
            "integration_configuration_masked": _mask_cfg(cfg),
        }

    return {**base, "collectable_via_lacework_api": False, "integration_configuration_masked": _mask_cfg(cfg)}


def lacework_evidence_for_storage(payload: dict[str, Any]) -> dict[str, Any]:
    return payload
