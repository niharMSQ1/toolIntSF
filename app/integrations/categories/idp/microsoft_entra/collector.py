from __future__ import annotations

import os
from typing import Any

import httpx

from app.integrations.categories.idp.iam_evidence_catalog import ALL_IAM_EVIDENCE_CODES
from app.integrations.categories.idp.microsoft_entra.constants import MAX_GRAPH_PAGES
from app.integrations.categories.idp.microsoft_entra.credentials import graph_base_url, resolve_access_token
from app.integrations.categories.idp.microsoft_entra.seed import CODE_TO_COLLECTOR


def _log_http_line(r: httpx.Response, url: str) -> None:
    if os.environ.get("ENTRA_DEBUG_HTTP"):
        print(r.status_code, url, r.text[:500])
    else:
        print(r.status_code, url, f"len={len(r.content)}")


def _graph_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _graph_host(cfg: dict[str, Any]) -> str:
    u = graph_base_url(cfg).rstrip("/")
    for suf in ("/v1.0", "/beta"):
        if u.endswith(suf):
            return u[: -len(suf)]
    return u


def _v1(cfg: dict[str, Any]) -> str:
    return f"{_graph_host(cfg)}/v1.0"


def _beta(cfg: dict[str, Any]) -> str:
    return f"{_graph_host(cfg)}/beta"


def _graph_error_message(payload: dict[str, Any]) -> str | None:
    err = payload.get("error")
    if not err:
        return None
    if isinstance(err, dict):
        return str(err.get("message") or err.get("code") or err)
    return str(err)


def graph_get_paginated(
    start_url: str,
    access_token: str,
    *,
    max_pages: int = MAX_GRAPH_PAGES,
) -> dict[str, Any]:
    headers = _graph_headers(access_token)
    all_values: list[dict[str, Any]] = []
    url: str | None = start_url
    pages = 0
    with httpx.Client(timeout=120.0) as client:
        while url and pages < max_pages:
            r = client.get(url, headers=headers)
            _log_http_line(r, url)
            r.raise_for_status()
            data = r.json()
            if not isinstance(data, dict):
                raise ValueError("Microsoft Graph returned non-object JSON")
            gerr = _graph_error_message(data)
            if gerr:
                raise ValueError(f"Microsoft Graph error: {gerr}")
            vals = data.get("value")
            if isinstance(vals, list):
                for item in vals:
                    if isinstance(item, dict):
                        all_values.append(item)
            url = data.get("@odata.nextLink")
            if isinstance(url, str) and url.strip():
                url = url.strip()
            else:
                url = None
            pages += 1
    return {
        "value": all_values,
        "pages_fetched": pages,
        "truncated": pages >= max_pages,
    }


def graph_get_json(url: str, access_token: str) -> dict[str, Any]:
    headers = _graph_headers(access_token)
    with httpx.Client(timeout=120.0) as client:
        r = client.get(url, headers=headers)
        _log_http_line(r, url)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict):
            return data
        return {"value": data}


def _step_ok(label: str, url: str, token: str, *, paginate: bool = False) -> dict[str, Any]:
    try:
        body = graph_get_paginated(url, token) if paginate else graph_get_json(url, token)
        return {"label": label, "url": url, "response": body}
    except Exception as e:  # noqa: BLE001
        return {"label": label, "url": url, "error": str(e)[:4000]}


