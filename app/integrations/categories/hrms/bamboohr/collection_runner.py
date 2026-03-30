"""Orchestrates BambooHR evidence collection using generic GRC persistence.

Note: BambooHR integration currently supports fetching the employee directory.
We use that snapshot as the source payload for all HRMS catalog evidence masters.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.integrations.categories.hrms.bamboohr import api_client
from app.integrations.categories.hrms.bamboohr.credentials import resolve_api_key, ready_for_api_calls
from app.integrations.categories.hrms.bamboohr.normalize import bamboo_extract_employees
from app.integrations.core.persistence import (
    insert_evidence_collection_after_failed_collect,
    list_evidence_masters,
    normalize_evidence_master_description,
    remap_evidence_to_controls,
    tool_integration_service as persistence,
    upsert_evidence_full_replace,
)
from app.schemas import CollectEvidenceResponse, CollectionItemResult

logger = logging.getLogger(__name__)


def _employee_row_preview(raw_row: dict[str, Any], max_fields: int = 10) -> dict[str, Any]:
    """Keep tool_evidence compact (avoid storing full raw employee payload)."""

    # Common BambooHR directory keys (best-effort).
    keys = [
        "id",
        "employeeId",
        "employeeNumber",
        "displayName",
        "preferredName",
        "workEmail",
        "workPhone",
        "hireDate",
        "terminationDate",
        "employmentHistoryStatus",
        "jobTitle",
        "department",
        "supervisorId",
    ][:max_fields]

    out: dict[str, Any] = {}
    for k in keys:
        if k in raw_row:
            out[k] = raw_row.get(k)

    # Normalize some common aliases to make preview easier to consume.
    if "employeeNumber" in raw_row and "employeeNumber" not in out:
        out["employeeNumber"] = raw_row.get("employeeNumber")
    if "id" not in out and (raw_row.get("id") is not None or raw_row.get("employeeId") is not None):
        out["id"] = raw_row.get("id") or raw_row.get("employeeId")
    if "displayName" not in out:
        dn = raw_row.get("displayName") or raw_row.get("preferredName")
        if dn:
            out["displayName"] = dn

    return out


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
    """Collect BambooHR directory evidence into evidence tables."""

    integration = persistence.get_integration(session, org_id, tool_id)
    if not integration:
        raise ValueError("Integration not found; call /configure first.")

    cfg = integration.get("configuration_data")
    if not isinstance(cfg, dict):
        raise ValueError("Invalid configuration_data")

    if not ready_for_api_calls(cfg):
        raise ValueError("BambooHR is not configured (missing bamboohr_subdomain/bamboohr_api_key).")

    api_key = resolve_api_key(cfg)

    # Fetch once; reuse for all HRMS catalog masters.
    raw_directory = api_client.get_directory(cfg, api_key)
    employee_rows = bamboo_extract_employees(raw_directory)

    snapshot = {
        "source": "bamboohr/api/v1/employees/directory",
        "bamboohr_subdomain": (cfg.get("bamboohr_subdomain") or cfg.get("subdomain") or None),
        "employees_count": len(employee_rows),
        # Store preview only to keep DB size manageable.
        "employees_preview": [_employee_row_preview(r) for r in employee_rows[:50]],
    }

    masters = list_evidence_masters(
        session,
        tool_id=tool_id,
        evidence_codes=evidence_codes,
        # HRMS catalog masters can include many types that aren't directly backed
        # by the directory endpoint; we still persist a snapshot for each master.
        source=None,
        domain_id=None,
    )
    if not masters:
        effective = persistence.get_domain_id_for_tool(session, tool_id)
        raise ValueError(f"No evidence_masters found for domain {effective}.")

    results: list[CollectionItemResult] = []
    now_utc = datetime.now(timezone.utc)

    for master in masters:
        started = datetime.now(timezone.utc)
        try:
            ev = upsert_evidence_full_replace(
                session,
                organization_id=org_id,
                title=master["name"],
                tool_id=tool_id,
                evidence_code=master["code"],
                evidence_description=normalize_evidence_master_description(master),
            )

            remapped = remap_evidence_to_controls(
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
                tool_evidence={
                    "bamboohr_directory_snapshot": snapshot,
                    "evidence_master_code": master["code"],
                },
                status="success",
                detail={"mapped_controls": remapped, "collected_at": now_utc.isoformat()},
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
            logger.exception("BambooHR evidence collect failed for master=%s", master.get("code"))
            # Persist failed evidence so the UI can show it.
            try:
                insert_evidence_collection_after_failed_collect(
                    session,
                    organization_id=org_id,
                    tool_id=tool_id,
                    master=master,
                    user_id=user_id,
                    tool_evidence={"bamboohr_directory_snapshot": snapshot},
                    status="failed",
                    detail=None,
                    error_message=str(e),
                    started_at=started,
                    completed_at=datetime.now(timezone.utc),
                )
            except Exception:
                # Avoid masking the original exception; we already rolled back.
                pass

            results.append(
                CollectionItemResult(
                    evidence_master_code=master.get("code") or "",
                    name=master.get("name") or "",
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


def run_evidence_collection_after_config_background(org_id: str, tool_id: str, user_id: str) -> None:
    """Background wrapper for POST /hrms/bamboohr/configure (after credentials validation)."""
    from app.database import pooled_session

    try:
        with pooled_session() as session:
            out = run_evidence_collection(session, org_id=org_id, tool_id=tool_id, user_id=user_id)
            ok = sum(1 for r in out.results if r.status == "success")
            logger.info(
                "BambooHR evidence collection finished org=%s tool=%s success=%s/%s",
                org_id,
                tool_id,
                ok,
                len(out.results),
            )
    except Exception:
        logger.exception("BambooHR evidence collection failed org=%s tool=%s user_id=%s", org_id, tool_id, user_id)

