"""IAM catalog + PingOne Management API path hints (verified paths only; see README for gaps)."""

from __future__ import annotations

from app.integrations.categories.idp.iam_evidence_catalog import (
    ALL_IAM_EVIDENCE_CODES,
    EVIDENCE_MASTER_NAME_ORDER,
    IAM_EVIDENCE_SEED_ROWS,
)

# Verified in PingOne Platform API reference: Management API under api.pingone.{tld}/v1
_VERIFIED = "/v1/environments/{envID}/users | /populations | /applications | /activities (filtered)"

_PING_API_BY_CODE: dict[str, str] = {
    "EV-37": "/v1/environments/{envID}/users",
    "EV-39": "/v1/environments/{envID}/populations; /v1/environments/{envID}/applications",
    "EV-40": "/v1/environments/{envID}/users",
    "EV-75": "/v1/environments/{envID}/populations; /v1/environments/{envID}/applications",
    "EV-77": f"PingOne password policy resources ({_VERIFIED})",
    "EV-78": "PingOne sign-on policy resources (see PingOne Platform APIs — Sign-On Policies)",
    "EV-126": "/v1/environments/{envID}/applications",
    "EV-127": "/v1/environments/{envID}/activities (SCIM filter; date range required per docs)",
    "EV-151": "/v1/environments/{envID}/populations",
    "EV-154": "User MFA / device APIs (product-specific; see PingOne docs)",
    "EV-167": "PingOne policy resources (see PingOne Platform APIs)",
    "EV-189": "/v1/environments/{envID}/activities",
    "EV-207": "/v1/environments/{envID}/applications",
    "EV-461": "PingOne sign-on policy resources (see PingOne Platform APIs)",
    "EV-463": "/v1/environments/{envID}/applications",
    "EV-476": "PingOne sign-on / password policy resources (see PingOne Platform APIs)",
    "EV-522": "/v1/environments/{envID}/populations; /v1/environments/{envID}/applications",
}

PING_IAM_SEED_ROWS: list[dict[str, str]] = [
    {**row, "api": _PING_API_BY_CODE[row["code"]]} for row in IAM_EVIDENCE_SEED_ROWS
]

ALL_PING_IAM_EVIDENCE_CODES = ALL_IAM_EVIDENCE_CODES
