"""Collect basic GCP evidence snapshots via Google REST APIs."""

from __future__ import annotations

from typing import Any

import httpx

from app.integrations.categories.cloud.gcp.credentials import resolve_project_id
from app.integrations.categories.cloud.gcp.evidence_map import EVIDENCE_CODE_STRATEGY, GcpStrategy
from app.integrations.categories.cloud.gcp.session import build_access_token


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


def _get(client: httpx.Client, url: str, token: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    r = client.get(url, headers=_headers(token), params=params or {})
    r.raise_for_status()
    data = r.json()
    return data if isinstance(data, dict) else {}


def _build_baseline(cfg: dict[str, Any]) -> dict[str, Any]:
    project_id = resolve_project_id(cfg) or ""
    token = build_access_token(cfg)
    with httpx.Client(timeout=90.0) as client:
        project = _get(
            client,
            f"https://cloudresourcemanager.googleapis.com/v1/projects/{project_id}",
            token,
        )
        buckets = _get(
            client,
            "https://storage.googleapis.com/storage/v1/b",
            token,
            params={"project": project_id, "maxResults": 50},
        )
        instances = _get(
            client,
            f"https://compute.googleapis.com/compute/v1/projects/{project_id}/aggregated/instances",
            token,
            params={"maxResults": 50},
        )
        try:
            iam = client.post(
                f"https://cloudresourcemanager.googleapis.com/v1/projects/{project_id}:getIamPolicy",
                headers={**_headers(token), "Content-Type": "application/json"},
                json={},
            )
            iam.raise_for_status()
            iam_policy = iam.json() if isinstance(iam.json(), dict) else {}
        except Exception:
            iam_policy = {}
    return {
        "project": {
            "projectId": project.get("projectId"),
            "projectNumber": project.get("projectNumber"),
            "name": project.get("name"),
            "lifecycleState": project.get("lifecycleState"),
        },
        "buckets_sample": (buckets.get("items") or [])[:50] if isinstance(buckets.get("items"), list) else [],
        "compute_instances_aggregated_sample": instances,
        "iam_policy": iam_policy,
    }


def collect_for_master(master: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    code = str(master.get("code") or "")
    strategy: GcpStrategy = EVIDENCE_CODE_STRATEGY.get(code, "partial_metadata")  # type: ignore[assignment]
    project_id = resolve_project_id(cfg) or ""
    baseline = _build_baseline(cfg)
    out: dict[str, Any] = {
        "evidence_code": code,
        "integration": "gcp",
        "project_id": project_id,
        "strategy": strategy,
    }

    if strategy in {"asset_inventory", "partial_metadata"}:
        return {
            **out,
            "collectable_via_gcp_api": True,
            "project": baseline.get("project"),
            "buckets_count": len(baseline.get("buckets_sample") or []),
            "note": "Project metadata + bucket sample collected from GCP APIs.",
        }
    if strategy == "resource_labels":
        instances = baseline.get("compute_instances_aggregated_sample") or {}
        return {
            **out,
            "collectable_via_gcp_api": True,
            "compute_instances_labels_snapshot": instances,
        }
    if strategy == "iam_policy":
        return {
            **out,
            "collectable_via_gcp_api": True,
            "iam_policy": baseline.get("iam_policy") or {},
        }
    if strategy == "storage_inventory":
        return {
            **out,
            "collectable_via_gcp_api": True,
            "buckets_sample": baseline.get("buckets_sample") or [],
        }
    if strategy == "compute_inventory":
        return {
            **out,
            "collectable_via_gcp_api": True,
            "compute_instances_aggregated_sample": baseline.get("compute_instances_aggregated_sample") or {},
        }
    return {
        **out,
        "collectable_via_gcp_api": False,
        "message": "No collector strategy mapped for this evidence code yet.",
    }


def gcp_evidence_for_storage(payload: dict[str, Any]) -> dict[str, Any]:
    return payload

