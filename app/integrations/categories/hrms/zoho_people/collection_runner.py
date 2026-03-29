"""Orchestrates Zoho People evidence collection using generic GRC persistence."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.integrations.categories.hrms.zoho_people.api_endpoints import FORM_EMPLOYEE
from app.integrations.categories.hrms.zoho_people.collector import (
    ZohoPeopleApiNonSuccessError,
    collect_for_master,
    fetch_form_records_paginated,
    needs_employee_prefetch,
    zoho_evidence_for_tool_storage,
)
from app.integrations.categories.hrms.zoho_people.employee_preview import emit_employee_master_preview
from app.integrations.categories.hrms.zoho_people.employee_sync import sync_employees_from_zoho_people
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


def _catalog_domain_id_from_cfg(cfg: Any) -> str | None:
    """Optional UUID in config when evidence_masters were seeded under a different domain than ``tools.domain_id``."""
    if not isinstance(cfg, dict):
        return None
    for key in ("catalog_domain_id", "evidence_masters_domain_id"):
        raw = cfg.get(key)
        if raw is None:
            continue
        s = str(raw).strip()
        if not s:
            continue
        try:
            uuid.UUID(s)
        except ValueError:
            continue
        return s
    return None


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

    catalog_domain_id = _catalog_domain_id_from_cfg(cfg)

    # Scope by tools.domain_id (or catalog_domain_id override only). Do not filter evidence_masters.source.
    masters = persistence.list_evidence_masters(
        session,
        tool_id=tool_id,
        evidence_codes=evidence_codes,
        master_name_order=EVIDENCE_MASTER_NAME_ORDER,
        source=None,
        domain_id=catalog_domain_id,
    )
    if not masters:
        tool_domain_id = persistence.get_domain_id_for_tool(session, tool_id)
        effective = catalog_domain_id or str(tool_domain_id)
        raise ValueError(
            f"No evidence_masters for domain {effective} (tools.domain_id={tool_domain_id}). "
            "Seed evidence_masters for this tool's domain, or set configuration_data.catalog_domain_id / "
            "evidence_masters_domain_id if masters live under a different domain UUID."
        )

    token = resolve_access_token(cfg)
    base = cfg.get("people_base_url") or people_base_url(resolve_region(cfg))
    employee_cache: dict[str, Any] | None = None
    if needs_employee_prefetch(masters) and token:
        employee_cache = fetch_form_records_paginated(base, token, FORM_EMPLOYEE)
        emit_employee_master_preview(employee_cache)
        rows = (employee_cache or {}).get("rows") or []
        if rows:
            ins, upd = sync_employees_from_zoho_people(
                session,
                organization_id=org_id,
                sync_user_id=user_id,
                rows=rows,
            )
            logger.info(
                "Zoho People → employees table: inserted=%s updated=%s (org=%s)",
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
                cfg,
                date_from=date_from,
                date_to=date_to,
                employee_cache=employee_cache,
            )
            if isinstance(content, dict) and content.get("skipped"):
                reason = str(
                    content.get("reason")
                    or content.get("error_hint")
                    or "Collector skipped this evidence type"
                )
                results.append(
                    CollectionItemResult(
                        evidence_master_code=master["code"],
                        name=master["name"],
                        status="skipped",
                        error=reason,
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
            )
            persistence.insert_evidence_collection(
                session,
                evidence_id=ev["id"],
                evidence_name=master["name"],
                user_id=user_id,
                tool_id=tool_id,
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
        except ZohoPeopleApiNonSuccessError as e:
            logger.warning(
                "Skipping evidence (Zoho non-success): %s %s — %s",
                master.get("code"),
                master.get("name"),
                e,
            )
            results.append(
                CollectionItemResult(
                    evidence_master_code=master["code"],
                    name=master["name"],
                    status="skipped",
                    error=str(e),
                )
            )
            continue
        except Exception as e:  # noqa: BLE001
            session.rollback()
            logger.exception(
                "Zoho collect failed for %s %s (no evidence row persisted)",
                master.get("code"),
                master.get("name"),
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
