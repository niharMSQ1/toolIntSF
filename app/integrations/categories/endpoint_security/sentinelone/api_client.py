"""
SentinelOne Management Console Web API v2.1 (API token).

Authentication: ``Authorization: ApiToken <token>`` (see SentinelOne console: Settings → Users → API token).

References (vendor / community mirrors of the public API surface):
- https://celerium.github.io/SentinelOne-PowerShellWrapper/ — URIs such as ``/agents``, ``/threats``.
- Application inventory: ``GET .../installed-applications`` (Application Risk; SKU / feature requirements may apply).
"""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlencode

import httpx

from app.integrations.categories.endpoint_security.sentinelone.constants import (
    AGENTS_PATH,
    INSTALLED_APPLICATIONS_PATH,
    THREATS_PATH,
)


class SentinelOneApiError(Exception):
    """Non-success HTTP or unexpected SentinelOne API response."""


def _api_token_headers(api_token: str) -> dict[str, str]:
    return {
        "Authorization": f"ApiToken {api_token.strip()}",
        "Accept": "application/json",
    }


def _get_json(
    url: str,
    api_token: str,
    *,
    timeout: float = 60.0,
    verify_tls: bool = True,
    max_retries: int = 3,
) -> dict[str, Any]:
    last_err: str | None = None
    for attempt in range(max_retries):
        with httpx.Client(timeout=timeout, verify=verify_tls) as client:
            r = client.get(url, headers=_api_token_headers(api_token))
        if r.status_code == 200:
            try:
                return r.json()
            except Exception as e:  # noqa: BLE001
                raise SentinelOneApiError(f"Invalid JSON: {e}") from e
        if r.status_code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
            time.sleep(0.5 * (2**attempt))
            last_err = f"HTTP {r.status_code}: {r.text[:500]}"
            continue
        raise SentinelOneApiError(f"GET {url} HTTP {r.status_code}: {r.text[:2000]}")
    raise SentinelOneApiError(last_err or "request failed")


def _list_paged(
    api_root: str,
    path: str,
    api_token: str,
    *,
    limit: int,
    timeout: float,
    verify_tls: bool,
) -> dict[str, Any]:
    lim = max(1, min(limit, 1000))
    q = urlencode({"limit": lim})
    url = f"{api_root.rstrip('/')}{path}?{q}"
    return _get_json(url, api_token, timeout=timeout, verify_tls=verify_tls)


def list_agents(
    api_root: str,
    api_token: str,
    *,
    limit: int = 50,
    timeout: float = 60.0,
    verify_tls: bool = True,
) -> dict[str, Any]:
    """GET ``/agents`` — agent inventory (see SentinelOne Web API v2.1)."""
    return _list_paged(api_root, AGENTS_PATH, api_token, limit=limit, timeout=timeout, verify_tls=verify_tls)


def list_threats(
    api_root: str,
    api_token: str,
    *,
    limit: int = 50,
    timeout: float = 60.0,
    verify_tls: bool = True,
) -> dict[str, Any]:
    """GET ``/threats`` — threat events."""
    return _list_paged(api_root, THREATS_PATH, api_token, limit=limit, timeout=timeout, verify_tls=verify_tls)


def list_installed_applications(
    api_root: str,
    api_token: str,
    *,
    limit: int = 50,
    timeout: float = 90.0,
    verify_tls: bool = True,
) -> dict[str, Any]:
    """GET ``/installed-applications`` — application risk / inventory (feature/SKU may be required)."""
    return _list_paged(
        api_root, INSTALLED_APPLICATIONS_PATH, api_token, limit=limit, timeout=timeout, verify_tls=verify_tls
    )


def validate_credentials(api_root: str, api_token: str, *, timeout: float = 45.0, verify_tls: bool = True) -> None:
    """GET ``/agents?limit=1`` to verify token and connectivity."""
    list_agents(api_root, api_token, limit=1, timeout=timeout, verify_tls=verify_tls)
