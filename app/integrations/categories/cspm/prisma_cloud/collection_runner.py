"""Orchestrate Prisma Cloud CSPM evidence collection."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.integrations.categories.cspm.prisma_cloud.collector import collect_for_master, prisma_evidence_for_storage
from app.integrations.categories.cspm.prisma_cloud.credentials import credentials_valid_shape, ready_for_collection
from app.integrations.categories.cspm.prisma_cloud.seed import ALL_PRISMA_EVIDENCE_CODES, EVIDENCE_MASTER_NAME_ORDER
from app.integrations.categories.cspm.prisma_cloud.token_refresh import ensure_prisma_jwt
from app.integrations.categories.cspm.prisma_cloud.constants import PRISMA_CLOUD_SOURCE
from app.integrations.core.constants import EVIDENCE_FROM_TOOL
from app.integrations.core.persistence import (
    normalize_evidence_master_description,
    tool_integration_service as persistence,
)
from app.schemas import CollectEvidenceResponse, CollectionItemResult

logger = logging.getLogger(__name__)


def run_prisma_cloud_evidence_collection_after_configure_background(org_id: str, tool_id: str, user_id: str) -> None:
    from app.database import pooled_session

    try:
        with pooled_session() as session:
            out = run_prisma_cloud_evidence_collection(
                session,
                org_id=org_id,
                tool_id=tool_id,
                user_id=user_id,
                evidence_codes=None,
                date_from=None,
                date_to=None,
            )
            ok = sum(1 for r in out.results if r.status == "success")
            logger.info(
                "Post-configure Prisma Cloud evidence collection finished org=%s tool=%s success=%s/%s",
                org_id,
                tool_id,
                ok,
                len(out.results),
            )
    except Exception:
        logger.exception(
            "Post-configure Prisma Cloud evidence collection failed org=%s tool=%s",
            org_id,
            tool_id,
        )


def run_prisma_cloud_evidence_collection(
    session: Session,
    *,
    org_id: str,
    tool_id: str,
    user_id: str,
    evidence_codes: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> CollectEvidenceResponse:
    del date_from, date_to
    integration = persistence.get_integration(session, org_id, tool_id)
    if not integration:
        raise ValueError("Integration not found; call /configure first.")

    cfg = ensure_prisma_jwt(session, integration)
    if not isinstance(cfg, dict):
        raise ValueError("Invalid configuration_data")
    if not ready_for_collection(cfg) or not credentials_valid_shape(cfg):
        raise ValueError(
            "Prisma Cloud is not ready: set api_base_url, access_key_id, and secret_key, then POST /configure."
        )
    jwt = cfg.get("prisma_jwt")
    if not jwt or not str(jwt).strip():
        raise ValueError("Missing Prisma Cloud JWT after login.")

    code_filter = evidence_codes if evidence_codes else list(ALL_PRISMA_EVIDENCE_CODES)
    masters = persistence.list_evidence_masters(
        session,
        tool_id=tool_id,
        evidence_codes=code_filter,
        master_name_order=EVIDENCE_MASTER_NAME_ORDER,
        source=PRISMA_CLOUD_SOURCE,
    )
    if not masters:
        raise ValueError(
            "No evidence_masters for this tool's domain with source prisma_cloud; run seed_prisma_cloud_evidence_masters."
        )

    results: list[CollectionItemResult] = []
    for master in masters:
        started = datetime.now(timezone.utc)
        try:
            content = collect_for_master(master, cfg, jwt=str(jwt))
            ev = persistence.upsert_evidence_full_replace(
                session,
                organization_id=org_id,
                title=master["name"],
                tool_id=tool_id,
                evidence_code=master["code"],
                evidence_description=normalize_evidence_master_description(master),
            )
            mapped = persistence.remap_evidence_to_controls(
                session,
                evidence_id=ev["id"],
                evidence_master_id=master["id"],
            )
            persistence.insert_evidence_collection(
                session,
                evidence_id=ev["id"],
                evidence_name=master["name"],
                user_id=user_id,
                tool_id=tool_id,
                tool_evidence=prisma_evidence_for_storage(content),
                evidence_from=EVIDENCE_FROM_TOOL,
                status="success",
                detail={"mapped_controls": mapped},
                error_message=None,
                started_at=started,
                completed_at=datetime.now(timezone.utc),
            )
            results.append(
                CollectionItemResult(
                    evidence_master_code=master["code"],
                    name=master["name"],
                    status="success",
                    error=None,
                )
            )
        except Exception as e:  # noqa: BLE001
            session.rollback()
            persistence.insert_evidence_collection_after_failed_collect(
                session,
                organization_id=org_id,
                tool_id=tool_id,
                master=master,
                user_id=user_id,
                tool_evidence={},
                status="failed",
                detail={"evidence_master_code": master["code"], "name": master["name"]},
                error_message=str(e)[:8000],
                started_at=started,
                completed_at=datetime.now(timezone.utc),
            )
            results.append(
                CollectionItemResult(
                    evidence_master_code=master["code"],
                    name=master["name"],
                    status="failed",
                    error=str(e),
                )
            )

    return CollectEvidenceResponse(
        org_id=org_id,
        tool_id=tool_id,
        user_id=user_id,
        results=results,
    )
