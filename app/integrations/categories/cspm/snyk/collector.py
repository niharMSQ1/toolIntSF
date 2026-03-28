"""Build evidence payloads per evidence_masters.code for Snyk."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.cspm.snyk import api_client
from app.integrations.categories.cspm.snyk.constants import MAX_ISSUES_PER_SCOPE
from app.integrations.categories.cspm.snyk.credentials import (
    AUTH_TYPE_OAUTH2,
    has_credentials_for_api,
    resolve_auth_type,
    resolve_group_id,
    resolve_org_ids,
)
from app.integrations.categories.cspm.snyk.evidence_map import EVIDENCE_CODE_STRATEGY, SnykStrategy
from app.integrations.categories.cspm.snyk.regions import resolve_rest_base_url


def _mask_cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    m = dict(cfg)
    for k in ("snyk_api_token", "api_token", "token", "oauth_client_secret", "client_secret", "oauth_access_token"):
        if k in m and m[k]:
            m[k] = "***"
    return m


def _region(cfg: dict[str, Any]) -> str | None:
    r = cfg.get("region")
    return str(r).strip() if r is not None and str(r).strip() else None


def _issue_cap_per_org(org_count: int) -> int:
    if org_count <= 0:
        return MAX_ISSUES_PER_SCOPE
    return max(400, min(MAX_ISSUES_PER_SCOPE // org_count, MAX_ISSUES_PER_SCOPE))


def _require_usable_auth(cfg: dict[str, Any]) -> None:
    if not has_credentials_for_api(cfg):
        raise ValueError("Missing Snyk credentials (API token or OAuth client credentials / access token).")
    if resolve_auth_type(cfg) == AUTH_TYPE_OAUTH2 and not (cfg.get("oauth_access_token") and str(cfg["oauth_access_token"]).strip()):
        raise ValueError("Missing OAuth access token; re-run POST /configure to exchange client credentials.")


def _load_all_issues(cfg: dict[str, Any]) -> tuple[list[dict[str, Any]], str | None]:
    gid = resolve_group_id(cfg)
    if gid:
        issues = api_client.list_issues_for_group(cfg, gid)
        return issues, None
    orgs = resolve_org_ids(cfg)
    merged: list[dict[str, Any]] = []
    cap = _issue_cap_per_org(len(orgs))
    for oid in orgs:
        merged.extend(api_client.list_issues_for_org(cfg, oid, max_items=cap))
    return merged, gid


def _load_projects_by_org(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for oid in resolve_org_ids(cfg):
        projects = api_client.list_projects_for_org(cfg, oid)
        out.append({"org_id": oid, "project_count": len(projects), "projects_sample": projects[:200]})
    return out


def collect_for_master(master: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    code = str(master.get("code") or "")
    strategy: SnykStrategy = EVIDENCE_CODE_STRATEGY.get(code, "issues_summary")  # type: ignore[assignment]
    _require_usable_auth(cfg)

    region = _region(cfg)
    rest_base = resolve_rest_base_url(region)
    base: dict[str, Any] = {
        "evidence_code": code,
        "integration": "snyk",
        "snyk_rest_base": rest_base,
        "strategy": strategy,
        "auth_type": resolve_auth_type(cfg),
    }

    if strategy == "integration_config":
        orgs_meta = api_client.list_orgs_v1(cfg)
        projects_payload = _load_projects_by_org(cfg) if resolve_org_ids(cfg) else []
        return {
            **base,
            "collectable_via_snyk_api": True,
            "integration_configuration_masked": _mask_cfg(cfg),
            "orgs_list_sample": orgs_meta[:50],
            "projects_by_org": projects_payload,
            "note": "Snyk scan configuration is represented by org/project inventory and stored integration scope.",
        }

    gid = resolve_group_id(cfg)
    if not gid and not resolve_org_ids(cfg):
        return {
            **base,
            "collectable_via_snyk_api": False,
            "message": "Set org_ids (or org_id) or group_id in configuration_data to scope Snyk collection.",
        }

    all_issues, _used_group = _load_all_issues(cfg)

    if strategy == "dependency_issues":
        dep = [x for x in all_issues if api_client.is_dependency_style_issue(api_client.issue_attributes(x))]
        return {
            **base,
            "collectable_via_snyk_api": True,
            "issue_count_total": len(all_issues),
            "issue_count_dependency_filtered": len(dep),
            "severity_summary": api_client.summarize_severity(dep),
            "sample": api_client.remediation_subset(dep, 300),
        }

    if strategy == "projects_config":
        if gid:
            return {
                **base,
                "collectable_via_snyk_api": True,
                "message": "Group-scoped integration: project listing uses org endpoints; provide org_ids for per-project configuration export.",
                "group_id": gid,
            }
        projects_payload = _load_projects_by_org(cfg)
        return {
            **base,
            "collectable_via_snyk_api": True,
            "data": projects_payload,
        }

    if strategy == "issues_summary":
        return {
            **base,
            "collectable_via_snyk_api": True,
            "issue_count": len(all_issues),
            "severity_summary": api_client.summarize_severity(all_issues),
            "sample": api_client.remediation_subset(all_issues, 400),
        }

    if strategy == "remediation":
        return {
            **base,
            "collectable_via_snyk_api": True,
            "issue_count": len(all_issues),
            "remediation_focus_sample": api_client.remediation_subset(all_issues, 500),
        }

    if strategy == "code_issues":
        code_issues = [x for x in all_issues if api_client.is_code_style_issue(api_client.issue_attributes(x))]
        return {
            **base,
            "collectable_via_snyk_api": True,
            "issue_count_total": len(all_issues),
            "issue_count_code_filtered": len(code_issues),
            "severity_summary": api_client.summarize_severity(code_issues),
            "sample": api_client.remediation_subset(code_issues, 300),
        }

    if strategy == "vuln_scan_summary":
        dep = sum(1 for x in all_issues if api_client.is_dependency_style_issue(api_client.issue_attributes(x)))
        cod = sum(1 for x in all_issues if api_client.is_code_style_issue(api_client.issue_attributes(x)))
        return {
            **base,
            "collectable_via_snyk_api": True,
            "totals": {
                "all_issues": len(all_issues),
                "dependency_like": dep,
                "code_like": cod,
            },
            "severity_summary": api_client.summarize_severity(all_issues),
            "sample": api_client.remediation_subset(all_issues, 250),
        }

    return {
        **base,
        "collectable_via_snyk_api": False,
        "message": "No collector mapping for this code.",
    }


def snyk_evidence_for_storage(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize for JSON storage in evidence_collections.tool_evidence."""
    return payload
