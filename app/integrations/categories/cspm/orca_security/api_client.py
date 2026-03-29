"""
Orca Security HTTP API.

Authentication and alert query path are implemented to match the public
Cortex XSOAR / Demisto **Orca** integration (`Authorization: Token <api_token>`,
POST `/automations/query/alerts`). See:
https://github.com/demisto/content/blob/master/Packs/Orca/Integrations/Orca/Orca.py

Regional API hosts are described in third-party connector docs (e.g. Brinqa) and Orca product docs;
default host `api.orcasecurity.io`.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.integrations.categories.cspm.orca_security.constants import QUERY_ALERTS_PATH


class OrcaSecurityApiError(Exception):
    """Non-success HTTP or unexpected Orca API response."""


def _headers(api_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Token {api_token}",
        "Content-Type": "application/json",
    }


def validate_api_token(api_base_url: str, api_token: str, *, timeout: float = 45.0) -> None:
    """
    POST .../automations/query/alerts with body ``{"limit": 1}`` — same as Demisto ``validate_api_key``.
    Expects JSON with ``status`` == ``success`` on success.
    """
    url = f"{api_base_url.rstrip('/')}{QUERY_ALERTS_PATH}"
    with httpx.Client(timeout=timeout) as client:
        r = client.post(url, headers=_headers(api_token), json={"limit": 1})
    if r.status_code != 200:
        raise OrcaSecurityApiError(f"Orca API HTTP {r.status_code}: {r.text[:2000]}")
    try:
        data = r.json()
    except Exception as e:  # noqa: BLE001
        raise OrcaSecurityApiError(f"Invalid JSON: {e}") from e
    if data.get("status") != "success":
        raise OrcaSecurityApiError(str(data.get("error") or data)[:2000])


def query_alerts(
    api_base_url: str,
    api_token: str,
    *,
    limit: int = 100,
    page: int = 1,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """
    POST .../automations/query/alerts — list alerts (Demisto ``get_alerts``).

    Body fields per Orca.py: ``limit``, ``page``, optional ``from_date`` for incremental fetch.
    """
    url = f"{api_base_url.rstrip('/')}{QUERY_ALERTS_PATH}"
    body: dict[str, Any] = {"limit": max(1, min(limit, 500)), "page": max(1, page)}
    with httpx.Client(timeout=timeout) as client:
        r = client.post(url, headers=_headers(api_token), json=body)
    if r.status_code != 200:
        raise OrcaSecurityApiError(f"Orca API HTTP {r.status_code}: {r.text[:2000]}")
    try:
        return r.json()
    except Exception as e:  # noqa: BLE001
        raise OrcaSecurityApiError(f"Invalid JSON: {e}") from e
