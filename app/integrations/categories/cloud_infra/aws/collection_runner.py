"""Orchestrates AWS evidence collection using domain-driven evidence_masters."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.integrations.categories.cloud_infra.aws.client import validate_credentials
from app.integrations.categories.cloud_infra.aws.collector import (
    EVIDENCE_MASTER_NAME_ORDER,
    collect_for_master,
)
from app.integrations.core.persistence import (
    normalize_evidence_master_description,
    tool_integration_service as persistence,
)
from app.schemas import CollectEvidenceResponse, CollectionItemResult

logger = logging.getLogger(__name__)

_EXPECTED_TOOL_NAME = "aws"
_EXPECTED_DOMAIN_NAME = "cloud_infra"
_COLLECTION_SOURCE = "AWS API"


def _assert_aws_cloud_infra_tool(session: Session, tool_id: str) -> None:
    tool = persistence.get_tool_catalog_entry(session, tool_id)
    tool_name = str(tool.get("name") or "").strip().lower()
    domain_name = str(tool.get("domain_name") or "").strip().lower()
    if tool_name != _EXPECTED_TOOL_NAME:
        raise ValueError(f"Tool {tool_id!r} is not the AWS tool.")
    if not tool.get("domain_id"):
        raise ValueError("AWS tool has no domain_id; assign the CLOUD_INFRA domain in tools first.")
    if domain_name != _EXPECTED_DOMAIN_NAME:
        raise ValueError(
            f"AWS tool must belong to CLOUD_INFRA, but tools.domain_id resolves to {tool.get('domain_name')!r}."
        )


def run_aws_evidence_collection(
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
    _assert_aws_cloud_infra_tool(session, tool_id)

    integration = persistence.get_integration(session, org_id, tool_id)
    if not integration:
        raise ValueError("Integration not found; call /configure first.")

    cfg = integration.get("configuration_data")
    if not isinstance(cfg, dict):
        cfg = {}

    validate_credentials(cfg)

    masters = persistence.list_evidence_masters(
        session,
        tool_id=tool_id,
        evidence_codes=evidence_codes,
        master_name_order=EVIDENCE_MASTER_NAME_ORDER,
    )
    if not masters:
        raise ValueError("No evidence_masters for this tool's domain.")

    results: list[CollectionItemResult] = []

    for master in masters:
        started = datetime.now(timezone.utc)
        try:
            payload = collect_for_master(master, cfg)
            if payload is None:
                results.append(
                    CollectionItemResult(
                        evidence_master_code=master["code"],
                        name=master["name"],
                        status="skipped",
                        error="No AWS API mapping is registered for this evidence master.",
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
            persistence.replace_evidence_collection(
                session,
                evidence_id=ev["id"],
                evidence_name=master["name"],
                user_id=user_id,
                tool_evidence=payload,
                status="success",
                detail={"mapped_controls": mapped},
                error_message=None,
                started_at=started,
                completed_at=datetime.now(timezone.utc),
                source=_COLLECTION_SOURCE,
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
            logger.warning(
                "AWS evidence collection failed org=%s tool=%s code=%s error=%s",
                org_id,
                tool_id,
                master.get("code"),
                str(e),
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


def run_aws_evidence_collection_after_configure_background(org_id: str, tool_id: str, user_id: str) -> None:
    from app.database import pooled_session

    try:
        with pooled_session() as session:
            out = run_aws_evidence_collection(session, org_id=org_id, tool_id=tool_id, user_id=user_id)
            ok = sum(1 for r in out.results if r.status == "success")
            logger.info(
                "Post-config AWS evidence collection finished org=%s tool=%s success=%s/%s",
                org_id,
                tool_id,
                ok,
                len(out.results),
            )
    except Exception:
        logger.exception(
            "Post-config AWS evidence collection failed org=%s tool=%s user_id=%s",
            org_id,
            tool_id,
            user_id,
        )
