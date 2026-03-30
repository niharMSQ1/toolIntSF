"""ForgeRock OpenIDM / AM user JSON → IAMIdentity."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.idp.common_iam_schema import IAMIdentity


def forgerock_user_to_iam(raw: dict[str, Any]) -> IAMIdentity:
    uid = str(raw.get("_id") or raw.get("id") or raw.get("uuid") or "")
    uname = raw.get("userName") or raw.get("username")
    email = raw.get("mail") or raw.get("email")
    if isinstance(uname, str):
        pass
    else:
        uname = str(uname) if uname is not None else None
    if email is not None and not isinstance(email, str):
        email = str(email) if email else None
    return IAMIdentity(
        id=uid,
        username=uname,
        email=email,
        enabled=None,
        provider="forgerock",
        raw=raw,
    )


def extract_forgerock_users(body: Any) -> list[dict[str, Any]]:
    if isinstance(body, dict):
        res = body.get("result")
        if isinstance(res, list):
            return [x for x in res if isinstance(x, dict)]
        # Some deployments return Resources (SCIM-like)
        alt = body.get("Resources")
        if isinstance(alt, list):
            return [x for x in alt if isinstance(x, dict)]
    if isinstance(body, list):
        return [x for x in body if isinstance(x, dict)]
    return []
