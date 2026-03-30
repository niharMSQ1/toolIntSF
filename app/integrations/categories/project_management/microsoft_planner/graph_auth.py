"""Acquire Microsoft Graph access tokens — OAuth 2.0 client credentials or refresh token."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx


def _token_url(tenant_id: str) -> str:
    return f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"


def fetch_token_client_credentials(
    *,
    tenant_id: str,
    client_id: str,
    client_secret: str,
    scope: str = "https://graph.microsoft.com/.default",
) -> dict[str, Any]:
    """Client credentials grant — https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-client-creds-grant-flow"""
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": scope,
        "grant_type": "client_credentials",
    }
    with httpx.Client(timeout=60.0) as client:
        r = client.post(_token_url(tenant_id), data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        r.raise_for_status()
        return r.json()


def fetch_token_refresh(
    *,
    tenant_id: str,
    client_id: str,
    client_secret: str,
    refresh_token: str,
    scope: str = "https://graph.microsoft.com/.default offline_access",
) -> dict[str, Any]:
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
        "scope": scope,
    }
    with httpx.Client(timeout=60.0) as client:
        r = client.post(_token_url(tenant_id), data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        r.raise_for_status()
        return r.json()


def merge_token_into_config(cfg: dict[str, Any], token_payload: dict[str, Any]) -> dict[str, Any]:
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


def token_expired(cfg: dict[str, Any], *, skew_seconds: int = 120) -> bool:
    raw = cfg.get("access_token_expires_at")
    if not raw or not str(raw).strip():
        return True
    try:
        exp = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return True
    return datetime.now(timezone.utc) >= exp - timedelta(seconds=skew_seconds)
