"""OneLogin user JSON → IAMIdentity."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.idp.common_iam_schema import IAMIdentity


def onelogin_user_to_iam(raw: dict[str, Any]) -> IAMIdentity:
    uid = str(raw.get("id") or "")
    uname = raw.get("username")
    email = raw.get("email")
    if uname is not None and not isinstance(uname, str):
        uname = str(uname)
    if email is not None and not isinstance(email, str):
        email = str(email) if email else None
    st = raw.get("status")
    enabled = None
    if isinstance(st, (int, float)):
        enabled = int(st) == 1
    return IAMIdentity(
        id=uid,
        username=uname,
        email=email,
        enabled=enabled,
        provider="onelogin",
        raw=raw,
    )


def extract_onelogin_users(body: Any) -> list[dict[str, Any]]:
    if isinstance(body, dict):
        d = body.get("data")
        if isinstance(d, list):
            return [x for x in d if isinstance(x, dict)]
    if isinstance(body, list):
        return [x for x in body if isinstance(x, dict)]
    return []
