"""
Aqua CSP self-hosted REST API.

Login matches aquasecurity/terraform-provider-aquasec ``GetCspAuthToken``:
POST ``{base}/api/v1/login`` with JSON ``{"id","password"}``; response ``token``.
Subsequent requests: ``Authorization: Bearer <token>``.

Reference: https://github.com/aquasecurity/terraform-provider-aquasec/blob/main/client/client.go
"""

from __future__ import annotations

from typing import Any

import httpx

from app.integrations.categories.cspm.aqua_security.constants import HOSTS_PATH, IMAGES_PATH, LOGIN_PATH


class AquaSecurityApiError(Exception):
    """Non-success HTTP or unexpected Aqua API response."""


def _bearer_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token.strip()}",
        "Accept": "application/json",
    }


def login_csp(
    api_base_url: str,
    login_id: str,
    password: str,
    *,
    timeout: float = 45.0,
    verify_tls: bool = True,
) -> str:
    url = f"{api_base_url.rstrip('/')}{LOGIN_PATH}"
    body = {"id": login_id, "password": password}
    with httpx.Client(timeout=timeout, verify=verify_tls) as client:
        r = client.post(url, json=body, headers={"Content-Type": "application/json", "Accept": "application/json"})
    if r.status_code != 200:
        raise AquaSecurityApiError(f"Aqua login HTTP {r.status_code}: {r.text[:2000]}")
    try:
        data = r.json()
    except Exception as e:  # noqa: BLE001
        raise AquaSecurityApiError(f"Invalid JSON: {e}") from e
    token = data.get("token")
    if not token or not str(token).strip():
        raise AquaSecurityApiError(str(data)[:2000])
    return str(token).strip()


def validate_credentials(
    api_base_url: str,
    login_id: str,
    password: str,
    *,
    timeout: float = 45.0,
    verify_tls: bool = True,
) -> None:
    token = login_csp(api_base_url, login_id, password, timeout=timeout, verify_tls=verify_tls)
    list_hosts(api_base_url, token, timeout=timeout, verify_tls=verify_tls)


def list_hosts(
    api_base_url: str,
    access_token: str,
    *,
    timeout: float = 60.0,
    verify_tls: bool = True,
) -> dict[str, Any]:
    url = f"{api_base_url.rstrip('/')}{HOSTS_PATH}"
    with httpx.Client(timeout=timeout, verify=verify_tls) as client:
        r = client.get(url, headers=_bearer_headers(access_token))
    if r.status_code != 200:
        raise AquaSecurityApiError(f"Aqua hosts HTTP {r.status_code}: {r.text[:2000]}")
    try:
        return r.json()
    except Exception as e:  # noqa: BLE001
        raise AquaSecurityApiError(f"Invalid JSON: {e}") from e


def list_images(
    api_base_url: str,
    access_token: str,
    *,
    timeout: float = 60.0,
    verify_tls: bool = True,
) -> dict[str, Any]:
    url = f"{api_base_url.rstrip('/')}{IMAGES_PATH}"
    with httpx.Client(timeout=timeout, verify=verify_tls) as client:
        r = client.get(url, headers=_bearer_headers(access_token))
    if r.status_code != 200:
        raise AquaSecurityApiError(f"Aqua images HTTP {r.status_code}: {r.text[:2000]}")
    try:
        return r.json()
    except Exception as e:  # noqa: BLE001
        raise AquaSecurityApiError(f"Invalid JSON: {e}") from e
