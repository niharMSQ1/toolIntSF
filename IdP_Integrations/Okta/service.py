"""
Okta evidence collection: fetch MVP endpoints and persist Evidence + EvidenceCollections + EvidenceMappeds.
"""
import datetime
import uuid
from typing import Any, Dict, List

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import (
    ControlScenarios,
    Evidence,
    EvidenceCollections,
    EvidenceMappeds,
    ToolIntegrations,
)
from .client import OktaClient

EVIDENCEABLE_TYPE_CONTROL = "App\Models\Control"

# Caps to avoid timeouts on large orgs (per-user/per-group/per-app detail calls)
MAX_USERS_FOR_FACTORS_AND_ROLES = 100
MAX_GROUPS_FOR_MEMBERS = 100
MAX_APPS_FOR_ASSIGNMENTS = 50


async def collect_and_persist_evidence(
    db: Session,
    integration: ToolIntegrations,
    access_token: str,
) -> None:
    """
    Collect data from Okta MVP endpoints and persist as Evidence + EvidenceCollections.
    Okta uses API token (no OAuth); access_token is ignored and api_token from config is used.
    """
    config = integration.configuration_data or {}
    org_domain = config.get("org_domain")
    api_token = config.get("api_token")
    if not org_domain or not api_token:
        raise ValueError("org_domain and api_token required in integration configuration_data")

    client = OktaClient(org_domain=org_domain, api_token=api_token)

    # 1. Users
    users = await client.list_users()
    # 2. User factors (MFA) and roles - cap to avoid N+1 explosion
    user_factors_by_id: Dict[str, List[Dict[str, Any]]] = {}
    user_roles_by_id: Dict[str, List[Dict[str, Any]]] = {}
    for i, u in enumerate(users):
        if i >= MAX_USERS_FOR_FACTORS_AND_ROLES:
            break
        uid = (u.get("id") or "").strip()
        if not uid:
            continue
        try:
            user_factors_by_id[uid] = await client.list_user_factors(uid)
        except Exception:
            user_factors_by_id[uid] = []
        try:
            user_roles_by_id[uid] = await client.list_user_roles(uid)
        except Exception:
            user_roles_by_id[uid] = []

    # 3. Groups
    groups = await client.list_groups()
    # 4. Group members - cap
    group_members: Dict[str, List[Dict[str, Any]]] = {}
    for i, g in enumerate(groups):
        if i >= MAX_GROUPS_FOR_MEMBERS:
            break
        gid = (g.get("id") or "").strip()
        if not gid:
            continue
        try:
            group_members[gid] = await client.list_group_users(gid)
        except Exception:
            group_members[gid] = []

    # 5. Apps
    apps = await client.list_apps()
    # 6. App users and 7. App groups - cap
    app_users_map: Dict[str, List[Dict[str, Any]]] = {}
    app_groups_map: Dict[str, List[Dict[str, Any]]] = {}
    for i, app in enumerate(apps):
        if i >= MAX_APPS_FOR_ASSIGNMENTS:
            break
        aid = (app.get("id") or "").strip()
        if not aid:
            continue
        try:
            app_users_map[aid] = await client.list_app_users(aid)
        except Exception:
            app_users_map[aid] = []
        try:
            app_groups_map[aid] = await client.list_app_groups(aid)
        except Exception:
            app_groups_map[aid] = []

    # 8. Logs (one page; optional since from config for incremental)
    logs_since = config.get("logs_since")
    try:
        logs = await client.list_logs(limit=500, since=logs_since)
    except Exception:
        logs = []

    # 9. Policies
    try:
        policies = await client.list_policies()
    except Exception:
        policies = []

    # Build evidence payloads (aligned with MVP evidence names)
    today = datetime.date.today()
    due_date = today + datetime.timedelta(days=10)

    evidence_items: Dict[str, Dict[str, Any]] = {
        "Users": {
            "tool_payload": {"users": users, "count": len(users)},
            "title": "Okta - Users",
        },
        "User Factors (MFA)": {
            "tool_payload": {
                "user_factors": user_factors_by_id,
                "users_sampled": min(len(users), MAX_USERS_FOR_FACTORS_AND_ROLES),
            },
            "title": "Okta - User Factors (MFA)",
        },
        "Groups": {
            "tool_payload": {"groups": groups, "count": len(groups)},
            "title": "Okta - Groups",
        },
        "Group Members": {
            "tool_payload": {
                "group_members": group_members,
                "groups_sampled": min(len(groups), MAX_GROUPS_FOR_MEMBERS),
            },
            "title": "Okta - Group Members",
        },
        "Applications": {
            "tool_payload": {"apps": apps, "count": len(apps)},
            "title": "Okta - Applications",
        },
        "App Users": {
            "tool_payload": {
                "app_users": app_users_map,
                "apps_sampled": min(len(apps), MAX_APPS_FOR_ASSIGNMENTS),
            },
            "title": "Okta - App Users",
        },
        "App Groups": {
            "tool_payload": {
                "app_groups": app_groups_map,
                "apps_sampled": min(len(apps), MAX_APPS_FOR_ASSIGNMENTS),
            },
            "title": "Okta - App Groups",
        },
        "System Logs": {
            "tool_payload": {"logs": logs, "count": len(logs)},
            "title": "Okta - System Logs",
        },
        "Policies": {
            "tool_payload": {"policies": policies, "count": len(policies)},
            "title": "Okta - Policies",
        },
        "User Admin Roles": {
            "tool_payload": {
                "user_roles": user_roles_by_id,
                "users_sampled": min(len(users), MAX_USERS_FOR_FACTORS_AND_ROLES),
            },
            "title": "Okta - User Admin Roles",
        },
    }

    for evidence_name, info in evidence_items.items():
        evidence = Evidence(
            id=uuid.uuid4(),
            organization_id=integration.organization_id,
            tool_id=integration.tool_id,
            title=info["title"],
            description=f"Evidence collected from Okta - {evidence_name}",
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
            source="Okta",
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
    """Map evidence to controls via ControlScenarios (evidence_name match)."""
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
