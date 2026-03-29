"""
CrowdStrike Falcon REST API (OAuth2 client credentials).

Token endpoint and routes follow the published OpenAPI / FalconPy service collections:
- ``POST {base}/oauth2/token`` — ``oauth2AccessToken`` (form ``application/x-www-form-urlencoded``)
- ``GET {base}/devices/queries/devices/v1`` — host ID search (QueryDevices)
- ``GET {base}/detects/queries/detects/v1`` — detection ID search (QueryDetects)
- ``GET {base}/spotlight/combined/vulnerabilities/v1`` — Spotlight combined (filter required)

References:
- https://developer.crowdstrike.com/docs/openapi
- https://www.falconpy.io/Service-Collections/OAuth2.html
- https://www.falconpy.io/Service-Collections/Spotlight-Vulnerabilities.html
"""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlencode

import httpx

from app.integrations.categories.endpoint_security.crowdstrike_falcon.constants import (
    DETECTS_QUERY_PATH,
    DEVICES_QUERY_PATH,
    OAUTH2_TOKEN_PATH,
    SPOTLIGHT_COMBINED_VULNS_PATH,
)


class CrowdStrikeFalconApiError(Exception):
    """Non-success HTTP or unexpected Falcon API response."""


def _bearer_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token.strip()}",
        "Accept": "application/json",
    }


def get_access_token(
    api_base_url: str,
    client_id: str,
    client_secret: str,
    *,
    member_cid: str | None = None,
    timeout: float = 45.0,
    verify_tls: bool = True,
) -> tuple[str, float]:
    """
    OAuth2 access token (client credentials).

    POST ``/oauth2/token`` with form fields per Falcon OAuth2 API.
    Returns ``(access_token, expires_at_unix)``.
    """
    url = f"{api_base_url.rstrip('/')}{OAUTH2_TOKEN_PATH}"
    base_body: dict[str, str] = {
        "client_id": client_id,
        "client_secret": client_secret,
    }
    if member_cid:
        base_body["member_cid"] = member_cid
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    with httpx.Client(timeout=timeout, verify=verify_tls) as client:
        r = client.post(url, content=urlencode({**base_body, "grant_type": "client_credentials"}), headers=headers)
    if r.status_code != 200:
        with httpx.Client(timeout=timeout, verify=verify_tls) as client:
            r = client.post(url, content=urlencode(base_body), headers=headers)
    if r.status_code != 200:
        raise CrowdStrikeFalconApiError(f"Token HTTP {r.status_code}: {r.text[:2000]}")
    try:
        data = r.json()
    except Exception as e:  # noqa: BLE001
        raise CrowdStrikeFalconApiError(f"Invalid JSON: {e}") from e
    access = data.get("access_token")
    if not access or not str(access).strip():
        raise CrowdStrikeFalconApiError(str(data)[:2000])
    expires_in = data.get("expires_in")
    try:
        sec = float(expires_in) if expires_in is not None else 1800.0
    except (TypeError, ValueError):
        sec = 1800.0
    expires_at = time.time() + max(60.0, sec - 120.0)
    return str(access).strip(), expires_at


def _get_json(
    url: str,
    access_token: str,
    *,
    timeout: float = 60.0,
    verify_tls: bool = True,
    max_retries: int = 3,
) -> dict[str, Any]:
    last_err: str | None = None
    for attempt in range(max_retries):
        with httpx.Client(timeout=timeout, verify=verify_tls) as client:
            r = client.get(url, headers=_bearer_headers(access_token))
        if r.status_code == 200:
            try:
                return r.json()
            except Exception as e:  # noqa: BLE001
                raise CrowdStrikeFalconApiError(f"Invalid JSON: {e}") from e
        if r.status_code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
            time.sleep(0.5 * (2**attempt))
            last_err = f"HTTP {r.status_code}: {r.text[:500]}"
            continue
        raise CrowdStrikeFalconApiError(f"GET {url} HTTP {r.status_code}: {r.text[:2000]}")
    raise CrowdStrikeFalconApiError(last_err or "request failed")


def query_devices(
    api_base_url: str,
    access_token: str,
    *,
    limit: int = 25,
    timeout: float = 60.0,
    verify_tls: bool = True,
) -> dict[str, Any]:
    """GET ``/devices/queries/devices/v1`` — returns ``resources`` (device IDs) per Falcon API."""
    lim = max(1, min(limit, 5000))
    url = f"{api_base_url.rstrip('/')}{DEVICES_QUERY_PATH}?limit={lim}"
    return _get_json(url, access_token, timeout=timeout, verify_tls=verify_tls)


def query_detects(
    api_base_url: str,
    access_token: str,
    *,
    limit: int = 25,
    timeout: float = 60.0,
    verify_tls: bool = True,
) -> dict[str, Any]:
    """GET ``/detects/queries/detects/v1`` — returns detection IDs (``resources``)."""
    lim = max(1, min(limit, 5000))
    url = f"{api_base_url.rstrip('/')}{DETECTS_QUERY_PATH}?limit={lim}"
    return _get_json(url, access_token, timeout=timeout, verify_tls=verify_tls)


def query_spotlight_combined_vulnerabilities(
    api_base_url: str,
    access_token: str,
    *,
    filter_fql: str,
    limit: int = 25,
    timeout: float = 90.0,
    verify_tls: bool = True,
) -> dict[str, Any]:
    """
    GET ``/spotlight/combined/vulnerabilities/v1``.

    ``filter`` is required (FQL). Example: ``status:'open'`` (see Spotlight API docs).
    """
    lim = max(1, min(limit, 5000))
    url = f"{api_base_url.rstrip('/')}{SPOTLIGHT_COMBINED_VULNS_PATH}"
    with httpx.Client(timeout=timeout, verify=verify_tls) as client:
        r = client.get(
            url,
            headers=_bearer_headers(access_token),
            params={"limit": lim, "filter": filter_fql},
        )
    if r.status_code != 200:
        raise CrowdStrikeFalconApiError(f"Spotlight HTTP {r.status_code}: {r.text[:2000]}")
    try:
        return r.json()
    except Exception as e:  # noqa: BLE001
        raise CrowdStrikeFalconApiError(f"Invalid JSON: {e}") from e


def validate_credentials(
    api_base_url: str,
    client_id: str,
    client_secret: str,
    *,
    member_cid: str | None = None,
    timeout: float = 45.0,
    verify_tls: bool = True,
) -> None:
    """Obtain token and perform a minimal host query (limit=1)."""
    token, _ = get_access_token(
        api_base_url, client_id, client_secret, member_cid=member_cid, timeout=timeout, verify_tls=verify_tls
    )
    query_devices(api_base_url, token, limit=1, timeout=timeout, verify_tls=verify_tls)
