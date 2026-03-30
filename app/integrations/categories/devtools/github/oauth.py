"""GitHub OAuth App authorization code flow."""

from __future__ import annotations

import base64
import json
import urllib.parse
from typing import Any

import httpx

from app.integrations.categories.devtools.github.constants import (
    DEFAULT_GITHUB_OAUTH_SCOPES,
    GITHUB_OAUTH_ACCESS_TOKEN,
    GITHUB_OAUTH_AUTHORIZE,
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
    scopes: str = DEFAULT_GITHUB_OAUTH_SCOPES,
) -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scopes.strip(),
        "state": state,
        "allow_signup": "false",
    }
    return f"{GITHUB_OAUTH_AUTHORIZE}?{urllib.parse.urlencode(params)}"


def exchange_code_for_token(
    *,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code: str,
) -> dict[str, Any]:
    """
    POST https://github.com/login/oauth/access_token
    (Accept: application/json — https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps)
    """
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    with httpx.Client(timeout=60.0) as client:
        r = client.post(GITHUB_OAUTH_ACCESS_TOKEN, data=data, headers=headers)
        r.raise_for_status()
        return r.json()


def merge_token_into_config(cfg: dict[str, Any], token_payload: dict[str, Any]) -> dict[str, Any]:
    new_cfg = dict(cfg)
    if "access_token" in token_payload:
        new_cfg["access_token"] = token_payload["access_token"]
    if token_payload.get("token_type"):
        new_cfg["github_token_type"] = token_payload["token_type"]
    if token_payload.get("scope"):
        new_cfg["github_oauth_scope"] = token_payload["scope"]
    return new_cfg
