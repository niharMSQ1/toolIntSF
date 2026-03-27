"""Resolve Okta org URL and API token from tool_integrations.configuration_data."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse


def resolve_api_token(cfg: dict[str, Any]) -> str:
    t = cfg.get("api_token")
    if not t or not str(t).strip():
        raise ValueError("Missing api_token in configuration_data (Okta SSWS API token).")
    return str(t).strip()


def resolve_org_domain_raw(cfg: dict[str, Any]) -> str:
    u = cfg.get("org_domain") or cfg.get("okta_org_url") or cfg.get("base_url")
    if not u or not str(u).strip():
        raise ValueError("Missing org_domain in configuration_data (e.g. https://your-org.okta.com/).")
    return str(u).strip()


def resolve_okta_base_url(cfg: dict[str, Any]) -> str:
    """
    Normalize Okta org URL for Admin API calls.

    Accepts e.g. ``https://tenant-admin.okta.com/`` and returns ``https://tenant.okta.com``
    (API host without ``-admin``).
    """
    raw = resolve_org_domain_raw(cfg)
    s = raw.rstrip("/")
    if not s.lower().startswith("http"):
        s = f"https://{s}"
    parsed = urlparse(s)
    host = (parsed.netloc or parsed.path.split("/")[0]).strip()
    if not host:
        raise ValueError("Invalid org_domain; could not parse hostname.")
    if "-admin.okta.com" in host:
        host = host.replace("-admin.okta.com", ".okta.com")
    scheme = parsed.scheme if parsed.scheme in ("http", "https") else "https"
    return f"{scheme}://{host}"


def has_api_token(cfg: dict[str, Any]) -> bool:
    try:
        resolve_api_token(cfg)
    except ValueError:
        return False
    return True


def ready_for_collection(cfg: dict[str, Any]) -> bool:
    if not isinstance(cfg, dict):
        return False
    try:
        resolve_okta_base_url(cfg)
        resolve_api_token(cfg)
    except ValueError:
        return False
    return True
