import datetime
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import (
    ControlScenarios,
    Evidence,
    EvidenceCollections,
    EvidenceMappeds,
    ToolIntegrations,
)
from .client import JiraServicedeskClient


EVIDENCEABLE_TYPE_CONTROL = "App\Models\Control"

# Default offboarding request type values when no config is set (readme Section 6)
DEFAULT_OFFBOARDING_REQUEST_TYPES = (
    "Offboarding",
    "Employee Offboarding",
    "Access Removal",
    "User Deprovisioning",
    "Account Disable",
    "Employee Exit",
    "Terminate User Access",
    "Disable Account",
)
DEFAULT_OFFBOARDING_KEYWORDS = (
    "offboard",
    "deprovision",
    "disable",
    "termination",
    "access removal",
    "exit",
    "leaver",
)


def _get_deprovision_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Read admin-configurable deprovision/offboarding identifier from integration config.
    Expected shape: deprovision_identifier: { "field": "requestType", "values": ["Offboarding", ...] }
    Optional: optional_labels: ["offboarding"], correlation_field: "employee_email"
    """
    out = {
        "field": "requestType",
        "values": list(DEFAULT_OFFBOARDING_REQUEST_TYPES),
        "keywords": list(DEFAULT_OFFBOARDING_KEYWORDS),
        "optional_labels": [],
        "correlation_field": "requester_email",
    }
    di = (config or {}).get("deprovision_identifier")
    if isinstance(di, dict):
        if "field" in di:
            out["field"] = str(di["field"])
        if "values" in di and isinstance(di["values"], list):
            out["values"] = [str(v) for v in di["values"]]
        if "keywords" in di and isinstance(di["keywords"], list):
            out["keywords"] = [str(k).lower() for k in di["keywords"]]
    if "optional_labels" in config and isinstance(config["optional_labels"], list):
        out["optional_labels"] = [str(l).lower() for l in config["optional_labels"]]
    if config and config.get("correlation_field"):
        out["correlation_field"] = str(config["correlation_field"])
    return out


def _normalize_request_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract a flat canonical structure from one Jira request (handles JSM API shape).
    Returns: request_key, request_type, summary, created_at, requester_email, labels, custom_fields.
    """
    created_at = None
    created_raw = item.get("created") or item.get("createdDate")
    if isinstance(created_raw, dict):
        created_at = created_raw.get("iso8601") or created_raw.get("epochMillis")
    elif created_raw:
        created_at = created_raw
    if isinstance(created_at, (int, float)):
        try:
            created_at = datetime.datetime.utcfromtimestamp(
                created_at / 1000.0 if created_at > 1e12 else created_at
            ).isoformat()
        except (OSError, ValueError):
            created_at = str(created_at)
    elif created_at and not isinstance(created_at, str):
        created_at = str(created_at)

    request_type = ""
    rt = item.get("requestType") or item.get("requestTypeField")
    if isinstance(rt, dict):
        request_type = (rt.get("name") or rt.get("value") or "").strip()
    else:
        request_type = (rt or "").strip()

    reporter = item.get("reporter") or item.get("raiseOnBehalfOf") or {}
    requester_email = ""
    if isinstance(reporter, dict):
        requester_email = (reporter.get("emailAddress") or reporter.get("email") or "").strip()
    else:
        requester_email = str(reporter).strip()

    summary = (item.get("summary") or item.get("subject") or "").strip()
    request_key = (item.get("issueKey") or item.get("issueId") or item.get("id") or "").strip()
    labels = item.get("labels") or []
    if not isinstance(labels, list):
        labels = [labels] if labels else []
    labels = [str(l).lower() for l in labels]

    return {
        "request_key": request_key,
        "request_type": request_type,
        "summary": summary,
        "created_at": created_at,
        "requester_email": requester_email,
        "labels": labels,
        "custom_fields": {k: v for k, v in item.items() if k not in ("requestType", "requestTypeField", "created", "createdDate", "reporter", "raiseOnBehalfOf", "summary", "subject", "issueKey", "issueId", "id", "labels") and isinstance(k, str)},
    }


