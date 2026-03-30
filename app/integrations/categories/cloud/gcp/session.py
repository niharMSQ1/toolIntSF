"""GCP auth/session helpers using service-account JSON."""

from __future__ import annotations

from typing import Any

import httpx
from google.auth.transport.requests import Request
from google.oauth2 import service_account

from app.integrations.categories.cloud.gcp.credentials import resolve_project_id, resolve_service_account_info

_SCOPES = ("https://www.googleapis.com/auth/cloud-platform",)


class GcpAuthError(RuntimeError):
    """GCP auth/validation failed."""


def build_access_token(cfg: dict[str, Any]) -> str:
    info = resolve_service_account_info(cfg)
    if not info:
        raise GcpAuthError("Missing service_account_json in configuration_data.")
    try:
        creds = service_account.Credentials.from_service_account_info(info, scopes=_SCOPES)
        creds.refresh(Request())
    except Exception as e:  # noqa: BLE001
        raise GcpAuthError(f"Failed to build GCP access token: {e}") from e
    tok = creds.token
    if not tok:
        raise GcpAuthError("GCP credentials refresh returned empty token.")
    return str(tok)


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


def validate_gcp_access(cfg: dict[str, Any]) -> dict[str, Any]:
    project_id = resolve_project_id(cfg)
    if not project_id:
        raise GcpAuthError("Missing project_id in configuration_data.")
    token = build_access_token(cfg)
    url = f"https://cloudresourcemanager.googleapis.com/v1/projects/{project_id}"
    try:
        with httpx.Client(timeout=60.0) as client:
            r = client.get(url, headers=_headers(token))
            r.raise_for_status()
            data = r.json()
    except Exception as e:  # noqa: BLE001
        raise GcpAuthError(f"GCP project validation failed: {e}") from e
    if not isinstance(data, dict):
        raise GcpAuthError("Unexpected GCP validation response shape.")
    return {
        "projectId": data.get("projectId"),
        "projectNumber": data.get("projectNumber"),
        "lifecycleState": data.get("lifecycleState"),
    }

