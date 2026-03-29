"""Evidence payloads for Orca Security."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.cspm.orca_security import api_client
from app.integrations.categories.cspm.orca_security.credentials import resolve_api_base_url, resolve_api_token
from app.integrations.categories.cspm.orca_security.evidence_map import EVIDENCE_CODE_STRATEGY, OrcaStrategy


def _mask_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    m = dict(cfg)
    for k in ("api_token", "orca_api_token"):
        if k in m and m[k]:
            m[k] = "***"
    return m


def collect_for_master(
    master: dict[str, Any],
    cfg: dict[str, Any],
) -> dict[str, Any]:
    code = str(master.get("code") or "")
    strategy: OrcaStrategy = EVIDENCE_CODE_STRATEGY.get(code, "partial_metadata")  # type: ignore[assignment]
    base_url = resolve_api_base_url(cfg)
    token = resolve_api_token(cfg) or ""
    base: dict[str, Any] = {
        "evidence_code": code,
        "integration": "orca_security",
        "api_base_url": base_url,
        "strategy": strategy,
    }

    if strategy == "alerts_query":
        data = api_client.query_alerts(base_url, token, limit=100, page=1)
        return {**base, "collectable_via_orca_api": True, "data": data}

    if strategy == "alerts_minimal":
        data = api_client.query_alerts(base_url, token, limit=1, page=1)
        return {
            **base,
            "collectable_via_orca_api": True,
            "data": data,
            "note": "Minimal query (limit=1) for connectivity and sample shape.",
        }

    if strategy == "partial_metadata":
        return {
            **base,
            "collectable_via_orca_api": True,
            "message": "Orca uses API token auth (see README).",
            "integration_configuration_masked": _mask_cfg(cfg),
        }

    return {**base, "collectable_via_orca_api": False, "integration_configuration_masked": _mask_cfg(cfg)}


def orca_evidence_for_storage(payload: dict[str, Any]) -> dict[str, Any]:
    return payload
