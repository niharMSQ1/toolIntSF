"""
Lacework HTTP API v2.

Token exchange and headers follow lacework/go-sdk:
POST https://{account}.lacework.net/api/v2/access/tokens
JSON body: keyId, expiryTime; header X-LW-UAKS: secret.
Other calls: Authorization: <token> (raw token, not necessarily Bearer).

References: https://docs.lacework.net/api/v2/docs/ (tenant OpenAPI),
https://github.com/lacework/go-sdk (api/auth.go, api/http.go).
"""

from __future__ import annotations

from typing import Any

import httpx

from app.integrations.categories.cspm.lacework.constants import (
    ACCESS_TOKENS_PATH,
    ALERTS_PATH,
    ORGANIZATION_INFO_PATH,
    USER_PROFILE_PATH,
)


class LaceworkApiError(Exception):
    """Non-success HTTP or unexpected Lacework API response."""


def _token_headers(access_token: str) -> dict[str, str]:
    """Lacework go-sdk sets Authorization to the raw JWT string (no Bearer prefix)."""
    return {
        "Authorization": access_token.strip(),
        "Accept": "application/json",
    }


def generate_access_token(
    api_base_url: str,
    key_id: str,
    secret: str,
    *,
    expiry_seconds: int = 3600,
    timeout: float = 45.0,
) -> str:
    # https://github.com/lacework/go-sdk/blob/main/api/auth.go — tokenRequest
    url = f"{api_base_url.rstrip('/')}{ACCESS_TOKENS_PATH}"
    body = {"keyId": key_id, "expiryTime": expiry_seconds}
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-LW-UAKS": secret,
    }
    with httpx.Client(timeout=timeout) as client:
        r = client.post(url, headers=headers, json=body)
    if r.status_code != 200:
        raise LaceworkApiError(f"Lacework token HTTP {r.status_code}: {r.text[:2000]}")
    try:
        data = r.json()
    except Exception as e:  # noqa: BLE001
        raise LaceworkApiError(f"Invalid JSON: {e}") from e
    token = data.get("token")
    if not token or not str(token).strip():
        raise LaceworkApiError(str(data)[:2000])
    return str(token).strip()


def validate_credentials(api_base_url: str, key_id: str, secret: str, *, timeout: float = 45.0) -> None:
    """Generate token and GET UserProfile (read-only sanity check)."""
    token = generate_access_token(api_base_url, key_id, secret, timeout=timeout)
    get_user_profile(api_base_url, token, timeout=timeout)


def get_user_profile(api_base_url: str, access_token: str, *, timeout: float = 45.0) -> dict[str, Any]:
    url = f"{api_base_url.rstrip('/')}{USER_PROFILE_PATH}"
    with httpx.Client(timeout=timeout) as client:
        r = client.get(url, headers=_token_headers(access_token))
    if r.status_code != 200:
        raise LaceworkApiError(f"Lacework UserProfile HTTP {r.status_code}: {r.text[:2000]}")
    try:
        return r.json()
    except Exception as e:  # noqa: BLE001
        raise LaceworkApiError(f"Invalid JSON: {e}") from e


def get_organization_info(api_base_url: str, access_token: str, *, timeout: float = 45.0) -> dict[str, Any]:
    url = f"{api_base_url.rstrip('/')}{ORGANIZATION_INFO_PATH}"
    with httpx.Client(timeout=timeout) as client:
        r = client.get(url, headers=_token_headers(access_token))
    if r.status_code != 200:
        raise LaceworkApiError(f"Lacework OrganizationInfo HTTP {r.status_code}: {r.text[:2000]}")
    try:
        return r.json()
    except Exception as e:  # noqa: BLE001
        raise LaceworkApiError(f"Invalid JSON: {e}") from e


def list_alerts(api_base_url: str, access_token: str, *, timeout: float = 60.0) -> dict[str, Any]:
    """GET /api/v2/Alerts (first page)."""
    url = f"{api_base_url.rstrip('/')}{ALERTS_PATH}"
    with httpx.Client(timeout=timeout) as client:
        r = client.get(url, headers=_token_headers(access_token))
    if r.status_code != 200:
        raise LaceworkApiError(f"Lacework Alerts HTTP {r.status_code}: {r.text[:2000]}")
    try:
        return r.json()
    except Exception as e:  # noqa: BLE001
        raise LaceworkApiError(f"Invalid JSON: {e}") from e
