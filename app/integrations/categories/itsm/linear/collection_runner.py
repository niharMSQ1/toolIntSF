"""Orchestrate Linear ITSM evidence collection."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.integrations.categories.itsm.linear.collector import (
    collect_all_issues,
    collect_for_master,
    linear_evidence_for_storage,
)
from app.integrations.categories.itsm.linear.credentials import (
    has_access_token,
    resolve_access_token,
    resolve_graphql_url,
)
from app.integrations.categories.itsm.linear.seed import ALL_LINEAR_ITSM_EVIDENCE_CODES, EVIDENCE_MASTER_NAME_ORDER
from app.integrations.categories.itsm.linear.token_refresh import refresh_linear_access_tokens
from app.integrations.categories.itsm.jira.constants import JIRA_CLOUD_SOURCE
from app.integrations.core.constants import EVIDENCE_FROM_TOOL
from app.integrations.core.persistence import (
    normalize_evidence_master_description,
    tool_integration_service as persistence,
)
from app.schemas import CollectEvidenceResponse, CollectionItemResult

logger = logging.getLogger(__name__)
_SHARED_ITSM_CATALOG_SOURCE = "itsm_catalog"


def _list_linear_evidence_masters(
    session: Session,
    *,
    tool_id: str,
    code_filter: list[str],
) -> list[dict[str, object]]:
    """
    Linear and Jira currently share the same ITSM EV code catalog, but evidence_masters.code
    is globally unique in this database. If Jira seeded the shared ITSM rows first, Linear
    cannot insert duplicate codes under source='linear'. In that case, reuse the shared Jira
    ITSM masters for the same domain instead of failing collection outright.
    """
    masters = persistence.list_evidence_masters(
        session,
        tool_id=tool_id,
        evidence_codes=code_filter,
        master_name_order=EVIDENCE_MASTER_NAME_ORDER,
        source="linear",
    )
    if masters:
        return masters
    masters = persistence.list_evidence_masters(
        session,
        tool_id=tool_id,
        evidence_codes=code_filter,
        master_name_order=EVIDENCE_MASTER_NAME_ORDER,
        source=JIRA_CLOUD_SOURCE,
    )
    if masters:
        return masters
    return persistence.list_evidence_masters(
        session,
        tool_id=tool_id,
        evidence_codes=code_filter,
        master_name_order=EVIDENCE_MASTER_NAME_ORDER,
        source=_SHARED_ITSM_CATALOG_SOURCE,
    )


def run_linear_evidence_collection(
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

    try:
        new_cfg, _ = refresh_linear_access_tokens(session, integration, force=False)
    except ValueError:
        new_cfg = dict(integration["configuration_data"] or {})
    if not isinstance(new_cfg, dict):
        new_cfg = {}
    if not has_access_token(new_cfg):
        raise ValueError("Complete Linear OAuth first (access token missing).")

    token = resolve_access_token(new_cfg)
    if not token:
        raise ValueError("Complete Linear OAuth first (access token missing).")
    graphql_url = resolve_graphql_url(new_cfg)

    code_filter = evidence_codes if evidence_codes else list(ALL_LINEAR_ITSM_EVIDENCE_CODES)
    masters = _list_linear_evidence_masters(
        session,
        tool_id=tool_id,
        code_filter=code_filter,
    )
    if not masters:
        raise ValueError("No evidence_masters for this tool's domain; run /configure to seed.")

    dataset = collect_all_issues(
        new_cfg,
        access_token=token,
        graphql_url=graphql_url,
    )

    results: list[CollectionItemResult] = []

    for master in masters:
        started = datetime.now(timezone.utc)
        try:
            content = collect_for_master(master, dataset)
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
                tool_evidence=linear_evidence_for_storage(content),
                evidence_from=EVIDENCE_FROM_TOOL,
                source="Linear GraphQL API",
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


def run_linear_evidence_collection_after_oauth_background(org_id: str, tool_id: str, user_id: str) -> None:
    from app.database import pooled_session

    try:
        with pooled_session() as session:
            out = run_linear_evidence_collection(
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
                "Post-OAuth Linear evidence collection finished org=%s tool=%s success=%s/%s",
                org_id,
                tool_id,
                ok,
                len(out.results),
            )
    except Exception:
        logger.exception(
            "Post-OAuth Linear evidence collection failed org=%s tool=%s user_id=%s",
            org_id,
            tool_id,
            user_id,
        )
