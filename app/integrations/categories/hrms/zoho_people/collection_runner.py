"""Orchestrates Zoho People evidence collection using generic GRC persistence."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.integrations.categories.hrms.zoho_people.collector import (
    collect_for_master,
    fetch_form_records_paginated,
    needs_employee_prefetch,
    zoho_evidence_for_tool_storage,
)
from app.integrations.categories.hrms.zoho_people.credentials import has_access_token, resolve_access_token, resolve_region
from app.integrations.categories.hrms.zoho_people.regions import people_base_url
from app.integrations.categories.hrms.zoho_people.seed import EVIDENCE_MASTER_NAME_ORDER
from app.integrations.categories.hrms.zoho_people.token_refresh import ensure_fresh_access_token
from app.integrations.core.persistence import (
    normalize_evidence_master_description,
    tool_integration_service as persistence,
)
from app.schemas import CollectEvidenceResponse, CollectionItemResult

logger = logging.getLogger(__name__)


def run_evidence_collection(
    session: Session,
    *,
    org_id: str,
    tool_id: str,
    user_id: str,
    evidence_codes: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> CollectEvidenceResponse:
    """Run the full Zoho People collection loop for the integration."""
    integration = persistence.get_integration(session, org_id, tool_id)
    if not integration:
        raise ValueError("Integration not found; call /configure first.")

    cfg = ensure_fresh_access_token(session, integration)
    if not has_access_token(cfg):
        raise ValueError("Complete OAuth first (tokens missing).")

    masters = persistence.list_evidence_masters(
        session,
        tool_id=tool_id,
        evidence_codes=evidence_codes,
        master_name_order=EVIDENCE_MASTER_NAME_ORDER,
        source="zoho_people",
    )
    if not masters:
        raise ValueError("No evidence_masters for this tool's domain; run /configure to seed.")

    token = resolve_access_token(cfg)
    base = cfg.get("people_base_url") or people_base_url(resolve_region(cfg))
    employee_cache: dict[str, Any] | None = None
    if needs_employee_prefetch(masters) and token:
        employee_cache = fetch_form_records_paginated(base, token, "employee")

    results: list[CollectionItemResult] = []

    for master in masters:
        started = datetime.now(timezone.utc)
        try:
            content = collect_for_master(
                master,
                cfg,
                date_from=date_from,
                date_to=date_to,
                employee_cache=employee_cache,
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
                mapped_by=user_id,
            )
            persistence.insert_evidence_collection(
                session,
                evidence_id=ev["id"],
                evidence_name=master["name"],
                user_id=user_id,
                tool_evidence=zoho_evidence_for_tool_storage(content),
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


def run_evidence_collection_after_oauth_background(org_id: str, tool_id: str, user_id: str) -> None:
    from app.database import pooled_session

    try:
        with pooled_session() as session:
            out = run_evidence_collection(session, org_id=org_id, tool_id=tool_id, user_id=user_id)
            ok = sum(1 for r in out.results if r.status == "success")
            logger.info(
                "Post-OAuth evidence collection finished org=%s tool=%s success=%s/%s",
                org_id,
                tool_id,
                ok,
                len(out.results),
            )
    except Exception:
        logger.exception(
            "Post-OAuth evidence collection failed org=%s tool=%s user_id=%s",
            org_id,
            tool_id,
            user_id,
        )
