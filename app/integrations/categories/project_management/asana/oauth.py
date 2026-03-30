"""Asana OAuth 2.0 authorization code flow — https://developers.asana.com/docs/oauth"""

from __future__ import annotations

import base64
import json
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.integrations.categories.project_management.asana.constants import (
    ASANA_OAUTH_AUTHORIZE,
    ASANA_OAUTH_TOKEN,
    DEFAULT_ASANA_SCOPES,
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
    state: str,
    scopes: str = DEFAULT_ASANA_SCOPES,
) -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "state": state,
        "scope": scopes.strip(),
    }
    return f"{ASANA_OAUTH_AUTHORIZE}?{urllib.parse.urlencode(params)}"


def exchange_code_for_tokens(
    *,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code: str,
) -> dict[str, Any]:
    """POST application/x-www-form-urlencoded to ASANA_OAUTH_TOKEN."""
    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "code": code,
    }
    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            ASANA_OAUTH_TOKEN,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        )
        r.raise_for_status()
        return r.json()


def refresh_access_token(
    *,
    client_id: str,
    client_secret: str,
    refresh_token: str,
) -> dict[str, Any]:
    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }
    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            ASANA_OAUTH_TOKEN,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        )
        r.raise_for_status()
        return r.json()


def merge_token_response_into_config(cfg: dict[str, Any], token_payload: dict[str, Any]) -> dict[str, Any]:
    new_cfg = dict(cfg)
    if "access_token" in token_payload:
        new_cfg["access_token"] = token_payload["access_token"]
    if token_payload.get("refresh_token"):
        new_cfg["refresh_token"] = token_payload["refresh_token"]
    exp = token_payload.get("expires_in")
    if exp is not None:
        at = datetime.now(timezone.utc) + timedelta(seconds=int(exp))
        new_cfg["access_token_expires_at"] = at.isoformat()
    return new_cfg
