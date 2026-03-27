"""Collect Okta Admin API payloads per evidence_masters.code."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.idp.okta import api_client
from app.integrations.categories.idp.okta.credentials import resolve_api_token, resolve_okta_base_url

# (path, query_params) — multiple steps merged under path keys in ``data``.
_CODE_FETCH_PLAN: dict[str, list[tuple[str, dict[str, Any]]]] = {
    "EV-37": [("/api/v1/users", {"limit": 200})],
    "EV-39": [
        ("/api/v1/roles", {"limit": 200}),
        ("/api/v1/groups", {"limit": 200}),
    ],
    "EV-40": [
        ("/api/v1/org/factors", {}),
        ("/api/v1/users", {"limit": 50}),
    ],
    "EV-75": [
        ("/api/v1/groups", {"limit": 200}),
        ("/api/v1/apps", {"limit": 200}),
    ],
    "EV-77": [("/api/v1/policies", {"type": "PASSWORD", "limit": 200})],
    "EV-78": [("/api/v1/policies", {"type": "OKTA_SIGN_ON", "limit": 200})],
    "EV-126": [("/api/v1/idps", {"limit": 200})],
    "EV-127": [("/api/v1/logs", {"limit": 100})],
    "EV-151": [("/api/v1/roles", {"limit": 200})],
    "EV-154": [("/api/v1/org/factors", {})],
    "EV-167": [("/api/v1/policies", {"limit": 200})],
    "EV-189": [("/api/v1/org", {})],
    "EV-207": [("/api/v1/apps", {"limit": 200})],
    "EV-461": [("/api/v1/policies", {"type": "OKTA_SIGN_ON", "limit": 200})],
    "EV-463": [("/api/v1/zones", {"limit": 200})],
    "EV-476": [("/api/v1/policies", {"type": "PASSWORD", "limit": 200})],
    "EV-522": [
        ("/api/v1/groups", {"limit": 200}),
        ("/api/v1/roles", {"limit": 200}),
    ],
}


def collect_for_master(master: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    code = str(master.get("code") or "")
    base = resolve_okta_base_url(cfg)
    token = resolve_api_token(cfg)
    plan = _CODE_FETCH_PLAN.get(code)
    if not plan:
        return {
            "evidence_code": code,
            "integration": "okta",
            "collectable_via_okta_api": False,
            "message": f"No Okta fetch plan for code {code}.",
        }
    steps: list[dict[str, Any]] = []
    for path, params in plan:
        steps.append(
            {
                "path": path,
                "query": params,
                "response": api_client.get_json(base, path, token, params=params),
            }
        )
    return {
        "evidence_code": code,
        "integration": "okta",
        "okta_org_url": base,
        "collectable_via_okta_api": True,
        "data": {"steps": steps},
    }


def okta_evidence_for_storage(content: dict[str, Any]) -> dict[str, Any]:
    return content if isinstance(content, dict) else {"payload": content}
