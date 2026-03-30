"""
Microsoft Defender for Cloud via Azure Resource Manager (ARM).

Authentication: OAuth 2.0 client credentials to Microsoft identity platform, scope for ARM.
See: https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-client-creds-grant-flow

Endpoints (Microsoft Learn — Defender for Cloud REST):
- GET .../providers/Microsoft.Security/assessments
- GET .../providers/Microsoft.Security/secureScores
"""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlencode

import httpx

from app.integrations.categories.cspm.defender_cloud.constants import (
    API_VERSION_ASSESSMENTS,
    API_VERSION_SECURE_SCORES,
    ARM_BASE_URL,
    ARM_SCOPE_DEFAULT,
)


class DefenderCloudApiError(Exception):
    """Non-success HTTP or auth failure for Defender / ARM."""


def get_client_credentials_token(
    tenant_id: str,
    client_id: str,
    client_secret: str,
    *,
    scope: str = ARM_SCOPE_DEFAULT,
    timeout: float = 60.0,
) -> tuple[str, float]:
    """
    OAuth 2.0 client credentials grant.

    POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
    Body (application/x-www-form-urlencoded): client_id, client_secret, scope, grant_type.

    Returns (access_token, expires_at_unix_epoch).
    """
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    body = urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": scope,
            "grant_type": "client_credentials",
        }
    )
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    with httpx.Client(timeout=timeout) as client:
        r = client.post(token_url, content=body, headers=headers)
    if r.status_code != 200:
        raise DefenderCloudApiError(f"Token request failed: {r.status_code} {r.text[:2000]}")
    data = r.json()
    access = data.get("access_token")
    if not access or not str(access).strip():
        raise DefenderCloudApiError("Token response missing access_token")
    expires_in = data.get("expires_in")
    try:
        sec = float(expires_in) if expires_in is not None else 3600.0
    except (TypeError, ValueError):
        sec = 3600.0
    # Refresh slightly before expiry
    expires_at = time.time() + max(60.0, sec - 120.0)
    return str(access), expires_at


def _arm_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}


def list_assessments(
    subscription_id: str,
    access_token: str,
    *,
    timeout: float = 120.0,
    max_pages: int = 5,
) -> dict[str, Any]:
    """
    GET /subscriptions/{subscriptionId}/providers/Microsoft.Security/assessments

    api-version=2020-01-01 — Microsoft Learn Assessments - List.
    """
    base = (
        f"{ARM_BASE_URL}/subscriptions/{subscription_id}"
        f"/providers/Microsoft.Security/assessments?api-version={API_VERSION_ASSESSMENTS}"
    )
    out: dict[str, Any] = {"value": []}
    url: str | None = base
    pages = 0
    with httpx.Client(timeout=timeout) as client:
        while url and pages < max_pages:
            r = client.get(url, headers=_arm_headers(access_token))
            if r.status_code != 200:
                raise DefenderCloudApiError(f"GET assessments failed: {r.status_code} {r.text[:2000]}")
            chunk = r.json()
            vals = chunk.get("value") or []
            if isinstance(vals, list):
                out["value"].extend(vals)
            next_link = chunk.get("nextLink")
            url = str(next_link) if next_link else None
            pages += 1
    return out


def list_secure_scores(
    subscription_id: str,
    access_token: str,
    *,
    timeout: float = 120.0,
    max_pages: int = 3,
) -> dict[str, Any]:
    """
    GET /subscriptions/{subscriptionId}/providers/Microsoft.Security/secureScores

    api-version=2020-01-01 — Microsoft Learn Secure Scores - List.
    """
    base = (
        f"{ARM_BASE_URL}/subscriptions/{subscription_id}"
        f"/providers/Microsoft.Security/secureScores?api-version={API_VERSION_SECURE_SCORES}"
    )
    out: dict[str, Any] = {"value": []}
    url: str | None = base
    pages = 0
    with httpx.Client(timeout=timeout) as client:
        while url and pages < max_pages:
            r = client.get(url, headers=_arm_headers(access_token))
            if r.status_code != 200:
                raise DefenderCloudApiError(f"GET secureScores failed: {r.status_code} {r.text[:2000]}")
            chunk = r.json()
            vals = chunk.get("value") or []
            if isinstance(vals, list):
                out["value"].extend(vals)
            next_link = chunk.get("nextLink")
            url = str(next_link) if next_link else None
            pages += 1
    return out


def validate_connection(
    tenant_id: str,
    client_id: str,
    client_secret: str,
    subscription_id: str,
) -> None:
    """Obtain token and call secure scores list (single page) as a health check."""
    token, _ = get_client_credentials_token(tenant_id, client_id, client_secret)
    _ = list_secure_scores(subscription_id, token, max_pages=1)
