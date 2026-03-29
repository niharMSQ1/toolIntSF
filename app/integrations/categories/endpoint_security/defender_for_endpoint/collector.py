"""Evidence payloads for Microsoft Defender for Endpoint."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.endpoint_security.defender_for_endpoint import api_client, normalization
from app.integrations.categories.endpoint_security.defender_for_endpoint.credentials import (
    resolve_api_base_url,
    resolve_client_id,
    resolve_client_secret,
    resolve_tenant_id,
    resolve_verify_tls,
)
from app.integrations.categories.endpoint_security.defender_for_endpoint.evidence_map import (
    EVIDENCE_CODE_STRATEGY,
    DefenderEndpointStrategy,
)


def _mask_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    m = dict(cfg)
    if m.get("client_secret"):
        m["client_secret"] = "***"
    return m


def collect_for_master(master: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    code = str(master.get("code") or "")
    strategy: DefenderEndpointStrategy = EVIDENCE_CODE_STRATEGY.get(code, "machines_list")  # type: ignore[assignment]
    tenant = resolve_tenant_id(cfg) or ""
    cid = resolve_client_id(cfg) or ""
    csec = resolve_client_secret(cfg) or ""
    base_url = resolve_api_base_url(cfg)
    verify = resolve_verify_tls(cfg)
    token, _ = api_client.get_access_token(tenant, cid, csec, verify_tls=verify)
    base: dict[str, Any] = {
        "evidence_code": code,
        "integration": "defender_for_endpoint",
        "api_base_url": base_url,
        "strategy": strategy,
    }

    if strategy == "machines_list":
        raw = api_client.list_machines(base_url, token, top=50, verify_tls=verify)
        norm = normalization.normalize_machines_payload(raw)
        return {**base, "collectable_via_defender_api": True, "normalized": norm, "raw": raw}

    if strategy == "alerts_list":
        raw = api_client.list_alerts(base_url, token, top=50, verify_tls=verify)
        norm = normalization.normalize_alerts_payload(raw)
        return {**base, "collectable_via_defender_api": True, "normalized": norm, "raw": raw}

    if strategy == "vulnerabilities_list":
        raw = api_client.list_machine_vulnerabilities(base_url, token, top=50, verify_tls=verify)
        norm = normalization.normalize_vulnerabilities_payload(raw)
        return {**base, "collectable_via_defender_api": True, "normalized": norm, "raw": raw}

    return {**base, "collectable_via_defender_api": False, "integration_configuration_masked": _mask_cfg(cfg)}


def defender_for_endpoint_evidence_for_storage(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    raw = out.get("raw")
    if isinstance(raw, dict) and len(str(raw)) > 500_000:
        out["raw"] = {"truncated": True, "note": "raw payload too large; see normalized.items"}
    return out
