"""OAuth state in `configuration_data.oauth_clients`; app id/secret from env (Vanta-style) or BYO in config."""

from __future__ import annotations

from typing import Any

from app.config import Settings, get_settings
from app.integrations.categories.idp.microsoft_entra.constants import DEFAULT_GRAPH_SCOPES, DEFAULT_GRAPH_SCOPES_GCC_HIGH
from app.integrations.categories.idp.microsoft_entra.national_cloud import NationalCloud, default_graph_base_url, parse_national_cloud

OAUTH_CLIENTS_KEY = "oauth_clients"
_NATIONAL_CLOUD_KEY = "national_cloud"


def resolve_national_cloud(cfg: dict[str, Any]) -> NationalCloud:
    clients = cfg.get(OAUTH_CLIENTS_KEY)
    if isinstance(clients, list) and clients:
        last = clients[-1]
        if isinstance(last, dict) and last.get(_NATIONAL_CLOUD_KEY):
            return parse_national_cloud(str(last[_NATIONAL_CLOUD_KEY]))
    raw = cfg.get(_NATIONAL_CLOUD_KEY)
    if raw is not None:
        return parse_national_cloud(str(raw))
    return NationalCloud.COMMERCIAL


def _settings_client_pair(settings: Settings, cloud: NationalCloud) -> tuple[str | None, str | None]:
    if cloud == NationalCloud.GCC_HIGH:
        return (settings.entra_gcc_high_client_id, settings.entra_gcc_high_client_secret)
    return (settings.entra_client_id, settings.entra_client_secret)


def _settings_default_redirect(settings: Settings, cloud: NationalCloud) -> str | None:
    if cloud == NationalCloud.GCC_HIGH:
        return settings.entra_gcc_high_redirect_uri
    return settings.entra_redirect_uri


def default_redirect_from_settings(settings: Settings, cloud: NationalCloud) -> str | None:
    """Public helper for configure: default redirect from env for this cloud."""
    return _settings_default_redirect(settings, cloud)


def resolve_active_oauth_entry(cfg: dict[str, Any]) -> dict[str, Any]:
    clients = cfg.get(OAUTH_CLIENTS_KEY)
    if isinstance(clients, list) and clients:
        last = clients[-1]
        if isinstance(last, dict) and last:
            return last
    cid, sec = cfg.get("client_id"), cfg.get("client_secret")
    if cid is not None and str(cid).strip():
        return {
            "client_id": str(cid),
            "client_secret": sec if sec is not None else "",
            "redirect_uri": str(cfg.get("redirect_uri", "")),
            "tenant_id": str(cfg.get("tenant_id", "common")),
            _NATIONAL_CLOUD_KEY: str(cfg.get(_NATIONAL_CLOUD_KEY, "commercial")),
        }
    # Shell row: tenant + cloud + optional redirect (client id/secret from env)
    if (
        cfg.get("tenant_id") is not None
        or cfg.get(_NATIONAL_CLOUD_KEY) is not None
        or cfg.get("redirect_uri")
        or cfg.get(OAUTH_CLIENTS_KEY) is not None
    ):
        return {
            "client_id": str(cfg.get("client_id") or ""),
            "client_secret": str(cfg.get("client_secret") or "") if cfg.get("client_secret") is not None else "",
            "redirect_uri": str(cfg.get("redirect_uri", "")),
            "tenant_id": str(cfg.get("tenant_id", "common")),
            _NATIONAL_CLOUD_KEY: str(cfg.get(_NATIONAL_CLOUD_KEY, "commercial")),
        }
    raise ValueError("Missing oauth_clients or tenant/configuration for Microsoft Entra integration")


