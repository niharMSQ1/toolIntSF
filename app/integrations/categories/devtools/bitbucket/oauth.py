"""Bitbucket Cloud OAuth 2.0 helpers."""

from __future__ import annotations

import base64
import json
import os
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.config import get_settings
from app.integrations.categories.devtools.bitbucket.constants import (
    BITBUCKET_AUTH_URL,
    BITBUCKET_TOKEN_URL,
    DEFAULT_BITBUCKET_SCOPES,
)


def _log_http(r: httpx.Response) -> None:
    if os.environ.get("BITBUCKET_DEBUG_HTTP"):
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


def resolve_scopes() -> str:
    s = get_settings()
    raw = getattr(s, "bitbucket_oauth_scopes", None)
    if raw and str(raw).strip():
        return " ".join(str(raw).split())
    return DEFAULT_BITBUCKET_SCOPES


def build_authorization_url(
    *,
    client_id: str,
    redirect_uri: str,
    state: str,
    scopes: str | None = None,
) -> str:
    sc = scopes or resolve_scopes()
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": sc,
        "state": state,
    }
    return f"{BITBUCKET_AUTH_URL}?{urllib.parse.urlencode(params)}"


def exchange_code_for_tokens(
    *,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code: str,
) -> dict[str, Any]:
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }
    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            BITBUCKET_TOKEN_URL,
            data=data,
            auth=(client_id, client_secret),
        )
        _log_http(r)
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
        "refresh_token": refresh_token,
    }
    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            BITBUCKET_TOKEN_URL,
            data=data,
            auth=(client_id, client_secret),
        )
        _log_http(r)
        r.raise_for_status()
        return r.json()


def merge_token_response_into_config(
    cfg: dict[str, Any],
    token_payload: dict[str, Any],
    *,
    clear_workspace_selection: bool = False,
) -> dict[str, Any]:
    new_cfg = dict(cfg)
    if "access_token" in token_payload:
        new_cfg["access_token"] = token_payload["access_token"]
    if "refresh_token" in token_payload:
        new_cfg["refresh_token"] = token_payload["refresh_token"]
    expires_in = token_payload.get("expires_in")
    if expires_in is not None:
        exp = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
        new_cfg["access_token_expires_at"] = exp.isoformat()
    new_cfg["oauth_completed_at"] = datetime.now(timezone.utc).isoformat()
    if clear_workspace_selection:
        new_cfg.pop("workspace_selection_completed_at", None)
        new_cfg.pop("selected_workspaces", None)
    return new_cfg
