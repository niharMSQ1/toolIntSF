"""Evidence payloads for Sysdig Secure."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.cspm.sysdig_secure import api_client
from app.integrations.categories.cspm.sysdig_secure.credentials import (
    resolve_api_base_url,
    resolve_api_token,
    resolve_verify_tls,
)
from app.integrations.categories.cspm.sysdig_secure.evidence_map import EVIDENCE_CODE_STRATEGY, SysdigStrategy


def _mask_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    m = dict(cfg)
    for k in ("api_token", "sysdig_api_token", "token"):
        if k in m and m[k]:
            m[k] = "***"
    return m


def collect_for_master(master: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    code = str(master.get("code") or "")
    strategy: SysdigStrategy = EVIDENCE_CODE_STRATEGY.get(code, "partial_metadata")  # type: ignore[assignment]
    base_url = resolve_api_base_url(cfg)
    token = resolve_api_token(cfg) or ""
    verify = resolve_verify_tls(cfg)
    base: dict[str, Any] = {
        "evidence_code": code,
        "integration": "sysdig_secure",
        "api_base_url": base_url,
        "strategy": strategy,
    }

    if strategy == "agents_connected":
        data = api_client.get_agents_connected(base_url, token, verify_tls=verify)
        return {**base, "collectable_via_sysdig_api": True, "data": data}

    if strategy == "user_me_minimal":
        data = api_client.get_user_me(base_url, token, verify_tls=verify)
        return {
            **base,
            "collectable_via_sysdig_api": True,
            "data": data,
            "note": "Current user / tenant context (redact in downstream if needed).",
        }

    if strategy == "partial_metadata":
        return {
            **base,
            "collectable_via_sysdig_api": True,
            "message": "Sysdig uses Bearer API token (see README).",
            "integration_configuration_masked": _mask_cfg(cfg),
        }

    return {**base, "collectable_via_sysdig_api": False, "integration_configuration_masked": _mask_cfg(cfg)}


def sysdig_evidence_for_storage(payload: dict[str, Any]) -> dict[str, Any]:
    return payload
