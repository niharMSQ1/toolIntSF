"""Resolve Atlassian cloud ID (Jira site) after OAuth."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.integrations.categories.itsm.jira import api_client
from app.integrations.categories.itsm.jira.credentials import resolve_access_token, resolve_cloud_id
from app.integrations.core.persistence import tool_integration_service as persistence


def ensure_cloud_id_in_config(session: Session, row: dict[str, Any]) -> dict[str, Any]:
    """If atlassian_cloud_id is missing, fetch accessible resources and persist the first Jira site."""
    cfg = dict(row["configuration_data"] or {})
    if not isinstance(cfg, dict):
        cfg = {}
    if resolve_cloud_id(cfg):
        return cfg
    token = resolve_access_token(cfg)
    if not token:
        raise ValueError("Missing access_token; complete OAuth first.")
    resources = api_client.list_accessible_resources(token)
    cid, site_url = api_client.pick_jira_cloud_id(resources)
    if not cid:
        raise ValueError(
            "Could not determine Jira Cloud site from accessible resources; "
            "ensure the OAuth app has Jira scopes and the user can access a Jira Cloud product."
        )
    new_cfg = dict(cfg)
    new_cfg["atlassian_cloud_id"] = cid
    if site_url:
        new_cfg["atlassian_site_url"] = site_url
    new_cfg["atlassian_accessible_resources"] = resources[:25]
    persistence.save_tool_integration_config(session, row["id"], new_cfg)
    return new_cfg
