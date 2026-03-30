from __future__ import annotations

from typing import Any

from app.integrations.categories.idp.google_workspace import api_client
from app.integrations.categories.idp.google_workspace.credentials import resolve_access_token, resolve_workspace_domain
from app.integrations.categories.idp.iam_evidence_catalog import ALL_IAM_EVIDENCE_CODES

_CODE_FETCH_PLAN: dict[str, list[str]] = {c: ["users"] for c in ALL_IAM_EVIDENCE_CODES}


def collect_for_master(master: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    code = str(master.get("code") or "")
    token = resolve_access_token(cfg)
    if not token:
        return {
            "evidence_code": code,
            "integration": "google_workspace",
            "collectable_via_google_api": False,
            "message": "access_token missing; refresh OAuth or set tokens.",
        }
    plan = _CODE_FETCH_PLAN.get(code)
    if not plan:
        return {
            "evidence_code": code,
            "integration": "google_workspace",
            "collectable_via_google_api": False,
            "message": "No fetch plan for this code.",
        }
    domain = resolve_workspace_domain(cfg)
    steps: list[dict[str, Any]] = []
    for _ in plan:
        steps.append(
            {
                "resource": "directory_users",
                "domain": domain,
                "response": api_client.list_users(cfg, token, max_results=200),
            }
        )
        break
    return {
        "evidence_code": code,
        "integration": "google_workspace",
        "google_workspace_domain": domain,
        "collectable_via_google_api": True,
        "data": {"steps": steps},
    }


def google_workspace_evidence_for_storage(content: dict[str, Any]) -> dict[str, Any]:
    return content if isinstance(content, dict) else {"payload": content}
