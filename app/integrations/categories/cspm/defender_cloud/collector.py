"""Evidence payloads per evidence_masters.code — Microsoft Defender for Cloud (ARM)."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.cspm.defender_cloud import api_client
from app.integrations.categories.cspm.defender_cloud.credentials import resolve_subscription_id
from app.integrations.categories.cspm.defender_cloud.evidence_map import EVIDENCE_CODE_STRATEGY, DefenderStrategy


def _mask_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    m = dict(cfg)
    for k in ("client_secret", "azure_client_secret", "azure_access_token"):
        if k in m and m[k]:
            m[k] = "***"
    return m


def collect_for_master(
    master: dict[str, Any],
    cfg: dict[str, Any],
    *,
    access_token: str,
) -> dict[str, Any]:
    code = str(master.get("code") or "")
    strategy: DefenderStrategy = EVIDENCE_CODE_STRATEGY.get(code, "partial_metadata")  # type: ignore[assignment]
    sub = resolve_subscription_id(cfg)
    base: dict[str, Any] = {
        "evidence_code": code,
        "integration": "defender_cloud",
        "subscription_id": sub,
        "strategy": strategy,
    }

    if strategy == "assessments" and sub:
        data = api_client.list_assessments(sub, access_token)
        return {
            **base,
            "collectable_via_azure_arm": True,
            "data": data,
            "note": "GET .../Microsoft.Security/assessments — paginated via nextLink (capped in client).",
        }

    if strategy == "secure_scores" and sub:
        data = api_client.list_secure_scores(sub, access_token)
        return {**base, "collectable_via_azure_arm": True, "data": data}

    if strategy == "partial_metadata":
        return {
            **base,
            "collectable_via_azure_arm": True,
            "message": "OAuth2 client credentials token obtained for scope https://management.azure.com/.default.",
            "integration_configuration_masked": _mask_cfg(cfg),
        }

    return {
        **base,
        "collectable_via_azure_arm": False,
        "integration_configuration_masked": _mask_cfg(cfg),
        "message": "Missing subscription_id or unknown strategy.",
    }


def defender_evidence_for_storage(payload: dict[str, Any]) -> dict[str, Any]:
    return payload
