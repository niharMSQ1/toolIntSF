"""OAuth 2.0 client credentials exchange for Snyk service accounts (short-lived access token)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.integrations.categories.cspm.snyk.regions import resolve_oauth_token_url


class SnykOAuthError(RuntimeError):
    """OAuth token endpoint failed."""


def exchange_client_credentials(
    client_id: str,
    client_secret: str,
    region: str | None,
) -> dict[str, Any]:
    """
    POST application/x-www-form-urlencoded to /oauth2/token (grant_type=client_credentials).

    Returns the JSON body (access_token, expires_in, token_type, ...).
    """
    url = resolve_oauth_token_url(region)
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id.strip(),
        "client_secret": client_secret.strip(),
    }
    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if r.status_code >= 400:
        raise SnykOAuthError(f"Snyk OAuth token error {r.status_code}: {r.text[:2000]}")
    try:
        body = r.json()
    except Exception as e:  # noqa: BLE001
        raise SnykOAuthError(f"Invalid OAuth token response: {e}") from e
    if not isinstance(body, dict) or not body.get("access_token"):
        raise SnykOAuthError("OAuth response missing access_token.")
    return body


def merge_oauth_token_into_config(cfg: dict[str, Any], token_response: dict[str, Any]) -> dict[str, Any]:
    """Persist oauth_access_token and oauth_token_expires_at (UTC ISO) with a small safety margin."""
    new_cfg = dict(cfg)
    new_cfg["oauth_access_token"] = str(token_response["access_token"]).strip()
    exp_in = token_response.get("expires_in")
    try:
        sec = int(exp_in) if exp_in is not None else 3600
    except (TypeError, ValueError):
        sec = 3600
    margin = min(120, max(0, sec // 10))
    until = datetime.now(timezone.utc) + timedelta(seconds=max(60, sec - margin))
    new_cfg["oauth_token_expires_at"] = until.isoformat()
    return new_cfg
