from __future__ import annotations

import logging
from typing import Annotated, Any

import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.auth.client import validate_grc_token
from app.auth.schemas import GrcAuthContext
from app.config import Settings, get_settings
from app.database import get_db
from app.models_generated import Organizations
from app.schemas import ToolIntegrationPayload, ToolIntegrationRequestBody

logger = logging.getLogger("app.auth.dependencies")

_http_bearer_optional = HTTPBearer(auto_error=False)


def _configuration_data_keys(configuration_data: dict[str, Any]) -> list[str]:
    return sorted(configuration_data.keys())


def _normalize_org_id_str(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip()
    return s if s else None


def _resolve_org_id_legacy(
    session: Session,
    request: Request,
    body_org_id: str | None,
) -> str:
    """
    When GRC bearer auth is not used: org_id comes from either
    `domain-name` header (Organizations.domain_name -> organizations.id) or
    JSON body `org_id` (legacy).
    """
    # Starlette headers are case-insensitive; use lowercase key.
    domain = (request.headers.get("domain-name") or "").strip()
    if domain:
        row = session.execute(
            select(Organizations.id).where(Organizations.domain_name == domain).limit(1)
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(
                status_code=400,
                detail=f"No organization found for domain_name={domain!r}.",
            )
        return str(row)

    resolved = _normalize_org_id_str(body_org_id)
    if not resolved:
        raise HTTPException(
            status_code=400,
            detail=(
                "org_id is required when domain-name header is not sent (or set "
                "grc_auth_validate_url for bearer-only flow)."
            ),
        )
    return resolved


def verify_grc_token(
    settings: Annotated[Settings, Depends(get_settings)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_http_bearer_optional)],
) -> GrcAuthContext:
    """
    Validates Bearer token against GRC auth when grc_auth_validate_url is set.
    Use on routes that need auth without body merge.
    """
    if not (settings.grc_auth_validate_url or "").strip():
        raise HTTPException(
            status_code=503,
            detail="GRC auth is not configured (grc_auth_validate_url).",
        )
    if credentials is None or not credentials.credentials:
        logger.info("verify_grc_token: missing bearer token")
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization bearer token.")
    logger.info("verify_grc_token: validating bearer token (token not logged)")
    try:
        return validate_grc_token(settings, credentials.credentials)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=401, detail="Token validation failed.") from e
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail="Auth service unavailable.") from e
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


def get_tool_integration_payload(
    request: Request,
    body: ToolIntegrationRequestBody,
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_http_bearer_optional)],
) -> ToolIntegrationPayload:
    """
    When grc_auth_validate_url is set: require Bearer token; org_id comes from GRC auth.
    When unset: org_id from `domain-name` header (lookup organizations.domain_name) or JSON body org_id.
    Optionally enforces body.user_id matches authenticated user when auth is enabled.
    """
    url_configured = bool((settings.grc_auth_validate_url or "").strip())

    logger.info(
        "get_tool_integration_payload: incoming user_id=%s tool_id=%s body_org_id=%s "
        "auth_url_configured=%s bearer_present=%s configuration_data_keys=%s",
        body.user_id,
        body.tool_id,
        body.org_id,
        url_configured,
        bool(credentials and credentials.credentials),
        _configuration_data_keys(body.configuration_data),
    )

    if url_configured:
        if credentials is None or not credentials.credentials:
            logger.info("get_tool_integration_payload: rejected — missing bearer while GRC auth is configured")
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization bearer token.")
        try:
            ctx = validate_grc_token(settings, credentials.credentials)
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=401, detail="Token validation failed.") from None
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Auth service unavailable.") from None
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e)) from e

        if body.user_id != ctx.user_id:
            logger.warning(
                "get_tool_integration_payload: user_id mismatch body=%s auth=%s",
                body.user_id,
                ctx.user_id,
            )
            raise HTTPException(status_code=403, detail="user_id does not match authenticated user.")

        logger.info(
            "get_tool_integration_payload: resolved org_id=%s from GRC auth user_id=%s tool_id=%s",
            ctx.organization_id,
            body.user_id,
            body.tool_id,
        )
        return ToolIntegrationPayload(
            org_id=ctx.organization_id,
            user_id=body.user_id,
            tool_id=body.tool_id,
            configuration_data=body.configuration_data,
        )

    org_id = _resolve_org_id_legacy(session, request, body.org_id)
    logger.info(
        "get_tool_integration_payload: resolved org_id=%s user_id=%s tool_id=%s",
        org_id,
        body.user_id,
        body.tool_id,
    )
    return ToolIntegrationPayload(
        org_id=org_id,
        user_id=body.user_id,
        tool_id=body.tool_id,
        configuration_data=body.configuration_data,
    )
