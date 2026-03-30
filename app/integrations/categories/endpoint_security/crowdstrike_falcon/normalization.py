"""
Map CrowdStrike Falcon API JSON into a small internal envelope for GRC evidence.

This is not a full vendor schema— it provides stable keys for reporting and control mapping.
"""

from __future__ import annotations

from typing import Any


def _resources_list(data: dict[str, Any]) -> list[Any]:
    res = data.get("resources")
    if isinstance(res, list):
        return res
    return []


def normalize_host_query_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Host ID query (QueryDevices) — ``resources`` are device IDs (strings)."""
    ids = _resources_list(data)
    items: list[dict[str, Any]] = []
    for rid in ids[:5000]:
        sid = str(rid)
        items.append(
            {
                "id": sid,
                "title": f"device:{sid}",
                "kind": "host_device_id",
                "severity": None,
                "timestamp": None,
            }
        )
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    return {
        "vendor": "crowdstrike_falcon",
        "artifact_type": "host_inventory",
        "item_count": len(items),
        "items": items,
        "pagination": {"query_params": meta.get("query_params"), "pagination": meta.get("pagination")},
    }


def normalize_detects_query_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Detection ID query — ``resources`` are detection IDs."""
    ids = _resources_list(data)
    items: list[dict[str, Any]] = []
    for rid in ids[:5000]:
        sid = str(rid)
        items.append(
            {
                "id": sid,
                "title": f"detection:{sid}",
                "kind": "detection_id",
                "severity": None,
                "timestamp": None,
            }
        )
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    return {
        "vendor": "crowdstrike_falcon",
        "artifact_type": "detections",
        "item_count": len(items),
        "items": items,
        "pagination": {"query_params": meta.get("query_params"), "pagination": meta.get("pagination")},
    }


def normalize_spotlight_combined_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Spotlight combined vulnerabilities — ``resources`` are vulnerability objects (see API docs)."""
    resources = _resources_list(data)
    items: list[dict[str, Any]] = []
    for row in resources[:5000]:
        if not isinstance(row, dict):
            continue
        vid = str(row.get("id") or row.get("vulnerability_id") or row.get("cve", {}).get("id") or "")
        items.append(
            {
                "id": vid or "unknown",
                "title": str(row.get("cve", {}).get("id") or vid or "vulnerability"),
                "kind": "spotlight_vulnerability",
                "severity": row.get("severity") or row.get("cve", {}).get("severity"),
                "timestamp": row.get("updated_timestamp") or row.get("created_timestamp"),
                "metadata": {k: row[k] for k in list(row.keys())[:40]},
            }
        )
    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    return {
        "vendor": "crowdstrike_falcon",
        "artifact_type": "vulnerabilities",
        "item_count": len(items),
        "items": items,
        "pagination": {"pagination": meta.get("pagination")},
    }
