from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.integrations.categories.idp.forgerock.credentials import resolve_api_base, resolve_users_path

logger = logging.getLogger("app.integrations.forgerock")


def _headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}


def get_json(api_base: str, access_token: str, path: str, *, params: dict[str, Any] | None = None) -> Any:
    p = path if path.startswith("/") else f"/{path}"
    url = f"{api_base.rstrip('/')}{p}"
    for attempt in range(3):
        with httpx.Client(timeout=120.0) as client:
            r = client.get(url, headers=_headers(access_token), params=params or {})
            logger.debug("ForgeRock GET %s -> %s", url, r.status_code)
            if r.status_code == 429 and attempt < 2:
                time.sleep(2.0)
                continue
            r.raise_for_status()
            if not r.content:
                return {}
            return r.json()
    return {}


def list_users(cfg: dict[str, Any], access_token: str) -> Any:
    base = resolve_api_base(cfg)
    path = resolve_users_path(cfg)
    if "?" in path:
        path_part, qs = path.split("?", 1)
        from urllib.parse import parse_qs

        q = {k: v[0] for k, v in parse_qs(qs).items()}
        return get_json(base, access_token, path_part, params=q)
    return get_json(base, access_token, path)


def validate_connection(cfg: dict[str, Any], access_token: str) -> bool:
    try:
        list_users(cfg, access_token)
        return True
    except httpx.HTTPStatusError:
        return False
