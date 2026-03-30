"""CyberArk Identity — tenant base URL and OAuth client (see CyberArk Identity developer docs)."""

from __future__ import annotations

from typing import Any


def resolve_identity_base_url(cfg: dict[str, Any]) -> str:
    u = cfg.get("cyberark_identity_base_url") or cfg.get("identity_base_url")
    if not u or not str(u).strip():
        raise ValueError(
            "Missing cyberark_identity_base_url (tenant origin, e.g. https://<subdomain>.identity.cyberark.cloud).",
        )
    return str(u).strip().rstrip("/")


def resolve_oauth_client(cfg: dict[str, Any]) -> tuple[str, str]:
    cid = cfg.get("client_id") or cfg.get("cyberark_client_id")
    sec = cfg.get("client_secret") or cfg.get("cyberark_client_secret")
    if not cid or not str(cid).strip():
        raise ValueError("Missing client_id for CyberArk Identity OAuth 2.0.")
    if not sec or not str(sec).strip():
        raise ValueError("Missing client_secret for CyberArk Identity OAuth 2.0.")
    return str(cid).strip(), str(sec).strip()


def resolve_access_token(cfg: dict[str, Any]) -> str | None:
    t = cfg.get("access_token")
    if t and str(t).strip():
        return str(t).strip()
    return None


def has_access_token(cfg: dict[str, Any]) -> bool:
    return bool(resolve_access_token(cfg))


def has_oauth_client(cfg: dict[str, Any]) -> bool:
    try:
        resolve_oauth_client(cfg)
        return True
    except ValueError:
        return False


def resolve_oauth_scope(cfg: dict[str, Any]) -> str | None:
    s = cfg.get("oauth_scope") or cfg.get("scope")
    if s and str(s).strip():
        return str(s).strip()
    return None


def ready_for_collection(cfg: dict[str, Any]) -> bool:
    if not isinstance(cfg, dict):
        return False
    try:
        resolve_identity_base_url(cfg)
    except ValueError:
        return False
    return has_oauth_client(cfg) or has_access_token(cfg)
