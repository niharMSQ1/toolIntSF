from __future__ import annotations

from typing import Any


def resolve_token(cfg: dict[str, Any]) -> str | None:
    for k in ("api_token", "smartsheet_access_token", "access_token"):
        t = cfg.get(k)
        if t and str(t).strip():
            return str(t).strip()
    return None


def has_token(cfg: dict[str, Any]) -> bool:
    return bool(resolve_token(cfg))
