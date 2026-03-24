from __future__ import annotations

import os
from typing import Any

import httpx

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


def collect_for_master(master: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    code = str(master.get("code") or "")
    key = CODE_TO_COLLECTOR.get(code)
    token = resolve_access_token(cfg)
    if not token:
        raise ValueError("Missing access_token; complete OAuth first.")
    base = graph_base_url(cfg)

    if key == "directory_users":
        url = f"{base}/users?$select=id,displayName,userPrincipalName,mail,accountEnabled,userType&$top=999"
        payload = graph_get_paginated(url, token)
        return {"collector_key": key, "graph_path": "/users", "payload": payload}

    if key == "directory_groups":
        url = (
            f"{base}/groups?$select=id,displayName,groupTypes,mail,mailEnabled,securityEnabled&$top=999"
        )
        payload = graph_get_paginated(url, token)
        return {"collector_key": key, "graph_path": "/groups", "payload": payload}

    raise ValueError(f"Unknown Entra collector for code={code!r}")


_STORE_DROP_KEYS: frozenset[str] = frozenset({"collector_key", "graph_path"})


def graph_evidence_for_tool_storage(content: dict[str, Any]) -> Any:
    out = {k: v for k, v in content.items() if k not in _STORE_DROP_KEYS}
    if len(out) == 1 and "payload" in out:
        return out["payload"]
    return out