def _classify_offboarding(
    requests_payload: Dict[str, Any],
    deprovision_config: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    From Jira customer requests API response, build list of normalized request items
    and mark which are offboarding (by request_type in values, or keyword in summary, or labels).
    Returns list of normalized items with is_offboarding=True for those that match.
    """
    values = requests_payload.get("values") or requests_payload.get("requests") or []
    if not isinstance(values, list):
        values = [values]
    field = (deprovision_config.get("field") or "requestType").lower()
    allowed_values = [v.lower() for v in (deprovision_config.get("values") or [])]
    keywords = [k.lower() for k in (deprovision_config.get("keywords") or [])]
    optional_labels = [l.lower() for l in (deprovision_config.get("optional_labels") or [])]

    classified: List[Dict[str, Any]] = []
    for item in values:
        if not isinstance(item, dict):
            continue
        norm = _normalize_request_item(item)
        norm["is_offboarding"] = False
        # Match by request type
        rt_lower = (norm.get("request_type") or "").lower()
        if rt_lower in allowed_values:
            norm["is_offboarding"] = True
        # Match by keyword in summary
        if not norm["is_offboarding"] and keywords:
            summary_lower = (norm.get("summary") or "").lower()
            if any(kw in summary_lower for kw in keywords):
                norm["is_offboarding"] = True
        # Match by label
        if not norm["is_offboarding"] and optional_labels:
            if any(lbl in (norm.get("labels") or []) for lbl in optional_labels):
                norm["is_offboarding"] = True
        classified.append(norm)
    return classified


async def collect_and_persist_evidence(
    db: Session,
    integration: ToolIntegrations,
    access_token: str,
) -> None:
    """
    - Get cloud_id from integration config
    - Fetch Service Desks and Customer Requests from JSM
    - Create Evidence rows ("Service Desks", "Customer Requests")
    - Create EvidenceCollections with raw API payloads
    - Map to controls via ControlScenarios -> EvidenceMappeds
    """
    config = integration.configuration_data or {}
    client_id = config.get("client_id")
    client_secret = config.get("client_secret")
    redirect_uri = config.get("redirect_uri")
    cloud_id = config.get("cloud_id")

    if not cloud_id:
        raise ValueError("cloud_id missing in integration configuration_data")

    jira_client = JiraServicedeskClient(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
    )

    servicedesk_data = await jira_client.fetch_servicedesks(cloud_id, access_token)
    requests_data = await jira_client.fetch_customer_requests(cloud_id, access_token)

    deprovision_config = _get_deprovision_config(config)
    classified = _classify_offboarding(requests_data, deprovision_config)
    offboarding_only = [c for c in classified if c.get("is_offboarding")]
    # Merge classified list into Customer Requests payload for downstream evaluation
    if not isinstance(requests_data, dict):
        requests_payload = {"values": [], "classified_offboarding": offboarding_only, "classified_requests": classified}
    else:
        requests_payload = dict(requests_data)
        requests_payload["classified_offboarding"] = offboarding_only
        requests_payload["classified_requests"] = classified

    today = datetime.date.today()
    due_date = today + datetime.timedelta(days=10)

    evidence_items = {
        "Service Desks": {
            "tool_payload": servicedesk_data,
            "title": "Jira Service Management - Service Desks",
        },
        "Customer Requests": {
            "tool_payload": requests_payload,
            "title": "Jira Service Management - Customer Requests",
        },
        "Offboarding Requests": {
            "tool_payload": {
                "classified_offboarding": offboarding_only,
                "classified_requests": classified,
                "deprovision_config_used": deprovision_config,
            },
            "title": "Jira Service Management - Offboarding Requests",
        },
    }

    for evidence_name, info in evidence_items.items():
        evidence = Evidence(
            id=uuid.uuid4(),
            organization_id=integration.organization_id,
            tool_id=integration.tool_id,
            title=info["title"],
            description=f"Evidence collected from Jira Service Management - {evidence_name}",
            due_date=due_date,
            status="active",
            created_at=datetime.datetime.utcnow(),
        )
        db.add(evidence)
        db.flush()

        collection = EvidenceCollections(
            id=uuid.uuid4(),
            evidence_id=evidence.id,
            evidence_from="integration",
            source="Jira Service Management",
            name=evidence_name,
            tool_evidence=info["tool_payload"],
            created_at=datetime.datetime.utcnow(),
        )
        db.add(collection)

        _map_evidence_to_controls(
            db=db,
            evidence=evidence,
            tool_id=integration.tool_id,
            evidence_name=evidence_name,
            mapped_by=str(integration.user_id),
        )


def _map_evidence_to_controls(
    db: Session,
    evidence: Evidence,
    tool_id: uuid.UUID,
    evidence_name: str,
    mapped_by: str,
) -> None:
    """
    Find ControlScenarios for this tool_id and evidence_name (case-insensitive).
    For each, upsert EvidenceMappeds (one per evidence_id + evidenceable_id).
    """
    now = datetime.datetime.utcnow()
    stmt = (
        select(ControlScenarios)
        .where(ControlScenarios.tool_id == tool_id)
        .where(func.lower(ControlScenarios.evidence_name) == evidence_name.lower())
    )
    scenarios = db.scalars(stmt).all()

    for scenario in scenarios:
        existing = db.scalars(
            select(EvidenceMappeds).where(
                EvidenceMappeds.evidence_id == evidence.id,
                EvidenceMappeds.evidenceable_type == EVIDENCEABLE_TYPE_CONTROL,
                EvidenceMappeds.evidenceable_id == scenario.control_id,
            )
        ).first()

        if existing:
            existing.mapped_by = mapped_by
            existing.updated_at = now
        else:
            mapping = EvidenceMappeds(
                id=uuid.uuid4(),
                evidence_id=evidence.id,
                evidenceable_type=EVIDENCEABLE_TYPE_CONTROL,
                evidenceable_id=scenario.control_id,
                mapped_by=mapped_by,
                created_at=now,
                updated_at=now,
            )
            db.add(mapping)
