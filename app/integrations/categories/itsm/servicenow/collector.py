"""Generic ServiceNow evidence collector using schema-driven mapping."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable

from app.integrations.categories.itsm.servicenow import client
from app.integrations.categories.itsm.servicenow.seed import CODE_TO_SCHEMA


SourceFetcher = Callable[[dict[str, Any]], list[dict[str, Any]]]

_SOURCE_FETCHERS: dict[str, SourceFetcher] = {
    "incidents": client.get_incidents,
    "changes": client.get_changes,
    "problems": client.get_problems,
    "requests": client.get_requests,
    "tasks": client.get_tasks,
    "users": client.get_users,
    "assets": client.get_assets,
}

_SOURCE_FIELD_ALIASES: dict[str, dict[str, str]] = {
    "incidents": {
        "ticket_id": "number",
        "incident_id": "u_incident_id",
        "incident_title": "short_description",
        "incident_description": "description",
        "incident_category": "category",
        "severity": "severity",
        "incident_severity": "u_incident_severity",
        "status": "state",
        "reported_time": "opened_at",
        "detected_time": "u_detected_time",
        "failure_detected_time": "u_failure_detected_time",
        "resolution_time": "resolved_at",
        "resolved_time": "resolved_at",
        "closure_time": "closed_at",
        "assigned_to": "assigned_to",
        "root_cause": "u_root_cause",
        "resolution_details": "close_notes",
        "resolution_summary": "close_notes",
        "resolved": "u_resolved",
        "created_time": "sys_created_on",
        "last_updated_time": "sys_updated_on",
        "alert_id": "u_alert_id",
        "event_id": "u_event_id",
        "alert_type": "u_alert_type",
        "investigation_status": "u_investigation_status",
        "investigation_details": "u_investigation_details",
        "triage_decision": "u_triage_decision",
        "escalated": "u_escalated",
        "impact": "u_impact",
        "affected_systems": "u_affected_systems",
        "response_actions": "u_response_actions",
        "containment_actions": "u_containment_actions",
        "eradication_actions": "u_eradication_actions",
        "recovery_actions": "u_recovery_actions",
        "reported_by": "caller_id",
        "root_cause_identified": "u_root_cause_identified",
        "investigation_summary": "u_investigation_summary",
        "remediation_required": "u_remediation_required",
        "ai_system_id": "u_ai_system_id",
        "ai_system_name": "u_ai_system_name",
        "investigation_started": "u_investigation_started",
        "remediation_action": "u_remediation_action",
        "user_id": "u_user_id",
        "user_identifier": "u_user_identifier",
        "remediation_status": "u_resolution_status",
        "threat_reference": "u_threat_reference",
        "investigation_actions": "u_investigation_actions",
        "resolution_actions": "u_resolution_actions",
        "service_name": "u_service_name",
        "notification_type": "u_notification_type",
        "communication_channel": "u_communication_channel",
        "message_summary": "u_message_summary",
        "sent_to": "u_sent_to",
        "acknowledged_status": "u_acknowledged_status",
        "follow_up_required": "u_follow_up_required",
        "misuse_confirmed": "u_misuse_confirmed",
        "system_id": "u_system_id",
        "system_name": "u_system_name",
        "incident_type": "incident_type",
    },
    "changes": {
        "ticket_id": "number",
        "change_id": "u_change_id",
        "change_type": "type",
        "system_id": "u_system_id",
        "system_name": "u_system_name",
        "requested_by": "requested_by",
        "change_description": "description",
        "risk_level": "risk",
        "impact_assessment": "risk_impact_analysis",
        "request_status": "state",
        "status": "state",
        "requested_time": "opened_at",
        "planned_start_time": "start_date",
        "planned_end_time": "end_date",
        "created_time": "sys_created_on",
        "last_updated_time": "sys_updated_on",
        "approval_id": "u_approval_id",
        "approved": "u_approval_status",
        "approver_id": "u_approver_id",
        "approver_role": "u_approver_role",
        "approval_time": "u_approval_time",
        "approval_status": "u_approval_status",
        "segregation_of_duties_verified": "u_pre_deployment_approval",
        "comments": "u_comments",
        "release_id": "u_release_id",
        "pre_deployment_approval": "u_pre_deployment_approval",
        "request_type": "u_request_type",
        "business_justification": "u_business_justification",
        "approval_required": "u_approval_required",
        "change_title": "short_description",
        "approved_by": "u_approved_by",
        "implementation_start_time": "u_implementation_start_time",
        "implementation_status": "u_implementation_status",
        "review_id": "u_review_id",
        "review_date": "u_review_date",
        "reviewed_by": "u_reviewed_by",
        "change_outcome": "u_change_outcome",
        "issues_identified": "u_issues_identified",
        "issue_details": "u_issue_details",
        "compliance_with_process": "u_compliance_with_process",
        "corrective_actions_defined": "u_corrective_actions_defined",
        "next_review_date": "u_next_review_date",
    },
    "problems": {
        "ticket_id": "number",
        "vulnerability_id": "u_vulnerability_id",
        "repository_id": "u_repository_id",
        "application_id": "u_application_id",
        "severity": "severity",
        "status": "state",
        "assigned_to": "assigned_to",
        "remediation_action": "u_remediation_action",
        "due_date": "u_due_date",
        "resolution_date": "resolved_at",
        "resolved": "u_resolved",
        "verified": "u_verified",
        "verification_status": "u_verification_status",
        "created_time": "sys_created_on",
        "last_updated_time": "sys_updated_on",
    },
    "requests": {
        "ticket_id": "number",
        "request_id": "u_request_id",
        "dataset_id": "u_dataset_id",
        "dataset_name": "u_dataset_name",
        "data_classification": "u_data_classification",
        "contains_customer_data": "u_contains_customer_data",
        "approval_required": "u_approval_required",
        "approval_status": "u_approval_status",
        "approved_by": "u_approved_by",
        "requested_by": "opened_by",
        "request_time": "opened_at",
        "approval_time": "u_approval_time",
        "approved_time": "u_approved_time",
        "review_comments": "u_review_comments",
        "record_id": "u_record_id",
        "vendor_id": "u_vendor_id",
        "vendor_name": "u_vendor_name",
        "request_date": "u_request_date",
        "approval_date": "u_approval_date",
        "onboarding_status": "u_onboarding_status",
        "user_id": "u_user_id",
        "user_name": "u_user_name",
        "customer_id": "u_customer_id",
        "customer_name": "u_customer_name",
        "customer_identifier": "u_customer_identifier",
        "ticket_type": "u_ticket_type",
        "issue_category": "u_issue_category",
        "issue_description": "u_issue_description",
        "reported_channel": "u_reported_channel",
        "priority": "priority",
        "status": "state",
        "assigned_to": "u_assigned_to",
        "escalation_required": "u_escalation_required",
        "sla_response_time": "u_sla_response_time",
        "sla_resolution_time": "u_sla_resolution_time",
        "response_time_actual": "u_response_time_actual",
        "resolution_time_actual": "u_resolution_time_actual",
        "system_id": "u_system_id",
        "system_name": "u_system_name",
        "access_type": "u_access_type",
        "requested_role": "u_requested_role",
        "justification": "description",
        "request_status": "state",
        "last_updated_time": "sys_updated_on",
        "approval_id": "u_approval_id",
        "approved": "u_approval_status",
        "approver_id": "u_approver_id",
        "approver_role": "u_approver_role",
        "comments": "u_review_comments",
        "business_justification": "u_business_justification",
        "provisioned": "u_provisioned",
        "provisioning_time": "u_provisioning_time",
        "data_subject_id": "u_data_subject_id",
        "data_subject_name": "u_data_subject_name",
        "request_submission_date": "u_request_submission_date",
        "identity_verified": "u_identity_verified",
        "system_scope": "u_system_scope",
        "processing_status": "u_processing_status",
        "completion_date": "u_completion_date",
        "sla_met": "u_sla_met",
        "requester_id": "u_requester_id",
        "requester_name": "u_requester_name",
        "data_scope": "u_data_scope",
        "purpose": "u_purpose",
        "sanitization_required": "u_sanitization_required",
        "anonymization_required": "u_anonymization_required",
        "data_transfer_allowed": "u_data_transfer_allowed",
        "control_id": "u_control_id",
        "control_name": "u_control_name",
        "appeal_id": "u_appeal_id",
        "data_subject_identifier": "u_data_subject_identifier",
        "original_decision_id": "u_original_decision_id",
        "appeal_reason": "u_appeal_reason",
        "appeal_submission_date": "u_appeal_submission_date",
        "appeal_status": "u_appeal_status",
        "review_outcome": "u_review_outcome",
        "decision_reversed": "u_decision_reversed",
        "response_provided": "u_response_provided",
        "response_date": "u_response_date",
        "resolution_summary": "u_resolution_summary",
        "request_description": "description",
        "sla_due_date": "u_sla_due_date",
        "processing_start_time": "opened_at",
        "processing_end_time": "closed_at",
        "response_type": "u_response_type",
        "data_provided": "u_data_provided",
        "modifications_applied": "u_modifications_applied",
        "response_sent": "u_response_sent",
        "response_method": "u_response_method",
        "compliance_status": "u_compliance_status",
        "complaint_category": "u_feedback_category",
        "complaint_description": "u_feedback_description",
        "submission_date": "u_submission_date",
        "reported_by": "u_reported_by",
        "investigation_started": "u_investigation_started",
        "resolution_status": "u_resolution_status",
        "resolution_details": "u_resolution_details",
        "investigation_summary": "u_investigation_summary",
        "root_cause_identified": "u_root_cause_identified",
        "resolution_action": "u_resolution_action",
        "resolution_date": "u_resolution_date",
        "customer_notified": "u_customer_notified",
        "customer_notification_date": "u_customer_notification_date",
        "customer_satisfaction_status": "u_customer_satisfaction_status",
        "feedback_type": "u_feedback_type",
        "feedback_category": "u_feedback_category",
        "feedback_description": "u_feedback_description",
        "submission_channel": "u_submission_channel",
        "content_id": "u_content_id",
        "content_title": "u_content_title",
        "content_type": "u_content_type",
        "submitted_by": "u_submitted_by",
        "reviewed_by": "u_reviewed_by",
        "review_date": "u_review_date",
        "confidentiality_check_passed": "u_confidentiality_check_passed",
        "publication_date": "u_publication_date",
        "engagement_type": "u_engagement_type",
        "communication_channel": "u_communication_channel",
        "engagement_date": "u_engagement_date",
        "conducted_by": "u_conducted_by",
        "summary": "u_summary",
        "follow_up_required": "u_follow_up_required",
        "next_engagement_date": "u_next_engagement_date",
        "reported_time": "u_reported_time",
        "ai_system_reference": "u_ai_system_reference",
        "resolved_time": "u_resolved_time",
        "reporter_type": "u_reporter_type",
        "concern_category": "u_concern_category",
        "concern_description": "u_concern_description",
        "resolution_time": "u_resolution_time",
        "register_id": "u_record_id",
        "request_received_date": "opened_at",
        "verification_status": "u_approval_status",
        "response_due_date": "u_sla_due_date",
        "resolution_outcome": "u_resolution_status",
        "processing_actions": "u_processing_actions",
        "closure_status": "u_closure_status",
        "closed_time": "closed_at",
        "service_review_id": "u_service_review_id",
        "service_name": "u_service_name",
        "review_type": "u_review_type",
        "review_status": "u_review_status",
        "findings": "u_findings",
        "created_time": "sys_created_on",
    },
    "tasks": {
        "ticket_id": "number",
        "employee_id": "u_employee_id",
        "employee_name": "u_employee_name",
        "system_id": "u_system_id",
        "system_name": "u_system_name",
        "access_type": "u_access_type",
        "revocation_requested_time": "u_revocation_requested_time",
        "revocation_completed_time": "u_revocation_completed_time",
        "revoked": "u_revoked",
        "status": "state",
        "performed_by": "u_performed_by",
        "verified": "u_verified",
        "created_time": "sys_created_on",
        "last_updated_time": "sys_updated_on",
        "incident_id": "u_incident_id",
        "action_id": "u_action_id",
        "action_description": "u_action_description",
        "priority": "priority",
        "assigned_to": "assigned_to",
        "due_date": "due_date",
        "completion_date": "u_completion_date",
        "completed": "u_completed",
        "verification_status": "u_verification_status",
        "user_id": "u_user_id",
        "access_role": "u_access_role",
        "issue_identified": "u_issue_identified",
        "revocation_required": "u_revocation_required",
        "revocation_completed": "u_revocation_completed",
        "revocation_time": "u_revocation_time",
        "resolution_details": "u_resolution_details",
        "control_id": "u_control_id",
        "control_name": "u_control_name",
        "issue_description": "u_issue_description",
        "issue_severity": "u_issue_severity",
        "identified_date": "u_identified_date",
        "control_owner": "u_control_owner",
        "remediation_action": "u_remediation_action",
        "sla_due_date": "u_sla_due_date",
        "remediation_start_time": "u_remediation_start_time",
        "remediation_end_time": "u_remediation_end_time",
        "report_id": "u_report_id",
        "report_name": "u_report_name",
        "reporting_period_start": "u_reporting_period_start",
        "reporting_period_end": "u_reporting_period_end",
        "total_actions_count": "u_total_actions_count",
        "open_actions_count": "u_open_actions_count",
        "in_progress_actions_count": "u_in_progress_actions_count",
        "closed_actions_count": "u_closed_actions_count",
        "overdue_actions_count": "u_overdue_actions_count",
        "high_severity_actions_count": "u_high_severity_actions_count",
        "remediation_progress_tracked": "u_remediation_progress_tracked",
        "requester_id": "u_requester_id",
        "data_type": "u_data_type",
        "disposal_reason": "u_disposal_reason",
        "approval_status": "u_approval_status",
        "approved_by": "u_approved_by",
        "request_date": "u_request_date",
        "execution_status": "u_execution_status",
        "execution_date": "u_execution_date",
        "test_id": "u_test_id",
        "test_description": "u_test_description",
        "scheduled_date": "u_scheduled_date",
        "test_outcome": "u_test_outcome",
        "issues_logged": "u_issues_logged",
        "closure_status": "u_closure_status",
        "closed_time": "closed_at",
        "department": "u_department",
        "issue_type": "u_issue_type",
        "issue_category": "u_issue_category",
        "reported_date": "u_reported_date",
        "reported_channel": "u_reported_channel",
        "investigation_started": "u_investigation_started",
        "resolution_status": "u_resolution_status",
    },
    "users": {
        "record_id": "u_record_id",
        "review_id": "u_review_id",
        "user_id": "sys_id",
        "system_id": "u_system_id",
        "approval_status": "u_approval_status",
        "approved_by": "u_approved_by",
        "approval_date": "u_approval_date",
        "justification": "u_justification",
        "created_time": "sys_created_on",
        "last_updated_time": "sys_updated_on",
    },
    "assets": {
        "ticket_id": "u_ticket_id",
        "asset_id": "u_asset_id",
        "asset_name": "u_asset_name",
        "request_type": "u_request_type",
        "provisioning_status": "u_provisioning_status",
        "approved": "u_approved",
        "requested_by": "u_requested_by",
        "approved_by": "u_approved_by",
        "provisioned_by": "u_provisioned_by",
        "request_time": "u_request_time",
        "approval_time": "u_approval_time",
        "provisioning_time": "u_provisioning_time",
        "created_time": "sys_created_on",
        "last_updated_time": "sys_updated_on",
        "decommission_status": "u_decommission_status",
        "decommission_approved": "u_decommission_approved",
        "decommissioned_by": "u_decommissioned_by",
        "decommission_time": "u_decommission_time",
        "reason": "u_reason",
        "record_id": "u_record_id",
        "sbom_id": "u_sbom_id",
        "component_name": "u_component_name",
        "license_type": "u_license_type",
        "review_date": "u_review_date",
        "reviewed_by": "u_reviewed_by",
        "exception_required": "u_exception_required",
        "approval_status": "u_approval_status",
        "justification": "u_justification",
    },
}

_SOURCE_DATE_FIELDS: dict[str, tuple[str, ...]] = {
    "incidents": ("opened_at", "resolved_at", "closed_at", "u_detected_time", "u_reported_time"),
    "changes": ("opened_at", "start_date", "end_date", "u_review_date", "u_approval_time"),
    "problems": ("opened_at", "resolved_at", "u_due_date"),
    "requests": ("opened_at", "closed_at", "u_request_date", "u_approval_date", "u_response_date"),
    "tasks": ("opened_at", "closed_at", "due_date", "u_execution_date", "u_scheduled_date"),
    "users": ("u_approval_date",),
    "assets": ("u_request_time", "u_approval_time", "u_provisioning_time", "u_review_date"),
}


def _build_mapping_config() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for code, schema_row in CODE_TO_SCHEMA.items():
        source = str(schema_row["source"])
        aliases = _SOURCE_FIELD_ALIASES.get(source, {})
        field_map = {field: aliases.get(field, field) for field in schema_row["required_fields"]}
        out[code] = {
            "source": source,
            "table": schema_row["table"],
            "field_map": field_map,
        }
    return out


SERVICENOW_MAPPING_CONFIG: dict[str, dict[str, Any]] = _build_mapping_config()


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
            return value.strip().lower() in {"true", "1", "yes", "y", "approved", "completed", "resolved", "closed_complete"}
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
    if isinstance(value, (datetime, date)) or any(token in field_name for token in ("date", "time")):
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


def _within_date_range(raw_data: dict[str, Any], source: str, date_from: str | None, date_to: str | None) -> bool:
    if not date_from and not date_to:
        return True
    for candidate_field in _SOURCE_DATE_FIELDS.get(source, ()):
        value = _get_path_value(raw_data, candidate_field)
        if not value:
            continue
        target = str(value)[:10]
        if date_from and target < date_from:
            continue
        if date_to and target > date_to:
            continue
        return True
    return False


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
        raise ValueError(f"No ServiceNow fetcher registered for source={source!r}")
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
    mapping = SERVICENOW_MAPPING_CONFIG.get(code)
    if schema_row is None or mapping is None:
        raise ValueError(f"No ServiceNow schema mapping registered for evidence_masters.code={code!r}")

    source = mapping["source"]
    raw_records = fetch_source_records(source, configuration_data, source_cache=source_cache)
    filtered_raw_records = [
        raw_record
        for raw_record in raw_records
        if _within_date_range(raw_record, source, date_from, date_to)
    ]
    rows = [
        map_to_evidence(raw_record, schema_row["required_fields"], mapping["field_map"])
        for raw_record in filtered_raw_records
    ]
    return {
        "source": "servicenow",
        "source_name": source,
        "table_name": mapping["table"],
        "evidence_code": code,
        "schema_fields": list(schema_row["required_fields"].keys()),
        "raw_records": filtered_raw_records,
        "records": rows,
        "record_count": len(rows),
    }


def servicenow_evidence_for_tool_storage(content: dict[str, Any]) -> list[dict[str, Any]]:
    raw_records = content.get("raw_records")
    if isinstance(raw_records, list):
        return [row for row in raw_records if isinstance(row, dict)]
    return []
