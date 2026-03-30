"""Collect OneLogin user payloads per evidence code."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.idp.onelogin import api_client
from app.integrations.categories.idp.onelogin.credentials import resolve_access_token, resolve_region, resolve_users_path
from app.integrations.categories.idp.iam_evidence_catalog import ALL_IAM_EVIDENCE_CODES

_CODE_FETCH_PLAN: dict[str, list[str]] = {c: ["users"] for c in ALL_IAM_EVIDENCE_CODES}


def collect_for_master(master: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    code = str(master.get("code") or "")
    token = resolve_access_token(cfg)
    if not token:
        return {
            "evidence_code": code,
            "integration": "onelogin",
            "collectable_via_onelogin_api": False,
            "message": "access_token missing; complete OAuth client_credentials via configure.",
        }
    plan = _CODE_FETCH_PLAN.get(code)
    if not plan:
        return {
            "evidence_code": code,
            "integration": "onelogin",
            "collectable_via_onelogin_api": False,
            "message": "No automated fetch plan for this code.",
        }
    region = resolve_region(cfg)
    path = resolve_users_path(cfg)
    steps: list[dict[str, Any]] = []
    for _ in plan:
        steps.append(
            {
                "resource": "users",
                "region": region,
                "path": path,
                "response": api_client.list_users(cfg, token),
            }
        )
        break
    return {
        "evidence_code": code,
        "integration": "onelogin",
        "onelogin_region": region,
        "collectable_via_onelogin_api": True,
        "data": {"steps": steps},
    }


def onelogin_evidence_for_storage(content: dict[str, Any]) -> dict[str, Any]:
    return content if isinstance(content, dict) else {"payload": content}
