"""
Map Microsoft Defender for Endpoint OData JSON into a small internal envelope for GRC evidence.
"""

from __future__ import annotations

from typing import Any


def _odata_value(data: dict[str, Any]) -> list[Any]:
    v = data.get("value")
    if isinstance(v, list):
        return v
    return []


def normalize_machines_payload(data: dict[str, Any]) -> dict[str, Any]:
    """``GET /api/machines`` — ``value`` is a list of machine objects."""
    rows = _odata_value(data)
    items: list[dict[str, Any]] = []
    for row in rows[:5000]:
        if not isinstance(row, dict):
            continue
        mid = str(row.get("id") or "")
        dns = str(row.get("computerDnsName") or mid or "machine")
        items.append(
            {
                "id": mid or dns,
                "title": dns,
                "kind": "endpoint_machine",
                "severity": row.get("riskScore"),
                "timestamp": row.get("lastSeen") or row.get("firstSeen"),
                "metadata": {
                    "osPlatform": row.get("osPlatform"),
                    "healthStatus": row.get("healthStatus"),
                    "exposureLevel": row.get("exposureLevel"),
                },
            }
        )
    return {
        "vendor": "defender_for_endpoint",
        "artifact_type": "machines",
        "item_count": len(items),
        "items": items,
        "pagination": {"odata_context": data.get("@odata.context")},
    }


def normalize_alerts_payload(data: dict[str, Any]) -> dict[str, Any]:
    """``GET /api/alerts`` — ``value`` is alerts."""
    rows = _odata_value(data)
    items: list[dict[str, Any]] = []
    for row in rows[:5000]:
        if not isinstance(row, dict):
            continue
        aid = str(row.get("id") or "")
        items.append(
            {
                "id": aid or "alert",
                "title": str(row.get("title") or aid),
                "kind": "defender_alert",
                "severity": row.get("severity"),
                "timestamp": row.get("alertCreationTime") or row.get("lastUpdateTime"),
                "metadata": {
                    "status": row.get("status"),
                    "category": row.get("category"),
                    "detectionSource": row.get("detectionSource"),
                    "machineId": row.get("machineId"),
                },
            }
        )
    return {
        "vendor": "defender_for_endpoint",
        "artifact_type": "alerts",
        "item_count": len(items),
        "items": items,
        "pagination": {"odata_context": data.get("@odata.context")},
    }


def normalize_vulnerabilities_payload(data: dict[str, Any]) -> dict[str, Any]:
    """``GET /api/vulnerabilities/machinesVulnerabilities``."""
    rows = _odata_value(data)
    items: list[dict[str, Any]] = []
    for row in rows[:5000]:
        if not isinstance(row, dict):
            continue
        vid = str(row.get("id") or "")
        cve = str(row.get("cveId") or "")
        items.append(
            {
                "id": vid or cve or "vuln",
                "title": cve or vid,
                "kind": "machine_software_vulnerability",
                "severity": row.get("severity"),
                "timestamp": None,
                "metadata": {
                    "machineId": row.get("machineId"),
                    "productName": row.get("productName"),
                    "productVendor": row.get("productVendor"),
                    "productVersion": row.get("productVersion"),
                    "fixingKbId": row.get("fixingKbId"),
                },
            }
        )
    return {
        "vendor": "defender_for_endpoint",
        "artifact_type": "vulnerabilities",
        "item_count": len(items),
        "items": items,
        "pagination": {"odata_context": data.get("@odata.context")},
    }
