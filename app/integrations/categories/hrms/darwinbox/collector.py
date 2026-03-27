"""Generic Darwinbox evidence collector using schema-driven mapping."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable

from app.integrations.categories.hrms.darwinbox import client
from app.integrations.categories.hrms.darwinbox.seed import CODE_TO_SCHEMA


SourceFetcher = Callable[[dict[str, Any]], list[dict[str, Any]]]


DARWINBOX_MAPPING_CONFIG: dict[str, dict[str, Any]] = {
    "EV-25": {
        "source": "terminations",
        "date_field": "termination_date",
        "field_map": {},
    },
    "EV-26": {
        "source": "terminations",
        "date_field": "completed_date",
        "field_map": {},
    },
    "EV-69": {
        "source": "roles",
        "field_map": {},
    },
    "EV-88": {
        "source": "trainings",
        "date_field": "completion_date",
        "field_map": {},
    },
    "EV-89": {
        "source": "trainings",
        "date_field": "completion_date",
        "field_map": {},
    },
    "EV-113": {
        "source": "background_checks",
        "date_field": "verification_date",
        "field_map": {},
    },
    "EV-114": {
        "source": "background_checks",
        "date_field": "verification_date",
        "field_map": {},
    },
    "EV-119": {
        "source": "documents",
        "date_field": "acknowledgment_date",
        "field_map": {},
    },
    "EV-121": {
        "source": "employees",
        "date_field": "action_date",
        "field_map": {
            "record_id": "disciplinary.record_id",
            "violation_type": "disciplinary.violation_type",
            "policy_violated": "disciplinary.policy_violated",
            "incident_date": "disciplinary.incident_date",
            "investigation_conducted": "disciplinary.investigation_conducted",
            "investigation_details": "disciplinary.investigation_details",
            "disciplinary_action_taken": "disciplinary.disciplinary_action_taken",
            "action_severity": "disciplinary.action_severity",
            "approved_by": "disciplinary.approved_by",
            "action_date": "disciplinary.action_date",
            "status": "disciplinary.status",
        },
    },
    "EV-128": {
        "source": "roles",
        "date_field": "effective_date",
        "field_map": {},
    },
    "EV-129": {
        "source": "roles",
        "date_field": "effective_date",
        "field_map": {},
    },
    "EV-130": {
        "source": "documents",
        "date_field": "signature_date",
        "field_map": {},
    },
    "EV-131": {
        "source": "documents",
        "date_field": "signature_date",
        "field_map": {},
    },
    "EV-136": {
        "source": "employees",
        "date_field": "review_date",
        "field_map": {
            "record_id": "performance_review.record_id",
            "review_cycle": "performance_review.review_cycle",
            "self_review_completed": "performance_review.self_review_completed",
            "manager_review_completed": "performance_review.manager_review_completed",
            "review_date": "performance_review.review_date",
            "performance_rating": "performance_review.performance_rating",
            "feedback_provided": "performance_review.feedback_provided",
            "review_status": "performance_review.review_status",
        },
    },
    "EV-137": {
        "source": "employees",
        "date_field": "review_date",
        "field_map": {
            "record_id": "probation_review.record_id",
            "probation_review_required": "probation_review.probation_review_required",
            "probation_review_completed": "probation_review.probation_review_completed",
            "review_date": "probation_review.review_date",
            "evaluation_result": "probation_review.evaluation_result",
            "manager_id": "manager_id",
            "review_status": "probation_review.review_status",
        },
    },
    "EV-140": {
        "source": "policy_ack",
        "date_field": "acknowledgement_date",
        "field_map": {},
    },
    "EV-144": {
        "source": "employees",
        "date_field": "decision_date",
        "field_map": {
            "record_id": "candidate_interview.record_id",
            "candidate_id": "candidate_interview.candidate_id",
            "candidate_name": "candidate_interview.candidate_name",
            "position_applied": "candidate_interview.position_applied",
            "interview_stage": "candidate_interview.interview_stage",
            "interviewer_id": "candidate_interview.interviewer_id",
            "interviewer_name": "candidate_interview.interviewer_name",
            "evaluation_score": "candidate_interview.evaluation_score",
            "feedback": "candidate_interview.feedback",
            "decision": "candidate_interview.decision",
            "decision_date": "candidate_interview.decision_date",
            "hiring_status": "candidate_interview.hiring_status",
        },
    },
    "EV-146": {
        "source": "roles",
        "date_field": "effective_date",
        "field_map": {},
    },
    "EV-160": {
        "source": "policy_ack",
        "date_field": "acknowledgment_date",
        "field_map": {},
    },
    "EV-227": {
        "source": "roles",
        "date_field": "tenure_start_date",
        "field_map": {},
    },
    "EV-230": {
        "source": "roles",
        "field_map": {},
    },
    "EV-292": {
        "source": "trainings",
        "date_field": "completion_date",
        "field_map": {},
    },
    "EV-317": {
        "source": "trainings",
        "date_field": "completion_date",
        "field_map": {},
    },
    "EV-337": {
        "source": "roles",
        "date_field": "appointment_date",
        "field_map": {},
    },
    "EV-402": {
        "source": "roles",
        "date_field": "assigned_date",
        "field_map": {},
    },
    "EV-417": {
        "source": "trainings",
        "date_field": "completion_date",
        "field_map": {},
    },
    "EV-521": {
        "source": "roles",
        "date_field": "last_reviewed_time",
        "field_map": {},
    },
    "EV-564": {
        "source": "employees",
        "field_map": {
            "record_id": "disclosure_check.record_id",
            "references": "disclosure_check.references",
            "contact_number": "disclosure_check.contact_number",
            "relation": "disclosure_check.relation",
            "disclosed_to": "disclosure_check.disclosed_to",
        },
    },
}

_SOURCE_FETCHERS: dict[str, SourceFetcher] = {
    "employees": client.get_employees,
    "terminations": client.get_terminations,
    "trainings": client.get_trainings,
    "background_checks": client.get_background_checks,
    "documents": client.get_documents,
    "roles": client.get_roles,
    "policy_ack": client.get_policy_ack,
}


def _get_path_value(raw_data: dict[str, Any], path: str) -> Any:
    current: Any = raw_data
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
        if current is None:
            return None
    return current


def _coerce_value(field_name: str, value: Any, exemplar: Any) -> Any:
    if value is None:
        return None
    if isinstance(exemplar, bool):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes", "y", "completed", "verified", "active"}
        return bool(value)
    if isinstance(exemplar, list):
        if isinstance(value, list):
            return value
        if value == "":
            return []
        return [value]
    if isinstance(exemplar, int) and not isinstance(exemplar, bool):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    if isinstance(exemplar, float):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    if isinstance(value, (datetime, date)) or any(token in field_name for token in ("date", "time", "day")):
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        return str(value)
    return value


def map_to_evidence(raw_data: dict[str, Any], schema: dict[str, Any], field_map: dict[str, str]) -> dict[str, Any]:
    mapped: dict[str, Any] = {}
    for field_name, exemplar in schema.items():
        source_path = field_map.get(field_name, field_name)
        raw_value = _get_path_value(raw_data, source_path)
        mapped[field_name] = _coerce_value(field_name, raw_value, exemplar)
    return mapped


def _within_date_range(value: str | None, date_from: str | None, date_to: str | None) -> bool:
    if not value:
        return True
    target = str(value)[:10]
    if date_from and target < date_from:
        return False
    if date_to and target > date_to:
        return False
    return True


def fetch_source_records(
    source: str,
    configuration_data: dict[str, Any],
    *,
    source_cache: dict[str, list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    cache = source_cache if source_cache is not None else {}
    if source in cache:
        return cache[source]
    fetcher = _SOURCE_FETCHERS.get(source)
    if fetcher is None:
        raise ValueError(f"No Darwinbox mock fetcher registered for source={source!r}")
    records = fetcher(configuration_data)
    cache[source] = records
    return records


def collect_for_master(
    master: dict[str, Any],
    configuration_data: dict[str, Any],
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    source_cache: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    code = str(master["code"])
    schema_row = CODE_TO_SCHEMA.get(code)
    mapping = DARWINBOX_MAPPING_CONFIG.get(code)
    if schema_row is None or mapping is None:
        raise ValueError(f"No Darwinbox schema mapping registered for evidence_masters.code={code!r}")

    source = mapping["source"]
    field_map = mapping.get("field_map", {})
    date_field = mapping.get("date_field")
    raw_records = fetch_source_records(source, configuration_data, source_cache=source_cache)

    rows = [
        map_to_evidence(raw_record, schema_row["required_fields"], field_map)
        for raw_record in raw_records
        if _within_date_range(
            _get_path_value(raw_record, date_field) if isinstance(date_field, str) else None,
            date_from,
            date_to,
        )
    ]
    return {
        "source": "darwinbox",
        "source_name": source,
        "evidence_code": code,
        "schema_fields": list(schema_row["required_fields"].keys()),
        "records": rows,
        "record_count": len(rows),
    }


def darwinbox_evidence_for_tool_storage(content: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": "darwinbox",
        "source_name": content["source_name"],
        "evidence_code": content["evidence_code"],
        "schema_fields": content["schema_fields"],
        "record_count": content["record_count"],
        "records": content["records"],
    }
