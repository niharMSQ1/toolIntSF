"""Wiz OAuth2 client credentials (service account)."""

from __future__ import annotations

from typing import Any

import httpx


def fetch_client_credentials_token(
    *,
    client_id: str,
    client_secret: str,
    auth_url: str = "https://auth.app.wiz.io/oauth/token",
    audience: str = "wiz-api",
    timeout_sec: float = 60.0,
) -> dict[str, Any]:
    """
    Exchange client_id/client_secret for an access token.

    Returns raw JSON including access_token, expires_in, token_type.
    """
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": audience,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    with httpx.Client(timeout=timeout_sec) as client:
        r = client.post(auth_url, data=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
    if not isinstance(data, dict) or not data.get("access_token"):
        raise ValueError("Token response missing access_token")
    return data
