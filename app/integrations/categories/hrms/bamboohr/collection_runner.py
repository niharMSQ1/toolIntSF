"""Orchestrate BambooHR evidence collection."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.integrations.categories.hrms.bamboohr.collector import (
    bamboohr_evidence_for_tool_storage,
    collect_for_master,
    fetch_employee_directory,
)
from app.integrations.categories.hrms.bamboohr.credentials import has_usable_credentials
from app.integrations.categories.hrms.bamboohr.employee_sync import sync_employees_from_bamboohr
from app.integrations.categories.hrms.bamboohr.seed import EVIDENCE_MASTER_NAME_ORDER
from app.integrations.categories.hrms.bamboohr.token_refresh import ensure_fresh_credentials
from app.integrations.core.persistence import (
    normalize_evidence_master_description,
    tool_integration_service as persistence,
)
from app.schemas import CollectEvidenceResponse, CollectionItemResult

logger = logging.getLogger(__name__)


def run_bamboohr_evidence_collection(
    session: Session,
    *,
    org_id: str,
    tool_id: str,
    user_id: str,
    evidence_codes: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> CollectEvidenceResponse:
    """Run the full BambooHR evidence collection loop."""
    integration = persistence.get_integration(session, org_id, tool_id)
    if not integration:
        raise ValueError("Integration not found; call /configure first.")

    cfg = ensure_fresh_credentials(session, integration)
    if not has_usable_credentials(cfg):
        raise ValueError("Complete BambooHR setup first (credentials missing).")

    masters = persistence.list_evidence_masters(
        session,
        tool_id=tool_id,
        evidence_codes=evidence_codes,
        master_name_order=EVIDENCE_MASTER_NAME_ORDER,
        source="bamboohr",
    )
    if not masters:
        raise ValueError("No BambooHR evidence_masters for this tool's domain; run /configure to seed.")

    directory_cache = fetch_employee_directory(cfg)
    rows = list(directory_cache.get("rows") or [])
    if rows:
        ins, upd = sync_employees_from_bamboohr(
            session,
            organization_id=org_id,
            sync_user_id=user_id,
            rows=rows,
        )
        logger.info(
            "BambooHR -> employees table: inserted=%s updated=%s (org=%s)",
            ins,
            upd,
            org_id,
        )

    results: list[CollectionItemResult] = []

    for master in masters:
        started = datetime.now(timezone.utc)
        try:
            content = collect_for_master(
                master,
                directory_cache,
                date_from=date_from,
                date_to=date_to,
            )
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
                tool_evidence=bamboohr_evidence_for_tool_storage(content),
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


def run_bamboohr_evidence_collection_after_auth_background(org_id: str, tool_id: str, user_id: str) -> None:
    from app.database import pooled_session

    try:
        with pooled_session() as session:
            out = run_bamboohr_evidence_collection(
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
                "Post-auth BambooHR evidence collection finished org=%s tool=%s success=%s/%s",
                org_id,
                tool_id,
                ok,
                len(out.results),
            )
    except Exception:
        logger.exception(
            "Post-auth BambooHR evidence collection failed org=%s tool=%s user_id=%s",
            org_id,
            tool_id,
            user_id,
        )

