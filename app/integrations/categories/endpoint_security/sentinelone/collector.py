"""Evidence payloads for SentinelOne."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.endpoint_security.sentinelone import api_client, normalization
from app.integrations.categories.endpoint_security.sentinelone.credentials import (
    resolve_api_base_url,
    resolve_api_token,
    resolve_verify_tls,
)
from app.integrations.categories.endpoint_security.sentinelone.evidence_map import (
    EVIDENCE_CODE_STRATEGY,
    SentinelOneStrategy,
)


def _mask_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    m = dict(cfg)
    if m.get("api_token"):
        m["api_token"] = "***"
    if m.get("sentinelone_api_token"):
        m["sentinelone_api_token"] = "***"
    return m


def collect_for_master(master: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    code = str(master.get("code") or "")
    strategy: SentinelOneStrategy = EVIDENCE_CODE_STRATEGY.get(code, "agents_list")  # type: ignore[assignment]
    root = resolve_api_base_url(cfg)
    token = resolve_api_token(cfg) or ""
    verify = resolve_verify_tls(cfg)
    base: dict[str, Any] = {
        "evidence_code": code,
        "integration": "sentinelone",
        "api_base_url": root,
        "strategy": strategy,
    }

    if strategy == "agents_list":
        raw = api_client.list_agents(root, token, limit=50, verify_tls=verify)
        norm = normalization.normalize_agents_payload(raw)
        return {**base, "collectable_via_sentinelone_api": True, "normalized": norm, "raw": raw}

    if strategy == "threats_list":
        raw = api_client.list_threats(root, token, limit=50, verify_tls=verify)
        norm = normalization.normalize_threats_payload(raw)
        return {**base, "collectable_via_sentinelone_api": True, "normalized": norm, "raw": raw}

    if strategy == "installed_applications_list":
        raw = api_client.list_installed_applications(root, token, limit=50, verify_tls=verify)
        norm = normalization.normalize_installed_applications_payload(raw)
        return {**base, "collectable_via_sentinelone_api": True, "normalized": norm, "raw": raw}

    return {**base, "collectable_via_sentinelone_api": False, "integration_configuration_masked": _mask_cfg(cfg)}


def sentinelone_evidence_for_storage(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    raw = out.get("raw")
    if isinstance(raw, dict) and len(str(raw)) > 500_000:
        out["raw"] = {"truncated": True, "note": "raw payload too large; see normalized.items"}
    return out
