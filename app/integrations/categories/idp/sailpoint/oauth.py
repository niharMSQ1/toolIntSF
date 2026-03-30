"""SailPoint IdentityNow OAuth 2.0 — POST {base}/oauth/token (client_credentials)."""

from __future__ import annotations

from typing import Any

import httpx


def exchange_client_credentials(
    *,
    api_base: str,
    client_id: str,
    client_secret: str,
) -> dict[str, Any]:
    token_url = f"{api_base.rstrip('/')}/oauth/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    with httpx.Client(timeout=60.0) as client:
        r = client.post(token_url, data=data, headers=headers)
        r.raise_for_status()
        return r.json()


def merge_token_into_config(cfg: dict[str, Any], token_payload: dict[str, Any]) -> dict[str, Any]:
    new_cfg = dict(cfg)
    if "access_token" in token_payload:
        new_cfg["access_token"] = token_payload["access_token"]
    if token_payload.get("expires_in") is not None:
        new_cfg["expires_in"] = token_payload["expires_in"]
    return new_cfg
