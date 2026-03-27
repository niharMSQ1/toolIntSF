from __future__ import annotations

from app.integrations.categories.idp.iam_evidence_catalog import (
    ALL_IAM_EVIDENCE_CODES,
    EVIDENCE_MASTER_NAME_ORDER,
    IAM_EVIDENCE_SEED_ROWS,
)

# Microsoft Graph path hints (documentation / api_endpoint on evidence_masters).
_ENTRA_GRAPH_API_HINTS: dict[str, str] = {
    "EV-37": "GET /users",
    "EV-39": "GET /directoryRoles (+ members sample)",
    "EV-40": "GET /authenticationMethodsPolicy, /users/{id}/authentication/methods (sample)",
    "EV-75": "GET /groups, identityGovernance/accessReviews/definitions (when permitted)",
    "EV-77": "GET /policies/authenticationMethodsPolicy, identity/conditionalAccess/policies",
    "EV-78": "GET /policies/authenticationMethodsPolicy, /policies/authorizationPolicy",
    "EV-126": "GET /applications",
    "EV-127": "GET /auditLogs/signIns",
    "EV-151": "GET /directoryRoles",
    "EV-154": "GET /policies/authenticationMethodsPolicy",
    "EV-167": "GET identity/conditionalAccess/policies",
    "EV-189": "GET /organization",
    "EV-207": "GET /applications",
    "EV-461": "GET identity/conditionalAccess/policies, namedLocations",
    "EV-463": "GET identity/conditionalAccess/namedLocations",
    "EV-476": "GET /policies/authenticationMethodsPolicy",
    "EV-522": "GET /groups, /directoryRoles",
}

ENTRA_EVIDENCE_SEED_ROWS: list[dict[str, str]] = [
    {
        "code": row["code"],
        "name": row["name"],
        "category": row["category"],
        "api": _ENTRA_GRAPH_API_HINTS[row["code"]],
        "collector_key": row["code"],
    }
    for row in IAM_EVIDENCE_SEED_ROWS
]

ALL_ENTRA_IAM_EVIDENCE_CODES = ALL_IAM_EVIDENCE_CODES

CODE_TO_COLLECTOR: dict[str, str] = {row["code"]: row["collector_key"] for row in ENTRA_EVIDENCE_SEED_ROWS}
