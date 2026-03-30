from __future__ import annotations

import logging

import httpx

from app.auth.schemas import GrcAuthContext, GrcAuthValidateResponse
from app.config import Settings

logger = logging.getLogger("app.auth.client")


def validate_grc_token(settings: Settings, bearer_token: str) -> GrcAuthContext:
    """
    Call GRC auth validate URL with Authorization: Bearer <token>.
    Expects JSON with success=true and data.user.organization_id.
    """
    url = (settings.grc_auth_validate_url or "").strip()
    if not url:
        raise ValueError("grc_auth_validate_url is not configured")

    headers = {"Authorization": f"Bearer {bearer_token.strip()}", "Accept": "application/json"}
    timeout = settings.grc_auth_validate_timeout_seconds

    logger.info("GRC auth validate: GET %s (bearer token not logged)", url)

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.get(url, headers=headers)
    except httpx.RequestError as e:
        logger.warning("GRC auth request failed: %s", e)
        raise

    if resp.status_code != 200:
        logger.warning("GRC auth HTTP %s: %s", resp.status_code, resp.text[:500])
        raise httpx.HTTPStatusError("GRC auth validation failed", request=resp.request, response=resp)

    try:
        parsed = GrcAuthValidateResponse.model_validate(resp.json())
    except Exception as e:
        logger.warning("GRC auth invalid JSON: %s", e)
        raise ValueError("Invalid GRC auth response") from e

    if not parsed.success or not parsed.data or not parsed.data.user:
        raise ValueError(parsed.message or "GRC auth rejected")

    org_id = parsed.data.user.organization_id
    if not org_id:
        raise ValueError("GRC auth response missing data.user.organization_id")

    uid = str(parsed.data.user.id)
    oid = str(org_id)
    logger.info(
        "GRC auth validate: success message=%s resolved user.id=%s user.organization_id=%s",
        parsed.message,
        uid,
        oid,
    )
    return GrcAuthContext(organization_id=oid, user_id=uid)
