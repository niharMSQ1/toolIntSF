from __future__ import annotations

import base64
import json
import os
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.integrations.categories.hrms.zoho_people.credentials import OAUTH_CLIENTS_KEY
from app.integrations.categories.hrms.zoho_people.regions import accounts_base_url, normalize_region, people_base_url


def _log_oauth_http(r: httpx.Response, *, endpoint: str) -> None:
    """Print HTTP status for each Zoho Accounts OAuth call."""
    line = f"[zoho_people] HTTP {r.status_code} | {endpoint} | {str(r.request.url)}"
    if os.environ.get("ZOHO_DEBUG_HTTP"):
        print(line, r.text)
    else:
        print(line, f"len={len(r.content)}")


DEFAULT_ZOHO_PEOPLE_SCOPES = (
    "ZOHOPEOPLE.forms.READ,"
    "ZOHOPEOPLE.leave.READ,"
    "ZOHOPEOPLE.training.READ,"
    "ZOHOPEOPLE.attendance.ALL,"
    "ZOHOPEOPLE.timetracker.ALL,"
    "ZOHOPEOPLE.files.READ"
)


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


def build_authorization_url(
    *,
    client_id: str,
    redirect_uri: str,
    region: str,
    state: str,
    scopes: str = DEFAULT_ZOHO_PEOPLE_SCOPES,
) -> str:
    base = accounts_base_url(region)
    params = {
        "scope": scopes,
        "client_id": client_id,
        "response_type": "code",
        "access_type": "offline",
        "redirect_uri": redirect_uri,
        "prompt": "consent",
        "state": state,
    }
    return f"{base}/oauth/v2/auth?{urllib.parse.urlencode(params)}"


def exchange_code_for_tokens(
    *,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code: str,
    accounts_server: str,
) -> dict[str, Any]:
    token_url = accounts_server.rstrip("/") + "/oauth/v2/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "code": code,
    }
    with httpx.Client(timeout=60.0) as client:
        r = client.post(token_url, data=data)
        _log_oauth_http(r, endpoint="accounts.oauth2.token (authorization_code)")
        r.raise_for_status()
        return r.json()


def refresh_access_token(
    *,
    client_id: str,
    client_secret: str,
    refresh_token: str,
    accounts_server: str,
) -> dict[str, Any]:
    token_url = accounts_server.rstrip("/") + "/oauth/v2/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }
    with httpx.Client(timeout=60.0) as client:
        r = client.post(token_url, data=data)
        _log_oauth_http(r, endpoint="accounts.oauth2.token (refresh_token)")
        r.raise_for_status()
        return r.json()


def merge_token_response_into_config(
    cfg: dict[str, Any],
    token_payload: dict[str, Any],
    *,
    region: str,
    accounts_server: str | None,
) -> dict[str, Any]:
    new_cfg = dict(cfg)
    clients: list[dict[str, Any]] = list(new_cfg.get(OAUTH_CLIENTS_KEY) or [])
    if not clients:
        cid = new_cfg.get("client_id")
        sec = new_cfg.get("client_secret")
        if cid and sec is not None and str(sec) != "":
            clients = [
                {
                    "client_id": str(cid),
                    "client_secret": str(sec),
                    "redirect_uri": str(new_cfg.get("redirect_uri", "")),
                    "region": normalize_region(str(new_cfg.get("region", region))),
                }
            ]
        else:
            raise ValueError("oauth_clients is required to store OAuth tokens")

    idx = len(clients) - 1
    entry = dict(clients[idx])
    r = normalize_region(region)
    entry["region"] = r
    if accounts_server:
        entry["accounts_server"] = accounts_server
    if "api_domain" in token_payload:
        entry["api_domain"] = token_payload["api_domain"]
    if "access_token" in token_payload:
        entry["access_token"] = token_payload["access_token"]
    if "refresh_token" in token_payload:
        entry["refresh_token"] = token_payload["refresh_token"]
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
        "accounts_server",
        "api_domain",
        "client_id",
        "client_secret",
        "redirect_uri",
        "region",
    ):
        new_cfg.pop(k, None)
    new_cfg["people_base_url"] = people_base_url(r)
    return new_cfg
