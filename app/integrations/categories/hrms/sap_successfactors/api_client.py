"""SAP SuccessFactors OData v2 JSON requests."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.integrations.categories.hrms.sap_successfactors.credentials import resolve_odata_base

logger = logging.getLogger("app.integrations.sap_successfactors")


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


def get_json(
    odata_base: str,
    access_token: str,
    entity_path: str,
    *,
    params: dict[str, Any] | None = None,
    max_retries: int = 2,
) -> Any:
    path = entity_path if entity_path.startswith("/") else f"/{entity_path}"
    url = f"{odata_base.rstrip('/')}{path}"
    for attempt in range(max_retries + 1):
        with httpx.Client(timeout=120.0) as client:
            r = client.get(url, headers=_headers(access_token), params=params or {})
            logger.debug("SF OData GET %s -> %s", url, r.status_code)
            if r.status_code == 429 and attempt < max_retries:
                time.sleep(2.0)
                continue
            r.raise_for_status()
            if not (r.text or "").strip():
                return {}
            return r.json()
    return {}


def list_users(cfg: dict[str, Any], access_token: str, *, top: int = 20) -> Any:
    base = resolve_odata_base(cfg)
    return get_json(base, access_token, "/User", params={"$format": "json", "$top": top})


def validate_connection(cfg: dict[str, Any], access_token: str) -> bool:
    try:
        list_users(cfg, access_token, top=1)
        return True
    except httpx.HTTPStatusError:
        return False
