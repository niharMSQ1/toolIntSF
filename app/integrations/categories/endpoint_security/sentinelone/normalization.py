"""
Map SentinelOne Web API v2.1 JSON into a small internal envelope for GRC evidence.

Typical list responses use a top-level ``data`` array (see SentinelOne API clients and integrator docs).
"""

from __future__ import annotations

from typing import Any


def _data_rows(payload: dict[str, Any]) -> list[Any]:
    d = payload.get("data")
    if isinstance(d, list):
        return d
    return []


def normalize_agents_payload(payload: dict[str, Any]) -> dict[str, Any]:
    rows = _data_rows(payload)
    items: list[dict[str, Any]] = []
    for row in rows[:5000]:
        if not isinstance(row, dict):
            continue
        rid = row.get("id")
        sid = str(rid) if rid is not None else ""
        host = str(row.get("computerName") or row.get("uuid") or sid or "agent")
        items.append(
            {
                "id": sid or host,
                "title": host,
                "kind": "sentinelone_agent",
                "severity": None,
                "timestamp": row.get("lastActiveDate") or row.get("registeredAt"),
                "metadata": {
                    "osType": row.get("osType"),
                    "agentVersion": row.get("agentVersion"),
                    "siteId": row.get("siteId"),
                    "groupId": row.get("groupId"),
                },
            }
        )
    return {
        "vendor": "sentinelone",
        "artifact_type": "agents",
        "item_count": len(items),
        "items": items,
        "pagination": payload.get("pagination") if isinstance(payload.get("pagination"), dict) else {},
    }


def normalize_threats_payload(payload: dict[str, Any]) -> dict[str, Any]:
    rows = _data_rows(payload)
    items: list[dict[str, Any]] = []
    for row in rows[:5000]:
        if not isinstance(row, dict):
            continue
        tid = str(row.get("id") or "")
        title = str(row.get("threatName") or row.get("classification") or tid or "threat")
        items.append(
            {
                "id": tid or title,
                "title": title,
                "kind": "sentinelone_threat",
                "severity": row.get("confidenceLevel") or row.get("threatName"),
                "timestamp": row.get("createdAt") or row.get("updatedAt"),
                "metadata": {
                    "classification": row.get("classification"),
                    "mitigationStatus": row.get("mitigationStatus"),
                    "agentId": row.get("agentId"),
                },
            }
        )
    return {
        "vendor": "sentinelone",
        "artifact_type": "threats",
        "item_count": len(items),
        "items": items,
        "pagination": payload.get("pagination") if isinstance(payload.get("pagination"), dict) else {},
    }


def normalize_installed_applications_payload(payload: dict[str, Any]) -> dict[str, Any]:
    rows = _data_rows(payload)
    items: list[dict[str, Any]] = []
    for row in rows[:5000]:
        if not isinstance(row, dict):
            continue
        rid = str(row.get("id") or "")
        name = str(row.get("name") or row.get("applicationName") or rid or "application")
        items.append(
            {
                "id": rid or name,
                "title": name,
                "kind": "installed_application",
                "severity": row.get("riskLevel") or row.get("vulnerabilityRiskLevel"),
                "timestamp": row.get("installedAt"),
                "metadata": {
                    "version": row.get("version"),
                    "publisher": row.get("publisher"),
                    "agentId": row.get("agentId"),
                },
            }
        )
    return {
        "vendor": "sentinelone",
        "artifact_type": "installed_applications",
        "item_count": len(items),
        "items": items,
        "pagination": payload.get("pagination") if isinstance(payload.get("pagination"), dict) else {},
    }
