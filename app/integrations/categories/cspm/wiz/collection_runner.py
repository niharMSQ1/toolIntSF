"""Orchestrate Wiz CSPM evidence collection."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.integrations.categories.cspm.wiz.collector import collect_for_master, wiz_evidence_for_storage
from app.integrations.categories.cspm.wiz.credentials import ready_for_collection, resolve_graphql_url
from app.integrations.categories.cspm.wiz.seed import ALL_CSPM_WIZ_EVIDENCE_CODES, EVIDENCE_MASTER_NAME_ORDER
from app.integrations.categories.cspm.wiz.token_refresh import force_refresh_access_token
from app.integrations.core.constants import EVIDENCE_FROM_TOOL
from app.integrations.core.persistence import (
    normalize_evidence_master_description,
    tool_integration_service as persistence,
)
from app.schemas import CollectEvidenceResponse, CollectionItemResult

logger = logging.getLogger(__name__)


def run_wiz_evidence_collection_after_configure_background(org_id: str, tool_id: str, user_id: str) -> None:
    """Run full Wiz collection in a new DB session (FastAPI BackgroundTasks)."""
    from app.database import pooled_session

    try:
        with pooled_session() as session:
            out = run_wiz_evidence_collection(
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
                "Post-configure Wiz evidence collection finished org=%s tool=%s success=%s/%s",
                org_id,
                tool_id,
                ok,
                len(out.results),
            )
    except Exception:
        logger.exception(
            "Post-configure Wiz evidence collection failed org=%s tool=%s user_id=%s",
            org_id,
            tool_id,
            user_id,
        )


def run_wiz_evidence_collection(
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

    cfg = force_refresh_access_token(session, integration)
    if not isinstance(cfg, dict):
        raise ValueError("Invalid configuration_data")
    if not ready_for_collection(cfg):
        raise ValueError(
            "Wiz is not ready: set graphql_url and client_id/client_secret, then POST /configure to obtain a token."
        )
    resolve_graphql_url(cfg)
    token = cfg.get("access_token")
    if not token or not str(token).strip():
        raise ValueError("Missing access token after configure.")

    code_filter = evidence_codes if evidence_codes else list(ALL_CSPM_WIZ_EVIDENCE_CODES)
    masters = persistence.list_evidence_masters(
        session,
        tool_id=tool_id,
        evidence_codes=code_filter,
        master_name_order=EVIDENCE_MASTER_NAME_ORDER,
        source=None,
    )
    if not masters:
        raise ValueError(
            "No evidence_masters for this tool's domain; seed evidence_masters manually before collect."
        )

    results: list[CollectionItemResult] = []

    for master in masters:
        started = datetime.now(timezone.utc)
        try:
            content = collect_for_master(master, cfg, access_token=str(token))
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
                tool_evidence=wiz_evidence_for_storage(content),
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
