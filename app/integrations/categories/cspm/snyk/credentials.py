"""Snyk auth: API key, access token (90d), or OAuth 2.0 client credentials — plus org/group scope."""

from __future__ import annotations

from typing import Any

# configuration_data["auth_type"] (optional; inferred if omitted)
AUTH_TYPE_API_KEY = "api_key"
AUTH_TYPE_ACCESS_TOKEN = "access_token"
AUTH_TYPE_OAUTH2 = "oauth2_client_credentials"


def _static_token(cfg: dict[str, Any]) -> str | None:
    for k in ("snyk_api_token", "api_token", "token"):
        v = cfg.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()
    return None


def resolve_oauth_client_id(cfg: dict[str, Any]) -> str | None:
    for k in ("oauth_client_id", "client_id"):
        v = cfg.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()
    return None


def resolve_oauth_client_secret(cfg: dict[str, Any]) -> str | None:
    for k in ("oauth_client_secret", "client_secret"):
        v = cfg.get(k)
        if v is not None and str(v).strip():
            return str(v).strip()
    return None


def oauth_client_credentials_present(cfg: dict[str, Any]) -> bool:
    return bool(resolve_oauth_client_id(cfg) and resolve_oauth_client_secret(cfg))


def resolve_auth_type(cfg: dict[str, Any]) -> str:
    """How to authenticate: static token (api_key / access_token) or OAuth client_credentials."""
    raw = cfg.get("auth_type") or cfg.get("snyk_auth_type")
    if raw is not None and str(raw).strip():
        s = str(raw).strip().lower().replace("-", "_")
        if s in ("oauth2", "oauth2_client_credentials", "oauth", "client_credentials"):
            return AUTH_TYPE_OAUTH2
        if s in ("access_token", "accesstoken"):
            return AUTH_TYPE_ACCESS_TOKEN
        if s in ("api_key", "apikey"):
            return AUTH_TYPE_API_KEY
    if oauth_client_credentials_present(cfg):
        return AUTH_TYPE_OAUTH2
    return AUTH_TYPE_API_KEY


def has_api_token(cfg: dict[str, Any]) -> bool:
    """True if a static API token / access token string is present (not OAuth-only)."""
    return _static_token(cfg) is not None


def resolve_api_token(cfg: dict[str, Any]) -> str | None:
    return _static_token(cfg)


def has_credentials_for_api(cfg: dict[str, Any]) -> bool:
    """Enough config to obtain an access token for API calls."""
    if resolve_auth_type(cfg) == AUTH_TYPE_OAUTH2:
        if cfg.get("oauth_access_token") and str(cfg["oauth_access_token"]).strip():
            return True
        return oauth_client_credentials_present(cfg)
    return has_api_token(cfg)


def resolve_org_ids(cfg: dict[str, Any]) -> list[str]:
    raw = cfg.get("org_ids")
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if x is not None and str(x).strip()]
    one = cfg.get("org_id")
    if one is not None and str(one).strip():
        return [str(one).strip()]
    return []


def resolve_group_id(cfg: dict[str, Any]) -> str | None:
    g = cfg.get("group_id")
    if g is None or not str(g).strip():
        return None
    return str(g).strip()


def ready_for_collection(cfg: dict[str, Any]) -> bool:
    if not has_credentials_for_api(cfg):
        return False
    if resolve_group_id(cfg):
        return True
    return bool(resolve_org_ids(cfg))


def rest_authorization_header(cfg: dict[str, Any]) -> str:
    """Authorization header value for REST + v1 (token vs Bearer)."""
    if resolve_auth_type(cfg) == AUTH_TYPE_OAUTH2:
        t = cfg.get("oauth_access_token")
        if not t or not str(t).strip():
            raise ValueError("Missing oauth_access_token; configure OAuth or refresh token.")
        return f"Bearer {str(t).strip()}"
    tok = resolve_api_token(cfg)
    if not tok:
        raise ValueError("Missing snyk_api_token (or api_token / token).")
    return f"token {tok}"
