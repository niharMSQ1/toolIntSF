"""Shared helpers for HRMS configure routers (masking, ToolIntegrationResponse)."""

from __future__ import annotations

from typing import Any

from app.schemas import ToolIntegrationResponse


def mask_configuration_data(cfg: dict[str, Any], secret_keys: tuple[str, ...]) -> dict[str, Any]:
    masked = dict(cfg)
    for k in secret_keys:
        if k in masked and masked[k]:
            masked[k] = "***"
    return masked


def tool_integration_response(
    row: dict[str, Any],
    *,
    configuration_data: dict | None = None,
) -> ToolIntegrationResponse:
    return ToolIntegrationResponse(
        id=str(row["id"]),
        organization_id=str(row["organization_id"]),
        tool_id=str(row["tool_id"]),
        configuration_data=configuration_data if configuration_data is not None else row["configuration_data"],
    )


DEFAULT_SECRET_KEYS = (
    "access_token",
    "refresh_token",
    "client_secret",
    "api_key",
    "api_secret",
    "bamboohr_api_key",
    "rippling_api_key",
    "paycom_client_secret",
    "webhook_secret",
)
