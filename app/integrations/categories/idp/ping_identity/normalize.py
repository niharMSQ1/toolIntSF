"""Map PingOne Management API JSON into common_iam_schema models."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.idp.common_iam_schema import IAMApplication, IAMAuditEvent, IAMGroup, IAMIdentity


def _embedded_list(body: Any, key: str) -> list[dict[str, Any]]:
    if not isinstance(body, dict):
        return []
    emb = body.get("_embedded")
    if not isinstance(emb, dict):
        return []
    chunk = emb.get(key)
    if isinstance(chunk, list):
        return [x for x in chunk if isinstance(x, dict)]
    return []


def ping_user_to_identity(raw: dict[str, Any]) -> IAMIdentity:
    uid = str(raw.get("id") or "")
    email = None
    em = raw.get("email")
    if isinstance(em, dict):
        email = str(em.get("address")) if em.get("address") else None
    elif isinstance(em, str):
        email = em
    uname = raw.get("username")
    return IAMIdentity(
        id=uid,
        username=str(uname) if uname is not None else None,
        email=email,
        enabled=raw.get("enabled") if isinstance(raw.get("enabled"), bool) else None,
        provider="ping_identity",
        raw=raw,
    )


def ping_population_to_group(raw: dict[str, Any]) -> IAMGroup:
    return IAMGroup(
        id=str(raw.get("id") or ""),
        name=str(raw.get("name")) if raw.get("name") is not None else None,
        provider="ping_identity",
        raw=raw,
    )


def ping_application_to_app(raw: dict[str, Any]) -> IAMApplication:
    return IAMApplication(
        id=str(raw.get("id") or ""),
        name=str(raw.get("name")) if raw.get("name") is not None else None,
        enabled=raw.get("enabled") if isinstance(raw.get("enabled"), bool) else None,
        provider="ping_identity",
        raw=raw,
    )


def ping_activity_to_event(raw: dict[str, Any]) -> IAMAuditEvent:
    return IAMAuditEvent(
        id=str(raw.get("id")) if raw.get("id") is not None else None,
        recorded_at=str(raw.get("recordedAt")) if isinstance(raw.get("recordedAt"), str) else None,
        action_type=str(raw.get("type")) if raw.get("type") is not None else None,
        provider="ping_identity",
        raw=raw,
    )


def extract_users(body: Any) -> list[dict[str, Any]]:
    users = _embedded_list(body, "users")
    if users:
        return users
    if isinstance(body, dict) and isinstance(body.get("_embedded"), dict):
        # Some responses nest under a single key
        for v in body["_embedded"].values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return [x for x in v if isinstance(x, dict)]
    return []


def extract_populations(body: Any) -> list[dict[str, Any]]:
    return _embedded_list(body, "populations")


def extract_applications(body: Any) -> list[dict[str, Any]]:
    return _embedded_list(body, "applications")


def extract_activities(body: Any) -> list[dict[str, Any]]:
    return _embedded_list(body, "activities")
