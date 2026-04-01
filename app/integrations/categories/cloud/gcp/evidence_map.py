"""Map cloud evidence codes to basic GCP collection strategies."""

from __future__ import annotations

from typing import Literal

GcpStrategy = Literal[
    "asset_inventory",
    "resource_labels",
    "iam_policy",
    "storage_inventory",
    "compute_inventory",
    "partial_metadata",
]

# Reuse Cloud evidence names/codes used in AWS cloud domain.
GCP_SEED_ROWS: list[dict[str, str]] = [
    {"code": "EV-16", "name": "Asset Inventory Register — Cloud", "category": "Cloud", "api_endpoint": "compute.instances.aggregatedList"},
    {"code": "EV-17", "name": "Asset Ownership Records — Cloud", "category": "Cloud", "api_endpoint": "compute.instances.aggregatedList(labels)"},
    {"code": "EV-84", "name": "Asset Classification Records — Cloud", "category": "Cloud", "api_endpoint": "cloudresourcemanager.projects.getIamPolicy"},
    {"code": "EV-115", "name": "Vendor Inventory Register — Cloud", "category": "Cloud", "api_endpoint": "cloudresourcemanager.projects.get"},
    {"code": "EV-116", "name": "Vendor Data Classification Records — Cloud", "category": "Cloud", "api_endpoint": "storage.buckets.list"},
    {"code": "EV-243", "name": "Data Classification Register — Cloud", "category": "Cloud", "api_endpoint": "storage.buckets.list"},
    {"code": "EV-295", "name": "Data Asset Register — Cloud", "category": "Cloud", "api_endpoint": "storage.buckets.list,compute.instances.aggregatedList"},
    {"code": "EV-326", "name": "AI System Inventory — Cloud", "category": "Cloud", "api_endpoint": "aiplatform.locations.list"},
    {"code": "EV-377", "name": "Asset Maintenance Log — Cloud", "category": "Cloud", "api_endpoint": "compute.instances.aggregatedList"},
    {"code": "EV-390", "name": "User Account Register — Cloud", "category": "Cloud", "api_endpoint": "cloudresourcemanager.projects.getIamPolicy"},
    {"code": "EV-433", "name": "AI Model Inventory — Cloud", "category": "Cloud", "api_endpoint": "aiplatform.models.list"},
    {"code": "EV-527", "name": "PII System Access Register — Cloud", "category": "Cloud", "api_endpoint": "storage.buckets.list"},
    {"code": "EV-541", "name": "Data Inventory Register — Cloud", "category": "Cloud", "api_endpoint": "storage.buckets.list"},
    {"code": "EV-547", "name": "Subprocessors Inventory Register — Cloud", "category": "Cloud", "api_endpoint": "cloudresourcemanager.projects.get"},
    {"code": "EV-248", "name": "Sensor System Configuration Records — Cloud", "category": "Cloud", "api_endpoint": "compute.instances.aggregatedList"},
]

ALL_GCP_EVIDENCE_CODES: tuple[str, ...] = tuple(r["code"] for r in GCP_SEED_ROWS)
EVIDENCE_MASTER_NAME_ORDER: tuple[str, ...] = tuple(r["name"] for r in GCP_SEED_ROWS)

EVIDENCE_CODE_STRATEGY: dict[str, GcpStrategy] = {
    "EV-16": "asset_inventory",
    "EV-17": "resource_labels",
    "EV-84": "iam_policy",
    "EV-115": "asset_inventory",
    "EV-116": "storage_inventory",
    "EV-243": "storage_inventory",
    "EV-295": "asset_inventory",
    "EV-326": "partial_metadata",
    "EV-377": "compute_inventory",
    "EV-390": "iam_policy",
    "EV-433": "partial_metadata",
    "EV-527": "iam_policy",
    "EV-541": "storage_inventory",
    "EV-547": "asset_inventory",
    "EV-248": "compute_inventory",
}

