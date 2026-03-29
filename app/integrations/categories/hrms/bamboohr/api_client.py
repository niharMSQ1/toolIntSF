"""Minimal BambooHR API client.

This is the second core file in the workflow.

Why this file comes right after ``credentials.py``:
- ``credentials.py`` answers "how do we authenticate?"
- ``api_client.py`` answers "how do we actually call BambooHR?"

We keep this layer small and focused:
- build the correct BambooHR base URL
- choose the right auth header based on auth mode
- make HTTP requests
- return parsed JSON to higher layers

Higher layers like services/collectors should not build headers or URLs themselves.
That separation keeps the architecture clean.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.integrations.categories.hrms.bamboohr.credentials import (
    AUTH_MODE_API_KEY,
    resolve_access_token,
    resolve_api_key,
    resolve_auth_mode,
    resolve_subdomain,
)


def bamboohr_base_url(subdomain: str) -> str:
    """Return the BambooHR tenant base URL.

    Example:
    - subdomain ``acme`` becomes ``https://api.bamboohr.com/api/gateway.php/acme/v1``

    Why this exists:
    - BambooHR is tenant-scoped, so the company subdomain is part of every API URL
    - we do not want URL-building duplicated throughout the integration
    """
    s = str(subdomain).strip()
    return f"https://api.bamboohr.com/api/gateway.php/{s}/v1"


def _build_auth_headers(cfg: dict[str, Any]) -> dict[str, str]:
    """Return BambooHR auth headers for the configured auth mode.

    API key mode:
    - BambooHR commonly uses Basic auth where the API key is the username and
      a placeholder value like ``x`` is used as the password.

    App/OAuth mode:
    - use a Bearer token in the Authorization header
    """
    mode = resolve_auth_mode(cfg)

    if mode == AUTH_MODE_API_KEY:
        api_key = resolve_api_key(cfg)
        if not api_key:
            raise ValueError("Missing BambooHR api_key for API key authentication.")
        return {"Accept": "application/json"}

    access_token = resolve_access_token(cfg)
    if not access_token:
        raise ValueError("Missing BambooHR access_token for app OAuth authentication.")
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }


def _build_basic_auth(cfg: dict[str, Any]) -> tuple[str, str] | None:
    """Return httpx Basic auth tuple when API key auth is active."""
    mode = resolve_auth_mode(cfg)
    if mode != AUTH_MODE_API_KEY:
        return None
    api_key = resolve_api_key(cfg)
    if not api_key:
        raise ValueError("Missing BambooHR api_key for API key authentication.")
    return (api_key, "x")


def _get(
    cfg: dict[str, Any],
    path: str,
    *,
    params: dict[str, Any] | None = None,
    timeout: float = 60.0,
) -> Any:
    """Generic GET helper used by BambooHR read operations."""
    base = bamboohr_base_url(resolve_subdomain(cfg))
    url = f"{base.rstrip('/')}/{path.lstrip('/')}"
    headers = _build_auth_headers(cfg)
    auth = _build_basic_auth(cfg)

    with httpx.Client(timeout=timeout, auth=auth) as client:
        response = client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()


def list_employees_directory(cfg: dict[str, Any]) -> Any:
    """Fetch the BambooHR employee directory.

    Why start with this endpoint:
    - employee directory data is central to most HRMS evidence use cases
    - it is a natural first proof that both auth modes work
    - later evidence collectors will likely build on this dataset
    """
    return _get(cfg, "/employees/directory")


def get_employee(cfg: dict[str, Any], employee_id: str, fields: list[str] | None = None) -> Any:
    """Fetch a single employee record from BambooHR.

    ``fields`` lets higher layers request only the columns they need.
    """
    params: dict[str, Any] | None = None
    if fields:
        params = {"fields": ",".join(fields)}
    return _get(cfg, f"/employees/{employee_id}", params=params)
