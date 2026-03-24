from __future__ import annotations

import base64
import json
import os
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.integrations.categories.idp.microsoft_entra.constants import DEFAULT_GRAPH_SCOPES
from app.integrations.categories.idp.microsoft_entra.credentials import OAUTH_CLIENTS_KEY
from app.integrations.categories.idp.microsoft_entra.national_cloud import NationalCloud, default_graph_base_url, login_authority_host


def _log_oauth_http(r: httpx.Response) -> None:
    if os.environ.get("ENTRA_DEBUG_HTTP"):
        print(r.status_code, r.text)
    else:
        print(r.status_code, str(r.request.url), f"len={len(r.content)}")


def build_state(org_id: str, tool_id: str) -> str:
    payload = {"org_id": org_id, "tool_id": tool_id}
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def parse_state(state: str) -> dict[str, str]:
    pad = "=" * (-len(state) % 4)
    raw = base64.urlsafe_b64decode(state + pad)
    data = json.loads(raw.decode("utf-8"))
    if "org_id" not in data or "tool_id" not in data:
        raise ValueError("Invalid state")
    return {"org_id": str(data["org_id"]), "tool_id": str(data["tool_id"])}


def authorization_base(tenant_id: str, cloud: NationalCloud) -> str:
    t = tenant_id.strip() or "common"
    host = login_authority_host(cloud)
    return f"{host}/{t}/oauth2/v2.0"


def build_authorization_url(
    *,
    client_id: str,
    redirect_uri: str,
    tenant_id: str,
    state: str,
    cloud: NationalCloud,
    scopes: str | None = None,
) -> str:
    base = authorization_base(tenant_id, cloud) + "/authorize"
    scope_str = (scopes or DEFAULT_GRAPH_SCOPES).strip()
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "response_mode": "query",
        "scope": scope_str,
        "state": state,
    }
    return f"{base}?{urllib.parse.urlencode(params)}"


def exchange_code_for_tokens(
    *,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code: str,
    tenant_id: str,
    cloud: NationalCloud,
    scopes: str | None = None,
) -> dict[str, Any]:
    token_url = authorization_base(tenant_id, cloud) + "/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "code": code,
        "scope": (scopes or DEFAULT_GRAPH_SCOPES).strip(),
    }
    with httpx.Client(timeout=60.0) as client:
        r = client.post(token_url, data=data)
        _log_oauth_http(r)
        r.raise_for_status()
        return r.json()


def refresh_access_token(
    *,
    client_id: str,
    client_secret: str,
    refresh_token: str,
    tenant_id: str,
    cloud: NationalCloud,
    scopes: str | None = None,
) -> dict[str, Any]:
    token_url = authorization_base(tenant_id, cloud) + "/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }
    if scopes and scopes.strip():
        data["scope"] = scopes.strip()
    with httpx.Client(timeout=60.0) as client:
        r = client.post(token_url, data=data)
        _log_oauth_http(r)
        r.raise_for_status()
        return r.json()


def merge_token_response_into_config(
    cfg: dict[str, Any],
    token_payload: dict[str, Any],
    *,
    tenant_id: str,
    cloud: NationalCloud,
) -> dict[str, Any]:
    from app.integrations.categories.idp.microsoft_entra.constants import DEFAULT_GRAPH_SCOPES_GCC_HIGH

    new_cfg = dict(cfg)
    clients: list[dict[str, Any]] = list(new_cfg.get(OAUTH_CLIENTS_KEY) or [])
    if not clients:
        cid = new_cfg.get("client_id")
        sec = new_cfg.get("client_secret")
        nc = cloud.value
        default_scopes = DEFAULT_GRAPH_SCOPES_GCC_HIGH if cloud == NationalCloud.GCC_HIGH else DEFAULT_GRAPH_SCOPES
        clients = [
            {
                "client_id": str(cid) if cid is not None and str(cid).strip() else "",
                "client_secret": str(sec) if sec is not None else "",
                "redirect_uri": str(new_cfg.get("redirect_uri", "")),
                "tenant_id": str(new_cfg.get("tenant_id", tenant_id)),
                "national_cloud": nc,
                "scopes": str(new_cfg.get("scopes") or default_scopes),
            }
        ]

    idx = len(clients) - 1
    entry = dict(clients[idx])
    entry["tenant_id"] = tenant_id
    entry["national_cloud"] = cloud.value
    if "access_token" in token_payload:
        entry["access_token"] = token_payload["access_token"]
    if "refresh_token" in token_payload:
        entry["refresh_token"] = token_payload["refresh_token"]
    if "scope" in token_payload:
        entry["granted_scope"] = token_payload["scope"]
    expires_in = token_payload.get("expires_in")
    if expires_in is not None:
        exp = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
        entry["access_token_expires_at"] = exp.isoformat()
    clients[idx] = entry
    new_cfg[OAUTH_CLIENTS_KEY] = clients

    for k in (
        "access_token",
        "refresh_token",
        "access_token_expires_at",
        "client_id",
        "client_secret",
        "redirect_uri",
        "tenant_id",
        "scopes",
    ):
        new_cfg.pop(k, None)
    new_cfg["national_cloud"] = cloud.value
    new_cfg["graph_base_url"] = default_graph_base_url(cloud)
    return new_cfg
