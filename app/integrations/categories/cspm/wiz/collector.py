"""Build evidence payloads per evidence_masters.code for Wiz CSPM."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.cspm.wiz import api_client
from app.integrations.categories.cspm.wiz.evidence_map import COLLECTABILITY_NOTES, EVIDENCE_CODE_STRATEGY, WizStrategy
from app.integrations.categories.cspm.wiz.credentials import resolve_graphql_url


def _mask_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    m = dict(cfg)
    for k in ("access_token", "client_secret", "refresh_token"):
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
    strategy: WizStrategy = EVIDENCE_CODE_STRATEGY.get(code, "partial_metadata")  # type: ignore[assignment]
    graphql_url = resolve_graphql_url(cfg)

    base: dict[str, Any] = {
        "evidence_code": code,
        "integration": "wiz",
        "wiz_graphql_endpoint": graphql_url,
    }

    if strategy == "export_only":
        note = COLLECTABILITY_NOTES.get(
            code,
            "Not represented as a single GraphQL export; use Wiz portal exports or procedural evidence.",
        )
        return {
            **base,
            "collectable_via_wiz_graphql_api": False,
            "strategy": strategy,
            "message": note,
        }

    if strategy == "integration_config":
        return {
            **base,
            "collectable_via_wiz_graphql_api": True,
            "strategy": strategy,
            "integration_configuration_masked": _mask_cfg(cfg),
            "note": "Connector scope is stored in this integration; full cloud connector matrix is configured in Wiz Settings.",
        }

    if strategy == "users":
        data = api_client.fetch_users_sample(graphql_url, access_token)
        return {
            **base,
            "collectable_via_wiz_graphql_api": True,
            "strategy": strategy,
            "data": data,
        }

    if strategy == "cloud_inventory":
        data = api_client.fetch_cloud_inventory_and_projects(graphql_url, access_token)
        return {
            **base,
            "collectable_via_wiz_graphql_api": True,
            "strategy": strategy,
            "data": data,
        }

    if strategy == "issues_critical_high":
        data = api_client.paginate_issues_critical_high(graphql_url, access_token)
        return {
            **base,
            "collectable_via_wiz_graphql_api": True,
            "strategy": strategy,
            "data": data,
        }

    if strategy == "vulnerability_findings":
        data = api_client.paginate_vulnerability_findings(graphql_url, access_token)
        return {
            **base,
            "collectable_via_wiz_graphql_api": True,
            "strategy": strategy,
            "data": data,
        }

    if strategy == "vulnerability_findings_container":
        data = api_client.paginate_vulnerability_findings(graphql_url, access_token)
        return {
            **base,
            "collectable_via_wiz_graphql_api": True,
            "strategy": strategy,
            "data": data,
            "note": "Wiz vulnerability findings API returns workload/container CVEs when ingested; filter by asset type in Wiz UI if needed.",
        }

    # issues (default posture mapping)
    if strategy == "issues":
        data = api_client.paginate_issues(graphql_url, access_token)
        return {
            **base,
            "collectable_via_wiz_graphql_api": True,
            "strategy": strategy,
            "data": data,
        }

    note = COLLECTABILITY_NOTES.get(code)
    return {
        **base,
        "collectable_via_wiz_graphql_api": False,
        "strategy": strategy,
        "message": note or "See Wiz documentation for API coverage of this control.",
    }


def wiz_evidence_for_storage(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize for JSON storage in evidence_collections.tool_evidence."""
    return payload
