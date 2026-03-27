"""Bitbucket Cloud workspace listing (after OAuth)."""

from __future__ import annotations

from typing import Any

import httpx

from app.integrations.categories.devtools.bitbucket.constants import BITBUCKET_API_BASE


def fetch_workspaces_for_token(access_token: str, *, page_len: int = 100) -> list[dict[str, Any]]:
    """
    Return workspace summaries: ``{"uuid", "slug", "name"}`` per workspace the user may access.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    out: list[dict[str, Any]] = []
    url: str | None = f"{BITBUCKET_API_BASE}/workspaces?role=member&pagelen={page_len}"
    with httpx.Client(timeout=60.0) as client:
        while url:
            r = client.get(url, headers=headers)
            r.raise_for_status()
            payload = r.json()
            for w in payload.get("values") or []:
                if not isinstance(w, dict):
                    continue
                out.append(
                    {
                        "uuid": str(w.get("uuid", "")),
                        "slug": str(w.get("slug", "")),
                        "name": str(w.get("name", "") or w.get("slug", "")),
                    }
                )
            url = None
            next_link = payload.get("next")
            if isinstance(next_link, str) and next_link.strip():
                url = next_link.strip()
    return out
