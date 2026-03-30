"""Collect CyberArk Identity SCIM payloads per evidence code."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.idp.cyberark import api_client
from app.integrations.categories.idp.cyberark.credentials import resolve_access_token, resolve_identity_base_url
from app.integrations.categories.idp.iam_evidence_catalog import ALL_IAM_EVIDENCE_CODES

_CODE_FETCH_PLAN: dict[str, list[str]] = {c: ["users"] for c in ALL_IAM_EVIDENCE_CODES}


def collect_for_master(master: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    code = str(master.get("code") or "")
    token = resolve_access_token(cfg)
    if not token:
        return {
            "evidence_code": code,
            "integration": "cyberark_identity",
            "collectable_via_cyberark_api": False,
            "message": "access_token missing; complete OAuth client_credentials via configure.",
        }
    plan = _CODE_FETCH_PLAN.get(code)
    if not plan:
        return {
            "evidence_code": code,
            "integration": "cyberark_identity",
            "collectable_via_cyberark_api": False,
            "message": "No automated fetch plan for this code.",
        }
    base = resolve_identity_base_url(cfg)
    steps: list[dict[str, Any]] = []
    for _ in plan:
        steps.append(
            {
                "resource": "scim_users",
                "path": f"{base}/scim/Users",
                "response": api_client.list_scim_users(cfg, token, count=200),
            }
        )
        break
    return {
        "evidence_code": code,
        "integration": "cyberark_identity",
        "identity_base_url": base,
        "collectable_via_cyberark_api": True,
        "data": {"steps": steps},
    }


def cyberark_evidence_for_storage(content: dict[str, Any]) -> dict[str, Any]:
    return content if isinstance(content, dict) else {"payload": content}
