"""
Microsoft Defender for Endpoint REST API (OAuth2 client credentials via Microsoft Entra).

Token: Microsoft documents acquiring an app token with resource ``https://api.securitycenter.microsoft.com``
(legacy v1 endpoint) so the audience matches Defender APIs; some calls use ``https://api.security.microsoft.com``.

References:
- https://learn.microsoft.com/en-us/defender-endpoint/api/api-hello-world
- https://learn.microsoft.com/en-us/defender-endpoint/api/get-machines
- https://learn.microsoft.com/en-us/defender-endpoint/api/get-alerts
- https://learn.microsoft.com/en-us/defender-endpoint/api/get-all-vulnerabilities-by-machines
"""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlencode

import httpx

from app.integrations.categories.endpoint_security.defender_for_endpoint.constants import (
    ALERTS_PATH,
    MACHINES_PATH,
    TOKEN_RESOURCE,
    VULNS_MACHINES_PATH,
)


class DefenderForEndpointApiError(Exception):
    """Non-success HTTP or unexpected Defender API response."""


def _bearer_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token.strip()}",
        "Accept": "application/json",
    }


def _token_url_v1(tenant_id: str) -> str:
    return f"https://login.microsoftonline.com/{tenant_id.strip()}/oauth2/token"


def _token_url_v2(tenant_id: str) -> str:
    return f"https://login.microsoftonline.com/{tenant_id.strip()}/oauth2/v2.0/token"


def get_access_token(
    tenant_id: str,
    client_id: str,
    client_secret: str,
    *,
    timeout: float = 45.0,
    verify_tls: bool = True,
) -> tuple[str, float]:
    """
    OAuth2 client credentials for Defender for Endpoint.

    Tries v2.0 token endpoint with ``scope={TOKEN_RESOURCE}.default``, then legacy v1 ``resource=`` form.
    Returns ``(access_token, expires_at_unix)``.
    """
    v2_body = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": f"{TOKEN_RESOURCE.rstrip('/')}/.default",
    }
    v1_body = {
        "resource": TOKEN_RESOURCE,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    last_err: str | None = None
    for url, body in ((_token_url_v2(tenant_id), v2_body), (_token_url_v1(tenant_id), v1_body)):
        with httpx.Client(timeout=timeout, verify=verify_tls) as client:
            r = client.post(url, content=urlencode(body), headers=headers)
        if r.status_code != 200:
            last_err = f"Token HTTP {r.status_code}: {r.text[:2000]}"
            continue
        try:
            data = r.json()
        except Exception as e:  # noqa: BLE001
            raise DefenderForEndpointApiError(f"Invalid JSON: {e}") from e
        access = data.get("access_token")
        if not access or not str(access).strip():
            raise DefenderForEndpointApiError(str(data)[:2000])
        expires_in = data.get("expires_in")
        try:
            sec = float(expires_in) if expires_in is not None else 3600.0
        except (TypeError, ValueError):
            sec = 3600.0
        expires_at = time.time() + max(60.0, sec - 120.0)
        return str(access).strip(), expires_at
    raise DefenderForEndpointApiError(last_err or "token request failed")


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
                raise DefenderForEndpointApiError(f"Invalid JSON: {e}") from e
        if r.status_code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
            time.sleep(0.5 * (2**attempt))
            last_err = f"HTTP {r.status_code}: {r.text[:500]}"
            continue
        raise DefenderForEndpointApiError(f"GET {url} HTTP {r.status_code}: {r.text[:2000]}")
    raise DefenderForEndpointApiError(last_err or "request failed")


def list_machines(
    api_base_url: str,
    access_token: str,
    *,
    top: int = 50,
    timeout: float = 60.0,
    verify_tls: bool = True,
) -> dict[str, Any]:
    """GET ``/api/machines`` — OData; 404 when no machines (per Microsoft docs)."""
    lim = max(1, min(top, 10000))
    url = f"{api_base_url.rstrip('/')}{MACHINES_PATH}?$top={lim}"
    with httpx.Client(timeout=timeout, verify=verify_tls) as client:
        r = client.get(url, headers=_bearer_headers(access_token))
    if r.status_code == 404:
        return {"value": [], "@odata.context": None, "note": "no machines (404 per API docs)"}
    if r.status_code != 200:
        raise DefenderForEndpointApiError(f"GET machines HTTP {r.status_code}: {r.text[:2000]}")
    try:
        return r.json()
    except Exception as e:  # noqa: BLE001
        raise DefenderForEndpointApiError(f"Invalid JSON: {e}") from e


def list_alerts(
    api_base_url: str,
    access_token: str,
    *,
    top: int = 50,
    timeout: float = 60.0,
    verify_tls: bool = True,
) -> dict[str, Any]:
    """GET ``/api/alerts`` — OData."""
    lim = max(1, min(top, 10000))
    url = f"{api_base_url.rstrip('/')}{ALERTS_PATH}?$top={lim}"
    return _get_json(url, access_token, timeout=timeout, verify_tls=verify_tls)


def list_machine_vulnerabilities(
    api_base_url: str,
    access_token: str,
    *,
    top: int = 50,
    timeout: float = 90.0,
    verify_tls: bool = True,
) -> dict[str, Any]:
    """GET ``/api/vulnerabilities/machinesVulnerabilities`` — OData."""
    lim = max(1, min(top, 10000))
    url = f"{api_base_url.rstrip('/')}{VULNS_MACHINES_PATH}?$top={lim}"
    return _get_json(url, access_token, timeout=timeout, verify_tls=verify_tls)


def validate_credentials(
    tenant_id: str,
    client_id: str,
    client_secret: str,
    api_base_url: str,
    *,
    timeout: float = 45.0,
    verify_tls: bool = True,
) -> None:
    """Obtain token and GET ``/api/machines?$top=1`` (200 or 404 empty per API docs)."""
    token, _ = get_access_token(tenant_id, client_id, client_secret, timeout=timeout, verify_tls=verify_tls)
    list_machines(api_base_url, token, top=1, timeout=timeout, verify_tls=verify_tls)
