from __future__ import annotations

from typing import Any


def resolve_api_key(cfg: dict[str, Any]) -> str | None:
    for k in ("api_key", "linear_api_key", "access_token"):
        t = cfg.get(k)
        if t and str(t).strip():
            return str(t).strip()
    return None


def has_api_key(cfg: dict[str, Any]) -> bool:
    return bool(resolve_api_key(cfg))
