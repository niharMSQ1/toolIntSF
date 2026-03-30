from __future__ import annotations

from typing import Any

from app.integrations.categories.idp.common_iam_schema import IAMIdentity


def google_user_to_iam(raw: dict[str, Any]) -> IAMIdentity:
    uid = str(raw.get("id") or "")
    return IAMIdentity(
        id=uid,
        username=str(raw.get("primaryEmail")) if raw.get("primaryEmail") else None,
        email=str(raw.get("primaryEmail")) if raw.get("primaryEmail") else None,
        enabled=not raw.get("suspended", False) if "suspended" in raw else None,
        provider="google_workspace",
        raw=raw,
    )


def extract_google_users(body: Any) -> list[dict[str, Any]]:
    if isinstance(body, dict) and isinstance(body.get("users"), list):
        return [x for x in body["users"] if isinstance(x, dict)]
    return []
