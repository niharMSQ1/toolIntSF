"""SailPoint public identity → IAMIdentity."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.idp.common_iam_schema import IAMIdentity


def sailpoint_identity_to_iam(raw: dict[str, Any]) -> IAMIdentity:
    uid = str(raw.get("id") or raw.get("externalId") or "")
    name = raw.get("name")
    email = None
    if isinstance(raw.get("email"), str):
        email = raw["email"]
    elif isinstance(raw.get("attributes"), dict):
        email = raw["attributes"].get("email")
    return IAMIdentity(
        id=uid,
        username=str(name) if isinstance(name, str) else None,
        email=email,
        enabled=True,
        provider="sailpoint_identitynow",
        raw=raw,
    )


def extract_identities(body: Any) -> list[dict[str, Any]]:
    if isinstance(body, list):
        return [x for x in body if isinstance(x, dict)]
    if isinstance(body, dict):
        for key in ("items", "data", "identities", "results"):
            v = body.get(key)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
    return []
