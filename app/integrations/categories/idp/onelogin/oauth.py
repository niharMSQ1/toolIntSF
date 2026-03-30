from __future__ import annotations

from typing import Any

import httpx

from app.integrations.categories.idp.onelogin.credentials import resolve_region, token_url_for_region


def exchange_client_credentials(*, cfg: dict[str, Any], client_id: str, client_secret: str) -> dict[str, Any]:
    region = resolve_region(cfg)
    url = token_url_for_region(region)
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    with httpx.Client(timeout=60.0) as client:
        r = client.post(url, data=data, headers=headers)
        r.raise_for_status()
        return r.json()


def merge_token_into_config(cfg: dict[str, Any], token_payload: dict[str, Any]) -> dict[str, Any]:
    new_cfg = dict(cfg)
    if "access_token" in token_payload:
        new_cfg["access_token"] = token_payload["access_token"]
    if token_payload.get("expires_in") is not None:
        new_cfg["expires_in"] = token_payload["expires_in"]
    return new_cfg
