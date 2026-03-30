"""Azure DevOps: PAT + organization (and optional project) in configuration_data."""

from __future__ import annotations

import base64
from typing import Any


def resolve_pat(cfg: dict[str, Any]) -> str | None:
    for key in ("personal_access_token", "pat", "azure_devops_token", "access_token", "token"):
        t = cfg.get(key)
        if t and str(t).strip():
            return str(t).strip()
    return None


def has_pat(cfg: dict[str, Any]) -> bool:
    return bool(resolve_pat(cfg))


def resolve_organization(cfg: dict[str, Any]) -> str:
    org = cfg.get("organization") or cfg.get("org") or cfg.get("azure_devops_organization")
    if not org or not str(org).strip():
        raise ValueError("Missing organization in configuration_data (Azure DevOps org name).")
    return str(org).strip()


def resolve_project(cfg: dict[str, Any]) -> str | None:
    p = cfg.get("project") or cfg.get("project_name")
    if p and str(p).strip():
        return str(p).strip()
    return None


def resolve_base_url(cfg: dict[str, Any]) -> str:
    u = cfg.get("base_url") or cfg.get("azure_devops_base_url")
    if u and str(u).strip():
        return str(u).strip().rstrip("/")
    from app.integrations.categories.devtools.azure_devops.constants import DEFAULT_AZURE_DEVOPS_BASE

    return DEFAULT_AZURE_DEVOPS_BASE


def resolve_api_version(cfg: dict[str, Any]) -> str:
    v = cfg.get("api_version") or cfg.get("azure_devops_api_version")
    if v and str(v).strip():
        return str(v).strip()
    from app.integrations.categories.devtools.azure_devops.constants import DEFAULT_API_VERSION

    return DEFAULT_API_VERSION


def basic_auth_header(pat: str) -> str:
    """PAT as password with empty user — https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate"""
    raw = f":{pat}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def ready_for_api_calls(cfg: dict[str, Any]) -> bool:
    try:
        resolve_organization(cfg)
    except ValueError:
        return False
    return has_pat(cfg)
