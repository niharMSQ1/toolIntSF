"""Collect SailPoint IdentityNow payloads per evidence code."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.idp.iam_evidence_catalog import ALL_IAM_EVIDENCE_CODES
from app.integrations.categories.idp.sailpoint import api_client
from app.integrations.categories.idp.sailpoint.credentials import resolve_access_token, resolve_api_base, resolve_identities_path

_CODE_FETCH_PLAN: dict[str, list[str]] = {c: ["identities"] for c in ALL_IAM_EVIDENCE_CODES}


def collect_for_master(master: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    code = str(master.get("code") or "")
    token = resolve_access_token(cfg)
    if not token:
        return {
            "evidence_code": code,
            "integration": "sailpoint_identitynow",
            "collectable_via_sailpoint_api": False,
            "message": "access_token missing; complete OAuth client_credentials via configure.",
        }
    plan = _CODE_FETCH_PLAN.get(code)
    if not plan:
        return {
            "evidence_code": code,
            "integration": "sailpoint_identitynow",
            "collectable_via_sailpoint_api": False,
            "message": "No automated fetch plan for this code.",
        }
    base = resolve_api_base(cfg)
    path = resolve_identities_path(cfg)
    steps: list[dict[str, Any]] = []
    for _ in plan:
        steps.append(
            {
                "resource": "public_identities",
                "path": f"{base}{path}",
                "response": api_client.list_public_identities(cfg, token, limit=200),
            }
        )
        break
    return {
        "evidence_code": code,
        "integration": "sailpoint_identitynow",
        "api_base_url": base,
        "collectable_via_sailpoint_api": True,
        "data": {"steps": steps},
    }


def sailpoint_evidence_for_storage(content: dict[str, Any]) -> dict[str, Any]:
    return content if isinstance(content, dict) else {"payload": content}
