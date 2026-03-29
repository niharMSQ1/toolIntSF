"""
Sysdig Secure / Monitor HTTP API (SaaS regional or on-prem).

Authentication matches sysdig-sdk-python ``_SdcCommon``:
``Authorization: Bearer <token>``.

Reference: https://github.com/sysdiglabs/sysdig-sdk-python/blob/master/sdcclient/_common.py
Sysdig docs: https://docs.sysdig.com/en/developer-tools/sysdig-api/
"""

from __future__ import annotations

from typing import Any

import httpx

from app.integrations.categories.cspm.sysdig_secure.constants import AGENTS_CONNECTED_PATH, USER_ME_PATH


class SysdigSecureApiError(Exception):
    """Non-success HTTP or unexpected Sysdig API response."""


def _bearer_headers(api_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_token.strip()}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def get_user_me(
    api_base_url: str,
    api_token: str,
    *,
    timeout: float = 45.0,
    verify_tls: bool = True,
) -> dict[str, Any]:
    url = f"{api_base_url.rstrip('/')}{USER_ME_PATH}"
    with httpx.Client(timeout=timeout, verify=verify_tls) as client:
        r = client.get(url, headers=_bearer_headers(api_token))
    if r.status_code != 200:
        raise SysdigSecureApiError(f"Sysdig GET /api/user/me HTTP {r.status_code}: {r.text[:2000]}")
    try:
        return r.json()
    except Exception as e:  # noqa: BLE001
        raise SysdigSecureApiError(f"Invalid JSON: {e}") from e


def get_agents_connected(
    api_base_url: str,
    api_token: str,
    *,
    timeout: float = 60.0,
    verify_tls: bool = True,
) -> dict[str, Any]:
    url = f"{api_base_url.rstrip('/')}{AGENTS_CONNECTED_PATH}"
    with httpx.Client(timeout=timeout, verify=verify_tls) as client:
        r = client.get(url, headers=_bearer_headers(api_token))
    if r.status_code != 200:
        raise SysdigSecureApiError(f"Sysdig GET /api/agents/connected HTTP {r.status_code}: {r.text[:2000]}")
    try:
        return r.json()
    except Exception as e:  # noqa: BLE001
        raise SysdigSecureApiError(f"Invalid JSON: {e}") from e


def validate_api_token(
    api_base_url: str,
    api_token: str,
    *,
    timeout: float = 45.0,
    verify_tls: bool = True,
) -> None:
    """GET /api/user/me — same family as sysdig-sdk-python ``get_user_info``."""
    get_user_me(api_base_url, api_token, timeout=timeout, verify_tls=verify_tls)
