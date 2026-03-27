"""Collect Jira issue search results per evidence_masters row."""

from __future__ import annotations

import re
from typing import Any

from app.integrations.categories.itsm.jira import api_client
from app.integrations.categories.itsm.jira.credentials import project_keys_list


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
    """Derive JQL text ~ terms from the catalog name (before —)."""
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


def build_jql(master: dict[str, Any], cfg: dict[str, Any]) -> str:
    """Build JQL: project scope + optional per-code override + keyword text search."""
    code = str(master.get("code") or "")
    overrides = cfg.get("jql_overrides")
    if isinstance(overrides, dict) and code in overrides and str(overrides[code]).strip():
        return str(overrides[code]).strip()

    default_jql = cfg.get("default_jql")
    if isinstance(default_jql, str) and default_jql.strip():
        return default_jql.strip()

    keys = project_keys_list(cfg)
    if not keys:
        raise ValueError(
            "Set configuration_data.project_keys (e.g. [\"PROJ\"] or \"PROJ,OPS\") "
            "or default_jql / jql_overrides for evidence codes."
        )
    pk = ", ".join(keys)
    base = f"project in ({pk}) AND updated >= -730d"
    terms = _keywords_from_evidence_name(str(master.get("name") or ""))
    if terms:
        ors = " OR ".join(f'text ~ "{t}"' for t in terms)
        return f"{base} AND ({ors}) ORDER BY updated DESC"
    return f"{base} ORDER BY updated DESC"


def collect_for_master(
    master: dict[str, Any],
    cfg: dict[str, Any],
    *,
    cloud_id: str,
    access_token: str,
) -> dict[str, Any]:
    jql = build_jql(master, cfg)
    data = api_client.search_issues(cloud_id, access_token, jql)
    return {
        "evidence_code": master.get("code"),
        "integration": "jira_cloud",
        "jql": jql,
        "search": data,
    }


def jira_evidence_for_storage(payload: dict[str, Any]) -> dict[str, Any]:
    return payload
