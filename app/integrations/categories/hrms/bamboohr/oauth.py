"""BambooHR OAuth 2.0 helpers.

Official BambooHR docs used for this helper shape:
- https://documentation.bamboohr.com/docs/getting-started

Important implementation note:
- BambooHR OAuth is company-domain scoped, so the company subdomain is part of
  both the authorization and token URLs.
"""

from __future__ import annotations

import base64
import json
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx


DEFAULT_BAMBOOHR_SCOPES = "employees:read offline_access"


def build_state(org_id: str, tool_id: str) -> str:
    """Encode the tenant/tool context so the callback knows where to save tokens."""
    payload = {"org_id": org_id, "tool_id": tool_id}
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def parse_state(state: str) -> dict[str, str]:
    """Decode the OAuth state payload from the callback."""
    pad = "=" * (-len(state) % 4)
    raw = base64.urlsafe_b64decode(state + pad)
    data = json.loads(raw.decode("utf-8"))
    if "org_id" not in data or "tool_id" not in data:
        raise ValueError("Invalid state")
    return {"org_id": str(data["org_id"]), "tool_id": str(data["tool_id"])}


def build_authorization_url(
    *,
    company_domain: str,
    client_id: str,
    redirect_uri: str,
    state: str,
    scopes: str = DEFAULT_BAMBOOHR_SCOPES,
) -> str:
    """Build the BambooHR browser authorization URL."""
    params = {
        "request": "authorize",
        "state": state,
        "response_type": "code",
        "scope": scopes,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
    }
    return f"https://{company_domain}.bamboohr.com/authorize.php?{urllib.parse.urlencode(params)}"


def exchange_code_for_tokens(
    *,
    company_domain: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code: str,
) -> dict[str, Any]:
    """Exchange the temporary authorization code for BambooHR tokens."""
    token_url = f"https://{company_domain}.bamboohr.com/token.php?request=token"
    payload = {
        "client_secret": client_secret,
        "client_id": client_id,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }
    with httpx.Client(timeout=60.0) as client:
        response = client.post(token_url, json=payload, headers={"Accept": "application/json"})
        response.raise_for_status()
        return response.json()


def refresh_access_token(
    *,
    company_domain: str,
    client_id: str,
    client_secret: str,
    refresh_token: str,
    redirect_uri: str,
) -> dict[str, Any]:
    """Refresh BambooHR access tokens using a refresh token."""
    token_url = f"https://{company_domain}.bamboohr.com/token.php?request=token"
    payload = {
        "client_secret": client_secret,
        "client_id": client_id,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
        "redirect_uri": redirect_uri,
    }
    with httpx.Client(timeout=60.0) as client:
        response = client.post(token_url, json=payload, headers={"Accept": "application/json"})
        response.raise_for_status()
        return response.json()


def merge_token_response_into_config(cfg: dict[str, Any], token_payload: dict[str, Any]) -> dict[str, Any]:
    """Store BambooHR OAuth tokens in configuration_data without discarding existing setup."""
    new_cfg = dict(cfg)
    if "access_token" in token_payload:
        new_cfg["access_token"] = token_payload["access_token"]
    if token_payload.get("refresh_token"):
        new_cfg["refresh_token"] = token_payload["refresh_token"]
    expires_in = token_payload.get("expires_in")
    if expires_in is not None:
        expiry = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
        new_cfg["access_token_expires_at"] = expiry.isoformat()
    if token_payload.get("scope"):
        new_cfg["oauth_scope"] = token_payload["scope"]
    if token_payload.get("companyDomain"):
        new_cfg["company_domain"] = token_payload["companyDomain"]
        new_cfg["subdomain"] = token_payload["companyDomain"]
    return new_cfg

