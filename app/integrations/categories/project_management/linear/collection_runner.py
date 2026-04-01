"""Collect Linear data and persist evidence rows via generic GRC persistence."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.integrations.categories.project_management.linear import api_client
from app.integrations.categories.project_management.linear.credentials import resolve_api_key
from app.integrations.categories.project_management.linear.evidence_map import (
    GRAPHQL_QUERY_DOC,
    REQUIRED_FIELDS,
    resolve_strategy,
)
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


def _read_path(item: dict[str, Any], dotted: str) -> Any:
    cur: Any = item
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur.get(part)
    return cur


def _validate_rows(rows: list[dict[str, Any]], required_fields: tuple[str, ...], *, allow_empty: bool = False) -> None:
    if not rows and not allow_empty:
        raise ValueError("No records returned by Linear query.")
    for idx, row in enumerate(rows):
        missing = [field for field in required_fields if _read_path(row, field) in (None, "")]
        if missing:
            raise ValueError(f"Linear record #{idx} missing required fields: {', '.join(missing)}")


def _collect_for_master(api_key: str, master: dict[str, Any]) -> dict[str, Any]:
    strategy = resolve_strategy(master.get("code", ""))
    required_fields = REQUIRED_FIELDS[strategy]

    if strategy == "identity_viewer":
        viewer = api_client.get_viewer(api_key) or {}
        _validate_rows([viewer], required_fields)
        return {
            "strategy": strategy,
            "query": GRAPHQL_QUERY_DOC[strategy],
            "required_fields": list(required_fields),
            "record_count": 1,
            "records": [viewer],
        }
    if strategy == "users_register":
        users = api_client.list_users(api_key, first=100)
        _validate_rows(users, required_fields)
        return {
            "strategy": strategy,
            "query": GRAPHQL_QUERY_DOC[strategy],
            "required_fields": list(required_fields),
            "record_count": len(users),
            "records": users,
        }
    if strategy == "projects_register":
        projects = api_client.list_projects(api_key, first=100)
        _validate_rows(projects, required_fields)
        return {
            "strategy": strategy,
            "query": GRAPHQL_QUERY_DOC[strategy],
            "required_fields": list(required_fields),
            "record_count": len(projects),
            "records": projects,
        }
    if strategy == "teams_register":
        teams = api_client.list_teams(api_key, first=100)
        _validate_rows(teams, required_fields)
        return {
            "strategy": strategy,
            "query": GRAPHQL_QUERY_DOC[strategy],
            "required_fields": list(required_fields),
            "record_count": len(teams),
            "records": teams,
        }
    if strategy == "workflow_states_register":
        states = api_client.list_workflow_states(api_key, first=100)
        _validate_rows(states, required_fields)
        return {
            "strategy": strategy,
            "query": GRAPHQL_QUERY_DOC[strategy],
            "required_fields": list(required_fields),
            "record_count": len(states),
            "records": states,
        }

    issues = api_client.list_issues(api_key, first=100)
    _validate_rows(issues, required_fields)
    return {
        "strategy": strategy,
        "query": GRAPHQL_QUERY_DOC[strategy],
        "required_fields": list(required_fields),
        "record_count": len(issues),
        "records": issues,
    }


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
    """Collect Linear evidence snapshots and store in evidence tables."""
    del date_from, date_to  # Not used by current Linear GraphQL queries.

    integration = persistence.get_integration(session, org_id, tool_id)
    if not integration:
        raise ValueError("Integration not found; call /configure first.")

    cfg = integration.get("configuration_data")
    if not isinstance(cfg, dict):
        raise ValueError("Invalid configuration_data")

    api_key = resolve_api_key(cfg)
    if not api_key:
        raise ValueError("Missing api_key (Linear personal API key).")

    masters = list_evidence_masters(
        session,
        tool_id=tool_id,
        evidence_codes=evidence_codes,
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
            evidence_payload = _collect_for_master(api_key, master)
            ev = upsert_evidence_full_replace(
                session,
                organization_id=org_id,
                title=master["name"],
                tool_id=tool_id,
                evidence_code=master["code"],
                evidence_description=normalize_evidence_master_description(master),
            )
            mapped = remap_evidence_to_controls(
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
                    "source": "linear/graphql",
                    "evidence_payload": evidence_payload,
                    "evidence_master_code": master["code"],
                },
                status="success",
                detail={
                    "mapped_controls": mapped,
                    "collected_at": now_utc.isoformat(),
                    "strategy": evidence_payload["strategy"],
                    "record_count": evidence_payload["record_count"],
                },
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
            logger.exception("Linear collect failed for master=%s", master.get("code"))
            try:
                insert_evidence_collection_after_failed_collect(
                    session,
                    organization_id=org_id,
                    tool_id=tool_id,
                    master=master,
                    user_id=user_id,
                    tool_evidence={"source": "linear/graphql"},
                    status="failed",
                    detail=None,
                    error_message=str(e),
                    started_at=started,
                    completed_at=datetime.now(timezone.utc),
                )
            except Exception:
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
    """Background wrapper used by Linear /configure."""
    from app.database import pooled_session

    try:
        with pooled_session() as session:
            out = run_evidence_collection(session, org_id=org_id, tool_id=tool_id, user_id=user_id)
            ok = sum(1 for r in out.results if r.status == "success")
            logger.info(
                "Linear evidence collection finished org=%s tool=%s success=%s/%s",
                org_id,
                tool_id,
                ok,
                len(out.results),
            )
    except Exception:
        logger.exception("Linear evidence collection failed org=%s tool=%s user_id=%s", org_id, tool_id, user_id)

