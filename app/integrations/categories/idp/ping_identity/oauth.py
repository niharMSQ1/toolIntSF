"""PingOne OAuth 2.0 client credentials (documented: POST {authBase}/{envId}/as/token)."""

from __future__ import annotations

import base64
from typing import Any

import httpx


def exchange_client_credentials(
    *,
    auth_base: str,
    token_environment_id: str,
    client_id: str,
    client_secret: str,
    scope: str | None = None,
) -> dict[str, Any]:
    """
    Obtain an access token per PingOne Platform APIs:
    POST ``{authBase}/{environmentID}/as/token`` with grant_type=client_credentials.

    Client authentication via HTTP Basic (client_id:client_secret) is documented on the token endpoint pages.
    """
    token_url = f"{auth_base.rstrip('/')}/{token_environment_id}/as/token"
    pair = f"{client_id}:{client_secret}"
    basic = base64.b64encode(pair.encode("utf-8")).decode("ascii")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "Authorization": f"Basic {basic}",
    }
    data: dict[str, str] = {"grant_type": "client_credentials"}
    if scope and scope.strip():
        data["scope"] = scope.strip()
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