def resolve_oauth_application_credentials(
    cfg: dict[str, Any],
    *,
    settings: Settings | None = None,
    cloud: NationalCloud | None = None,
) -> tuple[str, str]:
    """Returns (client_id, client_secret). Env wins unless BYO client_id+secret in configuration_data."""
    s = settings or get_settings()
    cloud = cloud or resolve_national_cloud(cfg)
    env_cid, env_sec = _settings_client_pair(s, cloud)

    try:
        e = resolve_active_oauth_entry(cfg)
    except ValueError:
        e = {}

    cid = (e.get("client_id") if isinstance(e, dict) else None) or env_cid
    sec_raw = e.get("client_secret") if isinstance(e, dict) else None
    if sec_raw is not None and str(sec_raw) != "":
        sec = str(sec_raw)
    else:
        sec = env_sec or ""

    if not cid or not str(cid).strip():
        raise ValueError(
            "Missing Entra client_id: set ENTRA_CLIENT_ID (commercial) or ENTRA_GCC_HIGH_CLIENT_ID (GCC High), "
            "or pass client_id in configuration_data."
        )
    if not sec or not str(sec).strip():
        raise ValueError(
            "Missing Entra client_secret: set ENTRA_CLIENT_SECRET or ENTRA_GCC_HIGH_CLIENT_SECRET, "
            "or pass client_secret in configuration_data."
        )
    return str(cid).strip(), str(sec).strip()


def resolve_redirect_uri(cfg: dict[str, Any], *, settings: Settings | None = None, cloud: NationalCloud | None = None) -> str:
    s = settings or get_settings()
    cloud = cloud or resolve_national_cloud(cfg)
    try:
        e = resolve_active_oauth_entry(cfg)
    except ValueError:
        e = {}
    u = e.get("redirect_uri") if isinstance(e, dict) else None
    if u and str(u).strip():
        return str(u).strip()
    u2 = cfg.get("redirect_uri")
    if u2 and str(u2).strip():
        return str(u2).strip()
    default = _settings_default_redirect(s, cloud)
    if default and str(default).strip():
        return str(default).strip()
    raise ValueError(
        "Missing redirect_uri: set ENTRA_REDIRECT_URI or ENTRA_GCC_HIGH_REDIRECT_URI, "
        "or pass redirect_uri in configuration_data (must match the Entra app registration)."
    )


def resolve_tenant_id(cfg: dict[str, Any]) -> str:
    try:
        e = resolve_active_oauth_entry(cfg)
        t = e.get("tenant_id") if isinstance(e, dict) else None
        if t and str(t).strip():
            return str(t).strip()
    except ValueError:
        pass
    return str(cfg.get("tenant_id") or "common")


def resolve_access_token(cfg: dict[str, Any]) -> str | None:
    try:
        e = resolve_active_oauth_entry(cfg)
    except ValueError:
        return cfg.get("access_token")
    if not isinstance(e, dict):
        return cfg.get("access_token")
    return e.get("access_token") or cfg.get("access_token")


def resolve_refresh_token(cfg: dict[str, Any]) -> str | None:
    try:
        e = resolve_active_oauth_entry(cfg)
    except ValueError:
        return cfg.get("refresh_token")
    if not isinstance(e, dict):
        return cfg.get("refresh_token")
    return e.get("refresh_token") or cfg.get("refresh_token")


def access_token_expires_raw(cfg: dict[str, Any]) -> str | None:
    try:
        e = resolve_active_oauth_entry(cfg)
    except ValueError:
        return cfg.get("access_token_expires_at")
    if not isinstance(e, dict):
        return cfg.get("access_token_expires_at")
    return e.get("access_token_expires_at") or cfg.get("access_token_expires_at")


def resolve_scopes(cfg: dict[str, Any], *, cloud: NationalCloud | None = None) -> str:
    cloud = cloud or resolve_national_cloud(cfg)
    try:
        e = resolve_active_oauth_entry(cfg)
    except ValueError:
        e = {}
    s = e.get("scopes") if isinstance(e, dict) else None
    if not s:
        s = cfg.get("scopes")
    if s and str(s).strip():
        return str(s).strip()
    return DEFAULT_GRAPH_SCOPES_GCC_HIGH if cloud == NationalCloud.GCC_HIGH else DEFAULT_GRAPH_SCOPES


def has_access_token(cfg: dict[str, Any]) -> bool:
    return bool(resolve_access_token(cfg))


def graph_base_url(cfg: dict[str, Any]) -> str:
    cloud = resolve_national_cloud(cfg)
    raw = cfg.get("graph_base_url")
    if raw and str(raw).strip():
        return str(raw).rstrip("/")
    try:
        e = resolve_active_oauth_entry(cfg)
        if isinstance(e, dict):
            g = e.get("graph_base_url")
            if g and str(g).strip():
                return str(g).rstrip("/")
    except ValueError:
        pass
    return default_graph_base_url(cloud)
