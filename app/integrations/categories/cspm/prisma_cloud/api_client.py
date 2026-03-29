"""
Prisma Cloud CSPM REST API (documented on pan.dev).

Auth: POST /login with JSON username (access key id) + password (secret key) → JWT.
Requests: header x-redlock-auth: <JWT>.
Session: GET /auth_token/extend with existing JWT (documented refresh path).
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.integrations.categories.cspm.prisma_cloud.constants import JWT_TTL_SECONDS


class PrismaCloudApiError(Exception):
    """Non-success HTTP or malformed response from Prisma Cloud API."""


def _url(base: str, path: str) -> str:
    return f"{base.rstrip('/')}/{path.lstrip('/')}"


def login(base_url: str, access_key_id: str, secret_key: str, *, timeout: float = 60.0) -> str:
    """
    POST /login — returns JWT for x-redlock-auth.

    Documented: https://pan.dev/prisma-cloud/api/cspm/app-login/
    """
    url = _url(base_url, "login")
    payload = {"username": access_key_id, "password": secret_key}
    with httpx.Client(timeout=timeout) as client:
        r = client.post(url, json=payload, headers={"Content-Type": "application/json"})
    if r.status_code != 200:
        raise PrismaCloudApiError(f"POST /login failed: {r.status_code} {r.text[:2000]}")
    data = r.json()
    token = data.get("token")
    if not token or not str(token).strip():
        raise PrismaCloudApiError("POST /login response missing token")
    return str(token)


def extend_session(base_url: str, jwt: str, *, timeout: float = 60.0) -> str:
    """
    GET /auth_token/extend — refresh JWT (requires valid session token).

    Documented: https://pan.dev/prisma-cloud/api/cspm/extend-session/
    """
    url = _url(base_url, "auth_token/extend")
    headers = {"x-redlock-auth": jwt, "Content-Type": "application/json"}
    with httpx.Client(timeout=timeout) as client:
        r = client.get(url, headers=headers)
    if r.status_code != 200:
        raise PrismaCloudApiError(f"GET /auth_token/extend failed: {r.status_code} {r.text[:2000]}")
    data = r.json()
    token = data.get("token")
    if not token or not str(token).strip():
        raise PrismaCloudApiError("GET /auth_token/extend response missing token")
    return str(token)


def _auth_headers(jwt: str) -> dict[str, str]:
    return {"x-redlock-auth": jwt, "Content-Type": "application/json"}


def get_cloud_accounts(base_url: str, jwt: str, *, timeout: float = 120.0) -> dict[str, Any]:
    """
    GET /cloud — onboarded cloud accounts summary.

    Documented: https://pan.dev/prisma-cloud/api/cspm/get-cloud-accounts/
    """
    url = _url(base_url, "cloud")
    with httpx.Client(timeout=timeout) as client:
        r = client.get(url, headers=_auth_headers(jwt))
    if r.status_code != 200:
        raise PrismaCloudApiError(f"GET /cloud failed: {r.status_code} {r.text[:2000]}")
    return r.json()


def get_alerts_v2(
    base_url: str,
    jwt: str,
    *,
    timeout: float = 120.0,
) -> dict[str, Any]:
    """
    GET /v2/alert — paginated alerts.

    Documented rate limits: 2/sec sustained, 10/sec burst (pan.dev).
    https://pan.dev/prisma-cloud/api/cspm/get-alerts-v-2/
    """
    url = _url(base_url, "v2/alert")
    with httpx.Client(timeout=timeout) as client:
        r = client.get(url, headers=_auth_headers(jwt))
    if r.status_code == 429:
        time.sleep(1.0)
        with httpx.Client(timeout=timeout) as client2:
            r = client2.get(url, headers=_auth_headers(jwt))
    if r.status_code != 200:
        raise PrismaCloudApiError(f"GET /v2/alert failed: {r.status_code} {r.text[:2000]}")
    return r.json()


def get_compliance_posture_v2(base_url: str, jwt: str, *, timeout: float = 120.0) -> dict[str, Any]:
    """
    GET /v2/compliance/posture — compliance statistics breakdown.

    Documented: https://pan.dev/prisma-cloud/api/cspm/get-compliance-posture-v-2/
    """
    url = _url(base_url, "v2/compliance/posture")
    with httpx.Client(timeout=timeout) as client:
        r = client.get(url, headers=_auth_headers(jwt))
    if r.status_code != 200:
        raise PrismaCloudApiError(f"GET /v2/compliance/posture failed: {r.status_code} {r.text[:2000]}")
    return r.json()


def validate_connection(base_url: str, access_key_id: str, secret_key: str) -> None:
    """Login once to verify credentials."""
    login(base_url, access_key_id, secret_key)


def jwt_needs_refresh(obtained_at_epoch: float | None) -> bool:
    if obtained_at_epoch is None:
        return True
    return (time.time() - obtained_at_epoch) > (JWT_TTL_SECONDS - 60)
