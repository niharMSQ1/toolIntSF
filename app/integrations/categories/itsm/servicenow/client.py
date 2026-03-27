"""ServiceNow Table API wrapper."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import httpx


DEFAULT_BASE_URL = "https://dev302959.service-now.com/login.do?user_name=admin&sys_action=sysverb_login&user_password=%246!AB9KUxuwf"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "$6!AB9KUxuwf"


def _auth(configuration_data: dict[str, Any]) -> tuple[str, str] | None:
    username = configuration_data.get("username") or DEFAULT_USERNAME
    password = configuration_data.get("password") or DEFAULT_PASSWORD
    if isinstance(username, str) and username and isinstance(password, str) and password:
        return username, password
    return None


def _normalize_base_url(base_url: str) -> str:
    raw = str(base_url).strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return raw.rstrip("/")


def _table_url(base_url: str, table_name: str) -> str:
    return f"{base_url.rstrip('/')}/api/now/table/{table_name}"


def _fetch_table_records(table_name: str, configuration_data: dict[str, Any]) -> list[dict[str, Any]]:
    base_url = _normalize_base_url(str(configuration_data.get("base_url") or DEFAULT_BASE_URL))
    if not base_url:
        raise ValueError("ServiceNow base_url is required.")

    auth = _auth(configuration_data)
    if auth is None:
        raise ValueError("ServiceNow username and password are required.")

    params = {"sysparm_limit": str(configuration_data.get("sysparm_limit", 100))}
    timeout = float(configuration_data.get("timeout_seconds", 20))
    headers = {"Accept": "application/json"}
    with httpx.Client(timeout=timeout, auth=auth, headers=headers) as client:
        response = client.get(_table_url(base_url, table_name), params=params)
        response.raise_for_status()
        payload = response.json()

    result = payload.get("result")
    if isinstance(result, list):
        return [row for row in result if isinstance(row, dict)]
    return []


def get_incidents(configuration_data: dict[str, Any]) -> list[dict[str, Any]]:
    return _fetch_table_records("incident", configuration_data)


def get_changes(configuration_data: dict[str, Any]) -> list[dict[str, Any]]:
    return _fetch_table_records("change_request", configuration_data)


def get_problems(configuration_data: dict[str, Any]) -> list[dict[str, Any]]:
    return _fetch_table_records("problem", configuration_data)


def get_requests(configuration_data: dict[str, Any]) -> list[dict[str, Any]]:
    return _fetch_table_records("sc_request", configuration_data)


def get_tasks(configuration_data: dict[str, Any]) -> list[dict[str, Any]]:
    return _fetch_table_records("task", configuration_data)


def get_users(configuration_data: dict[str, Any]) -> list[dict[str, Any]]:
    return _fetch_table_records("sys_user", configuration_data)


def get_assets(configuration_data: dict[str, Any]) -> list[dict[str, Any]]:
    return _fetch_table_records("alm_asset", configuration_data)
