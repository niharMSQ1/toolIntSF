"""SCIM User resources → IAMIdentity."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.idp.common_iam_schema import IAMIdentity


def scim_user_to_identity(raw: dict[str, Any]) -> IAMIdentity:
    uid = str(raw.get("id") or "")
    uname = None
    email = None
    active = raw.get("active")
    if isinstance(raw.get("userName"), str):
        uname = raw["userName"]
    emails = raw.get("emails")
    if isinstance(emails, list) and emails:
        e0 = emails[0]
        if isinstance(e0, dict) and e0.get("value"):
            email = str(e0["value"])
    return IAMIdentity(
        id=uid,
        username=uname,
        email=email,
        enabled=bool(active) if isinstance(active, bool) else None,
        provider="cyberark_identity",
        raw=raw,
    )


def extract_scim_users(body: Any) -> list[dict[str, Any]]:
    if isinstance(body, dict):
        res = body.get("Resources")
        if isinstance(res, list):
            return [x for x in res if isinstance(x, dict)]
    if isinstance(body, list):
        return [x for x in body if isinstance(x, dict)]
    return []
