"""Collect PingOne Management API payloads per evidence_masters.code (documented endpoints only)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.integrations.categories.idp.ping_identity import api_client
from app.integrations.categories.idp.ping_identity.credentials import (
    resolve_access_token,
    resolve_api_base,
    resolve_environment_id,
)


def _activities_filter_last_days(days: int = 7) -> str:
    """SCIM-style filter with date bounds (required for GET /activities per PingOne audit docs)."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=min(max(days, 1), 14))
    s = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    e = end.strftime("%Y-%m-%dT%H:%M:%SZ")
    return f'recordedAt ge "{s}" and recordedAt le "{e}"'


# (fetch_fn_name, extra) — resolved in collect_for_master
_CODE_FETCH_PLAN: dict[str, list[str]] = {
    "EV-37": ["users"],
    "EV-39": ["populations", "applications"],
    "EV-40": ["users"],
    "EV-75": ["populations", "applications"],
    "EV-126": ["applications"],
    "EV-127": ["activities"],
    "EV-151": ["populations"],
    "EV-189": ["activities"],
    "EV-207": ["applications"],
    "EV-463": ["applications"],
    "EV-522": ["populations", "applications"],
}


def collect_for_master(master: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    code = str(master.get("code") or "")
    token = resolve_access_token(cfg)
    if not token:
        return {
            "evidence_code": code,
            "integration": "ping_identity",
            "collectable_via_pingone_api": False,
            "message": "access_token missing; complete OAuth client_credentials via configure.",
        }
    plan = _CODE_FETCH_PLAN.get(code)
    if not plan:
        return {
            "evidence_code": code,
            "integration": "ping_identity",
            "collectable_via_pingone_api": False,
            "message": (
                "No automated PingOne fetch plan for this evidence code yet; "
                "use documented Management API paths from the PingOne Platform APIs reference."
            ),
        }
    env = resolve_environment_id(cfg)
    base = resolve_api_base(cfg)
    steps: list[dict[str, Any]] = []
    for step in plan:
        if step == "users":
            steps.append(
                {
                    "resource": "users",
                    "path": f"{base}/environments/{env}/users",
                    "response": api_client.list_users(cfg, token, limit=200),
                }
            )
        elif step == "populations":
            steps.append(
                {
                    "resource": "populations",
                    "path": f"{base}/environments/{env}/populations",
                    "response": api_client.list_populations(cfg, token, limit=200),
                }
            )
        elif step == "applications":
            steps.append(
                {
                    "resource": "applications",
                    "path": f"{base}/environments/{env}/applications",
                    "response": api_client.list_applications(cfg, token, limit=200),
                }
            )
        elif step == "activities":
            steps.append(
                {
                    "resource": "activities",
                    "path": f"{base}/environments/{env}/activities",
                    "filter": _activities_filter_last_days(7),
                    "response": api_client.list_activities(
                        cfg,
                        token,
                        filter_expr=_activities_filter_last_days(7),
                        limit=100,
                    ),
                }
            )
    return {
        "evidence_code": code,
        "integration": "ping_identity",
        "pingone_environment_id": env,
        "pingone_api_base": base,
        "collectable_via_pingone_api": True,
        "data": {"steps": steps},
    }


def ping_evidence_for_storage(content: dict[str, Any]) -> dict[str, Any]:
    return content if isinstance(content, dict) else {"payload": content}
