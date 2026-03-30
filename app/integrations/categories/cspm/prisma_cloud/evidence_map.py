"""
Maps evidence_masters.code (CSPM domain) to Prisma Cloud REST strategies.

Uses dedicated EV-701+ codes to avoid colliding with globally unique EV-604.. (Wiz) rows.
API references: pan.dev Prisma Cloud CSPM.
"""

from __future__ import annotations

from typing import Literal

PrismaStrategy = Literal[
    "cloud_accounts",
    "alerts_v2",
    "compliance_posture_v2",
    "partial_metadata",
]

# Seeded with source=prisma_cloud for CSPM tools using Palo Alto Prisma Cloud.
PRISMA_CSPM_SEED_ROWS: list[dict[str, str]] = [
    {
        "code": "EV-701",
        "name": "Prisma Cloud — cloud accounts onboarded",
        "category": "CSPM",
        "api_endpoint": "GET /cloud",
    },
    {
        "code": "EV-702",
        "name": "Prisma Cloud — alerts (List Alerts V2)",
        "category": "CSPM",
        "api_endpoint": "GET /v2/alert",
    },
    {
        "code": "EV-703",
        "name": "Prisma Cloud — compliance posture (V2)",
        "category": "CSPM",
        "api_endpoint": "GET /v2/compliance/posture",
    },
    {
        "code": "EV-704",
        "name": "Prisma Cloud — API session (JWT health)",
        "category": "CSPM",
        "api_endpoint": "GET /auth_token/extend",
    },
]

ALL_PRISMA_EVIDENCE_CODES: tuple[str, ...] = tuple(r["code"] for r in PRISMA_CSPM_SEED_ROWS)
EVIDENCE_MASTER_NAME_ORDER: tuple[str, ...] = tuple(r["name"] for r in PRISMA_CSPM_SEED_ROWS)

EVIDENCE_CODE_STRATEGY: dict[str, PrismaStrategy] = {
    "EV-701": "cloud_accounts",
    "EV-702": "alerts_v2",
    "EV-703": "compliance_posture_v2",
    "EV-704": "partial_metadata",
}
