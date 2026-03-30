"""Collect JumpCloud user payloads per evidence code."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.idp.jumpcloud import api_client
from app.integrations.categories.idp.jumpcloud.credentials import resolve_api_key
from app.integrations.categories.idp.iam_evidence_catalog import ALL_IAM_EVIDENCE_CODES

_CODE_FETCH_PLAN: dict[str, list[str]] = {c: ["users"] for c in ALL_IAM_EVIDENCE_CODES}


def collect_for_master(master: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    code = str(master.get("code") or "")
    try:
        key = resolve_api_key(cfg)
    except ValueError:
        return {
            "evidence_code": code,
            "integration": "jumpcloud",
            "collectable_via_jumpcloud_api": False,
            "message": "jumpcloud_api_key missing.",
        }
    plan = _CODE_FETCH_PLAN.get(code)
    if not plan:
        return {
            "evidence_code": code,
            "integration": "jumpcloud",
            "collectable_via_jumpcloud_api": False,
            "message": "No automated fetch plan for this code.",
        }
    steps: list[dict[str, Any]] = []
    for _ in plan:
        steps.append(
            {
                "resource": "systemusers",
                "response": api_client.list_system_users(cfg, key),
            }
        )
        break
    return {
        "evidence_code": code,
        "integration": "jumpcloud",
        "collectable_via_jumpcloud_api": True,
        "data": {"steps": steps},
    }


def jumpcloud_evidence_for_storage(content: dict[str, Any]) -> dict[str, Any]:
    return content if isinstance(content, dict) else {"payload": content}
