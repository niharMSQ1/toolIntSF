"""Orchestrate ForgeRock IAM evidence collection."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.integrations.categories.idp.forgerock.collector import collect_for_master, forgerock_evidence_for_storage
from app.integrations.categories.idp.forgerock.credentials import ready_for_collection, resolve_access_token, resolve_api_base
from app.integrations.categories.idp.forgerock.seed import ALL_FORGEROCK_IAM_EVIDENCE_CODES, EVIDENCE_MASTER_NAME_ORDER
from app.integrations.categories.idp.iam_evidence_catalog import iam_evidence_master_filter_sources
from app.integrations.core.constants import EVIDENCE_FROM_TOOL
from app.integrations.core.persistence import (
    normalize_evidence_master_description,
    tool_integration_service as persistence,
)
from app.schemas import CollectEvidenceResponse, CollectionItemResult

logger = logging.getLogger(__name__)


def run_forgerock_evidence_collection_after_configure_background(
    org_id: str,
    tool_id: str,
    user_id: str,
) -> None:
    from app.database import pooled_session

    try:
        with pooled_session() as session:
            out = run_forgerock_evidence_collection(
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
                "Post-configure ForgeRock evidence finished org=%s tool=%s success=%s/%s",
                org_id,
                tool_id,
                ok,
                len(out.results),
            )
    except Exception:
        logger.exception(
            "Post-configure ForgeRock evidence failed org=%s tool=%s user_id=%s",
            org_id,
            tool_id,
            user_id,
        )


def run_forgerock_evidence_collection(
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

    cfg = integration["configuration_data"]
    if not isinstance(cfg, dict):
        raise ValueError("Invalid configuration_data")
    if not ready_for_collection(cfg):
        raise ValueError(
            "Set forgerock_token_url, forgerock_api_base, and client_id/client_secret (or access_token), then POST /configure.",
        )

    resolve_api_base(cfg)
    resolve_access_token(cfg)

    code_filter = evidence_codes if evidence_codes else list(ALL_FORGEROCK_IAM_EVIDENCE_CODES)
    masters = persistence.list_evidence_masters(
        session,
        tool_id=tool_id,
        evidence_codes=code_filter,
        master_name_order=EVIDENCE_MASTER_NAME_ORDER,
        source=iam_evidence_master_filter_sources(),
    )
    if not masters:
        raise ValueError(
            "No evidence_masters for this tool's domain; seed IAM evidence before collect.",
        )

    results: list[CollectionItemResult] = []

    for master in masters:
        started = datetime.now(timezone.utc)
        try:
            content = collect_for_master(master, cfg)
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
                tool_evidence=forgerock_evidence_for_storage(content),
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


def validate_forgerock_credentials(cfg: dict[str, Any]) -> bool:
    try:
        from app.integrations.categories.idp.forgerock import api_client

        t = resolve_access_token(cfg)
        if not t:
            return False
        return api_client.validate_connection(cfg, t)
    except Exception:
        return False
