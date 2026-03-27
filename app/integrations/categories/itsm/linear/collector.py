"""Collect Linear issue search results per evidence_masters row."""

from __future__ import annotations

import re
from typing import Any

from app.integrations.categories.itsm.linear import api_client
from app.integrations.categories.itsm.linear.credentials import project_ids_list, team_ids_list


_STOPWORDS = frozenset(
    {
        "the",
        "and",
        "for",
        "itsm",
        "tickets",
        "ticket",
        "records",
        "record",
        "management",
        "request",
        "requests",
    }
)


def _keywords_from_evidence_name(name: str, *, max_terms: int = 6) -> list[str]:
    """Derive a search string from the catalog name (before —)."""
    part = name.split("—")[0].strip()
    words = re.split(r"[^\w]+", part)
    out: list[str] = []
    for w in words:
        w = w.strip()
        if len(w) < 3:
            continue
        wl = w.lower()
        if wl in _STOPWORDS:
            continue
        out.append(w)
        if len(out) >= max_terms:
            break
    return out


def build_search_query(master: dict[str, Any], cfg: dict[str, Any]) -> str | None:
    code = str(master.get("code") or "")
    overrides = cfg.get("search_overrides")
    if isinstance(overrides, dict) and code in overrides and str(overrides[code]).strip():
        return str(overrides[code]).strip()

    default_query = cfg.get("default_query")
    if isinstance(default_query, str) and default_query.strip():
        return default_query.strip()

    terms = _keywords_from_evidence_name(str(master.get("name") or ""))
    if not terms:
        return None
    return " ".join(terms)


def collect_for_master(
    master: dict[str, Any],
    cfg: dict[str, Any],
    *,
    access_token: str,
    graphql_url: str,
) -> dict[str, Any]:
    search_query = build_search_query(master, cfg)
    data = api_client.search_issues(
        access_token,
        graphql_url=graphql_url,
        query=search_query,
        team_id=team_ids_list(cfg)[0] if team_ids_list(cfg) else None,
        project_id=project_ids_list(cfg)[0] if project_ids_list(cfg) else None,
        first=50,
    )
    return {
        "evidence_code": master.get("code"),
        "integration": "linear",
        "search_query": search_query,
        "issues": data,
    }


def linear_evidence_for_storage(payload: dict[str, Any]) -> dict[str, Any]:
    return payload
