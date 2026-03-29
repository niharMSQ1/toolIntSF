"""Evidence payloads for Aqua CSP."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.cspm.aqua_security import api_client
from app.integrations.categories.cspm.aqua_security.credentials import (
    resolve_api_base_url,
    resolve_login_id,
    resolve_password,
    resolve_verify_tls,
)
from app.integrations.categories.cspm.aqua_security.evidence_map import EVIDENCE_CODE_STRATEGY, AquaStrategy


def _mask_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    m = dict(cfg)
    for k in ("password", "aqua_password"):
        if k in m and m[k]:
            m[k] = "***"
    return m


def collect_for_master(master: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    code = str(master.get("code") or "")
    strategy: AquaStrategy = EVIDENCE_CODE_STRATEGY.get(code, "partial_metadata")  # type: ignore[assignment]
    base_url = resolve_api_base_url(cfg)
    lid = resolve_login_id(cfg) or ""
    pw = resolve_password(cfg) or ""
    verify = resolve_verify_tls(cfg)
    token = api_client.login_csp(base_url, lid, pw, verify_tls=verify)
    base: dict[str, Any] = {
        "evidence_code": code,
        "integration": "aqua_security",
        "api_base_url": base_url,
        "strategy": strategy,
    }

    if strategy == "hosts_list":
        data = api_client.list_hosts(base_url, token, verify_tls=verify)
        return {**base, "collectable_via_aqua_api": True, "data": data}

    if strategy == "images_minimal":
        data = api_client.list_images(base_url, token, verify_tls=verify)
        return {
            **base,
            "collectable_via_aqua_api": True,
            "data": data,
            "note": "Container images inventory (CSPM-relevant workload coverage).",
        }

    if strategy == "partial_metadata":
        return {
            **base,
            "collectable_via_aqua_api": True,
            "message": "Aqua CSP uses POST /api/v1/login (see README).",
            "integration_configuration_masked": _mask_cfg(cfg),
        }

    return {**base, "collectable_via_aqua_api": False, "integration_configuration_masked": _mask_cfg(cfg)}


def aqua_evidence_for_storage(payload: dict[str, Any]) -> dict[str, Any]:
    return payload
