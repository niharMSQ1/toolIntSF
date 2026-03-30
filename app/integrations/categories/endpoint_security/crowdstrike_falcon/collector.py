"""Evidence payloads for CrowdStrike Falcon."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.endpoint_security.crowdstrike_falcon import api_client, normalization
from app.integrations.categories.endpoint_security.crowdstrike_falcon.credentials import (
    resolve_api_base_url,
    resolve_client_id,
    resolve_client_secret,
    resolve_member_cid,
    resolve_spotlight_filter_fql,
    resolve_verify_tls,
)
from app.integrations.categories.endpoint_security.crowdstrike_falcon.evidence_map import EVIDENCE_CODE_STRATEGY, FalconStrategy


def _mask_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    m = dict(cfg)
    for k in ("client_secret", "falcon_client_secret"):
        if k in m and m[k]:
            m[k] = "***"
    return m


def collect_for_master(master: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    code = str(master.get("code") or "")
    strategy: FalconStrategy = EVIDENCE_CODE_STRATEGY.get(code, "hosts_query")  # type: ignore[assignment]
    base_url = resolve_api_base_url(cfg)
    cid = resolve_client_id(cfg) or ""
    csec = resolve_client_secret(cfg) or ""
    member = resolve_member_cid(cfg)
    verify = resolve_verify_tls(cfg)
    token, _ = api_client.get_access_token(base_url, cid, csec, member_cid=member, verify_tls=verify)
    base: dict[str, Any] = {
        "evidence_code": code,
        "integration": "crowdstrike_falcon",
        "api_base_url": base_url,
        "strategy": strategy,
    }

    if strategy == "hosts_query":
        raw = api_client.query_devices(base_url, token, limit=50, verify_tls=verify)
        norm = normalization.normalize_host_query_payload(raw)
        return {
            **base,
            "collectable_via_falcon_api": True,
            "normalized": norm,
            "raw": raw,
        }

    if strategy == "detects_query":
        raw = api_client.query_detects(base_url, token, limit=50, verify_tls=verify)
        norm = normalization.normalize_detects_query_payload(raw)
        return {
            **base,
            "collectable_via_falcon_api": True,
            "normalized": norm,
            "raw": raw,
        }

    if strategy == "spotlight_vulns":
        fql = resolve_spotlight_filter_fql(cfg)
        raw = api_client.query_spotlight_combined_vulnerabilities(
            base_url, token, filter_fql=fql, limit=50, verify_tls=verify
        )
        norm = normalization.normalize_spotlight_combined_payload(raw)
        return {
            **base,
            "collectable_via_falcon_api": True,
            "normalized": norm,
            "raw": raw,
            "spotlight_filter_fql": fql,
        }

    return {**base, "collectable_via_falcon_api": False, "integration_configuration_masked": _mask_cfg(cfg)}


def crowdstrike_evidence_for_storage(payload: dict[str, Any]) -> dict[str, Any]:
    """Strip large raw if needed — keep normalized for controls."""
    out = dict(payload)
    raw = out.get("raw")
    if isinstance(raw, dict) and len(str(raw)) > 500_000:
        out["raw"] = {"truncated": True, "note": "raw payload too large; see normalized.items"}
    return out
