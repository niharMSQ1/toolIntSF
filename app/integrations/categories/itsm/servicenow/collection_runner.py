"""Orchestrates ServiceNow ITSM evidence collection using generic GRC persistence."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.integrations.categories.itsm.servicenow.collector import (
    collect_for_master,
    servicenow_evidence_for_tool_storage,
)
from app.integrations.categories.itsm.servicenow.seed import CODE_TO_SCHEMA, EVIDENCE_MASTER_NAME_ORDER
from app.integrations.core.persistence import (
    normalize_evidence_master_description,
    tool_integration_service as persistence,
)
from app.schemas import ServiceNowCollectEvidenceResponse, ServiceNowCollectionItemResult

logger = logging.getLogger(__name__)

_SUPPORTED_MASTER_SOURCES = {"itsm_catalog", "servicenow"}
_COLLECTION_SOURCE = "ServiceNow API"
_COLLECTION_WINDOW_DAYS = 30


def _resolve_collection_window(
    *,
    now: datetime,
    last_collection_at: datetime | None,
    requested_date_from: str | None,
    requested_date_to: str | None,
) -> tuple[str | None, str | None, str | None]:
    if requested_date_from or requested_date_to:
        return requested_date_from, requested_date_to, None
    if last_collection_at is None:
        return (now - timedelta(days=_COLLECTION_WINDOW_DAYS)).date().isoformat(), now.date().isoformat(), None
    if now - last_collection_at < timedelta(days=_COLLECTION_WINDOW_DAYS):
        return None, None, "Collected within the last 30 days; skipping fetch."
    next_date_from = (last_collection_at + timedelta(days=1)).date().isoformat()
    return next_date_from, now.date().isoformat(), None


def run_servicenow_evidence_collection(
    session: Session,
    *,
    org_id: str,
    tool_id: str,
    user_id: str,
    evidence_codes: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> ServiceNowCollectEvidenceResponse:
    integration = persistence.get_integration(session, org_id, tool_id)
    if not integration:
        raise ValueError("Integration not found; call /configure first.")

    cfg = integration.get("configuration_data")
    if not isinstance(cfg, dict):
        cfg = {}

    masters = persistence.list_evidence_masters(
        session,
        tool_id=tool_id,
        evidence_codes=evidence_codes,
        master_name_order=EVIDENCE_MASTER_NAME_ORDER,
    )
    masters = [
        master
        for master in masters
        if str(master.get("source") or "").strip() in _SUPPORTED_MASTER_SOURCES
        and str(master.get("code") or "").strip() in CODE_TO_SCHEMA
    ]
    if not masters:
        raise ValueError("No supported ServiceNow evidence_masters for this tool's domain.")

    results: list[ServiceNowCollectionItemResult] = []
    source_cache: dict[str, list[dict[str, Any]]] = {}

    for master in masters:
        started = datetime.now(timezone.utc)
        try:
            existing_evidence = persistence.get_evidence_by_org_title(session, org_id, master["name"])
            last_collection_at = None
            if existing_evidence is not None:
                last_collection_at = persistence.get_latest_evidence_collection_created_at(
                    session,
                    evidence_id=existing_evidence["id"],
                    source=_COLLECTION_SOURCE,
                )

            effective_date_from, effective_date_to, skip_reason = _resolve_collection_window(
                now=started,
                last_collection_at=last_collection_at,
                requested_date_from=date_from,
                requested_date_to=date_to,
            )
            if skip_reason is not None:
                results.append(
                    ServiceNowCollectionItemResult(
                        evidence_master_code=master["code"],
                        name=master["name"],
                        status="skipped",
                        error=skip_reason,
                        service_now_response=None,
                    )
                )
                continue

            content = collect_for_master(
                master,
                cfg,
                date_from=effective_date_from,
                date_to=effective_date_to,
                source_cache=source_cache,
            )
            raw_records = servicenow_evidence_for_tool_storage(content)
            if not raw_records:
                results.append(
                    ServiceNowCollectionItemResult(
                        evidence_master_code=master["code"],
                        name=master["name"],
                        status="skipped",
                        error="No new data found for the eligible collection window.",
                        service_now_response={"result": []},
                    )
                )
                continue

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
                tool_evidence=raw_records,
                status="success",
                detail={"mapped_controls": mapped},
                error_message=None,
                started_at=started,
                completed_at=datetime.now(timezone.utc),
                source=_COLLECTION_SOURCE,
            )
            results.append(
                ServiceNowCollectionItemResult(
                    evidence_master_code=master["code"],
                    name=master["name"],
                    status="success",
                    error=None,
                    service_now_response={"result": raw_records},
                )
            )
        except Exception as e:  # noqa: BLE001
            session.rollback()
            logger.warning(
                "Skipping DB persistence for failed ServiceNow evidence collection org=%s tool=%s code=%s error=%s",
                org_id,
                tool_id,
                master["code"],
                str(e),
            )
            results.append(
                ServiceNowCollectionItemResult(
                    evidence_master_code=master["code"],
                    name=master["name"],
                    status="failed",
                    error=str(e),
                    service_now_response=None,
                )
            )

    return ServiceNowCollectEvidenceResponse(
        org_id=org_id,
        tool_id=tool_id,
        user_id=user_id,
        results=results,
    )


def run_servicenow_evidence_collection_after_configure_background(org_id: str, tool_id: str, user_id: str) -> None:
    from app.database import pooled_session

    try:
        with pooled_session() as session:
            out = run_servicenow_evidence_collection(session, org_id=org_id, tool_id=tool_id, user_id=user_id)
            ok = sum(1 for r in out.results if r.status == "success")
            logger.info(
                "Post-config ServiceNow evidence collection finished org=%s tool=%s success=%s/%s",
                org_id,
                tool_id,
                ok,
                len(out.results),
            )
    except Exception:
        logger.exception(
            "Post-config ServiceNow evidence collection failed org=%s tool=%s user_id=%s",
            org_id,
            tool_id,
            user_id,
        )
