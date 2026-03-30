"""Workday OAuth 2.0 token endpoint (client credentials and refresh token)."""

from __future__ import annotations

import os
from typing import Any

import httpx


def _log(msg: str) -> None:
    if os.environ.get("WORKDAY_DEBUG_OAUTH"):
        print(msg)


def build_token_url(hostname: str, tenant: str) -> str:
    """``POST https://{{hostname}}/ccx/oauth2/{{tenant}}/token`` — documented Workday pattern."""
    return f"{hostname.rstrip('/')}/ccx/oauth2/{tenant}/token"


def exchange_client_credentials(
    *,
    hostname: str,
    tenant: str,
    client_id: str,
    client_secret: str,
    scope: str | None = None,
) -> dict[str, Any]:
    url = build_token_url(hostname, tenant)
    data: dict[str, str] = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    if scope and scope.strip():
        data["scope"] = scope.strip()
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    with httpx.Client(timeout=60.0) as client:
        r = client.post(url, data=data, headers=headers)
        _log(f"Workday token status={r.status_code}")
        r.raise_for_status()
        return r.json()


def refresh_access_token(
    *,
    hostname: str,
    tenant: str,
    client_id: str,
    client_secret: str,
    refresh_token: str,
) -> dict[str, Any]:
    url = build_token_url(hostname, tenant)
    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    with httpx.Client(timeout=60.0) as client:
        r = client.post(url, data=data, headers=headers)
        r.raise_for_status()
        return r.json()


def merge_token_response_into_config(cfg: dict[str, Any], token_payload: dict[str, Any]) -> dict[str, Any]:
    new_cfg = dict(cfg)
    if "access_token" in token_payload:
        new_cfg["access_token"] = token_payload["access_token"]
    if token_payload.get("refresh_token"):
        new_cfg["refresh_token"] = str(token_payload["refresh_token"])
    if token_payload.get("expires_in") is not None:
        new_cfg["expires_in"] = token_payload["expires_in"]
    if token_payload.get("token_type"):
        new_cfg["token_type"] = token_payload["token_type"]
    return new_cfg
