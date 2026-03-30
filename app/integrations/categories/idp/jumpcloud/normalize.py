"""JumpCloud system user → IAMIdentity."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.idp.common_iam_schema import IAMIdentity


def jumpcloud_user_to_iam(raw: dict[str, Any]) -> IAMIdentity:
    uid = str(raw.get("_id") or raw.get("id") or "")
    uname = raw.get("username")
    email = raw.get("email")
    if uname is not None and not isinstance(uname, str):
        uname = str(uname)
    if email is not None and not isinstance(email, str):
        email = str(email) if email else None
    return IAMIdentity(
        id=uid,
        username=uname,
        email=email,
        enabled=raw.get("account_locked") is False if "account_locked" in raw else None,
        provider="jumpcloud",
        raw=raw,
    )


def extract_jumpcloud_users(body: Any) -> list[dict[str, Any]]:
    if isinstance(body, list):
        return [x for x in body if isinstance(x, dict)]
    return []