def _collect_by_code(code: str, cfg: dict[str, Any], token: str) -> dict[str, Any]:
    v1 = _v1(cfg)
    beta = _beta(cfg)
    steps: list[dict[str, Any]] = []

    if code == "EV-37":
        url = f"{v1}/users?$select=id,displayName,userPrincipalName,mail,accountEnabled,userType&$top=999"
        steps.append(_step_ok("users", url, token, paginate=True))

    elif code == "EV-39":
        roles_url = f"{v1}/directoryRoles?$top=100"
        roles = graph_get_paginated(roles_url, token)
        steps.append({"label": "directoryRoles", "url": roles_url, "response": roles})
        for r in roles.get("value", [])[:8]:
            rid = r.get("id")
            if not rid:
                continue
            mu = f"{v1}/directoryRoles/{rid}/members?$top=100"
            steps.append(_step_ok(f"role_members:{r.get('displayName', rid)}", mu, token, paginate=True))

    elif code == "EV-40":
        steps.append(_step_ok("authenticationMethodsPolicy", f"{v1}/policies/authenticationMethodsPolicy", token))
        u0 = graph_get_paginated(f"{v1}/users?$top=5&$select=id", token)
        steps.append({"label": "users_sample", "response": u0})
        uids = [x.get("id") for x in u0.get("value", []) if isinstance(x, dict) and x.get("id")]
        for uid in uids[:3]:
            steps.append(
                _step_ok(
                    f"user_auth_methods:{uid}",
                    f"{v1}/users/{uid}/authentication/methods",
                    token,
                )
            )

    elif code == "EV-75":
        steps.append(_step_ok("groups", f"{v1}/groups?$top=200&$select=id,displayName,groupTypes", token, paginate=True))
        steps.append(
            _step_ok(
                "accessReview_definitions",
                f"{beta}/identityGovernance/accessReviews/definitions?$top=50",
                token,
                paginate=True,
            )
        )

    elif code == "EV-77":
        steps.append(_step_ok("authenticationMethodsPolicy", f"{v1}/policies/authenticationMethodsPolicy", token))
        steps.append(
            _step_ok(
                "conditionalAccessPolicies",
                f"{beta}/identity/conditionalAccess/policies?$top=100",
                token,
                paginate=True,
            )
        )

    elif code == "EV-78":
        steps.append(_step_ok("authenticationMethodsPolicy", f"{v1}/policies/authenticationMethodsPolicy", token))
        steps.append(_step_ok("authorizationPolicy", f"{v1}/policies/authorizationPolicy", token))

    elif code == "EV-126":
        steps.append(
            _step_ok(
                "applications",
                f"{v1}/applications?$top=200&$select=id,appId,displayName,signInAudience",
                token,
                paginate=True,
            )
        )

    elif code == "EV-127":
        steps.append(
            _step_ok(
                "signIns",
                f"{v1}/auditLogs/signIns?$top=100",
                token,
                paginate=True,
            )
        )

    elif code == "EV-151":
        steps.append(_step_ok("directoryRoles", f"{v1}/directoryRoles?$top=200", token, paginate=True))

    elif code == "EV-154":
        steps.append(_step_ok("authenticationMethodsPolicy", f"{v1}/policies/authenticationMethodsPolicy", token))

    elif code == "EV-167":
        steps.append(
            _step_ok(
                "conditionalAccessPolicies",
                f"{beta}/identity/conditionalAccess/policies?$top=100",
                token,
                paginate=True,
            )
        )

    elif code == "EV-189":
        steps.append(_step_ok("organization", f"{v1}/organization?$top=10", token, paginate=True))

    elif code == "EV-207":
        steps.append(
            _step_ok(
                "applications",
                f"{v1}/applications?$top=200&$select=id,appId,displayName,signInAudience",
                token,
                paginate=True,
            )
        )

    elif code == "EV-461":
        steps.append(
            _step_ok(
                "conditionalAccessPolicies",
                f"{beta}/identity/conditionalAccess/policies?$top=100",
                token,
                paginate=True,
            )
        )
        steps.append(
            _step_ok(
                "namedLocations",
                f"{beta}/identity/conditionalAccess/namedLocations?$top=100",
                token,
                paginate=True,
            )
        )

    elif code == "EV-463":
        steps.append(
            _step_ok(
                "namedLocations",
                f"{beta}/identity/conditionalAccess/namedLocations?$top=100",
                token,
                paginate=True,
            )
        )

    elif code == "EV-476":
        steps.append(_step_ok("authenticationMethodsPolicy", f"{v1}/policies/authenticationMethodsPolicy", token))

    elif code == "EV-522":
        steps.append(_step_ok("groups", f"{v1}/groups?$top=200&$select=id,displayName", token, paginate=True))
        steps.append(_step_ok("directoryRoles", f"{v1}/directoryRoles?$top=200", token, paginate=True))

    else:
        raise ValueError(f"Unknown IAM evidence code for Entra: {code!r}")

    return {
        "evidence_code": code,
        "integration": "microsoft_entra",
        "collectable_via_microsoft_graph": True,
        "data": {"steps": steps},
    }


def collect_for_master(master: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    code = str(master.get("code") or "")
    if code not in CODE_TO_COLLECTOR:
        raise ValueError(f"Unknown Entra evidence code: {code!r}")
    token = resolve_access_token(cfg)
    if not token:
        raise ValueError("Missing access_token; complete OAuth first.")
    if code not in ALL_IAM_EVIDENCE_CODES:
        raise ValueError(f"Evidence code not in IAM catalog: {code!r}")
    return _collect_by_code(code, cfg, token)


_STORE_DROP_KEYS: frozenset[str] = frozenset({"collectable_via_microsoft_graph"})


def graph_evidence_for_tool_storage(content: dict[str, Any]) -> Any:
    if isinstance(content, dict) and "data" in content:
        return content["data"]
    out = {k: v for k, v in content.items() if k not in _STORE_DROP_KEYS}
    if len(out) == 1 and "payload" in out:
        return out["payload"]
    return out
