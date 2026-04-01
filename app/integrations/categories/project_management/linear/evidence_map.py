"""Map Linear evidence codes to concrete GraphQL strategies and required fields."""

from __future__ import annotations

from typing import Literal

LinearStrategy = Literal[
    "identity_viewer",
    "users_register",
    "issues_register",
    "projects_register",
    "teams_register",
    "workflow_states_register",
]

# Strict mapping: every evidence code must be explicitly mapped.
# Keep this in sync with evidence_masters for the Linear tool/domain.
EVIDENCE_CODE_STRATEGY: dict[str, LinearStrategy] = {
    "EV-5": "issues_register",
    "EV-13": "issues_register",
    "EV-18": "issues_register",
    "EV-19": "issues_register",
    "EV-27": "issues_register",
    "EV-31": "issues_register",
    "EV-32": "issues_register",
    "EV-35": "issues_register",
    "EV-36": "workflow_states_register",
    "EV-38": "issues_register",
    "EV-51": "issues_register",
    "EV-58": "issues_register",
    "EV-62": "issues_register",
    "EV-71": "issues_register",
    "EV-72": "workflow_states_register",
    "EV-99": "issues_register",
    "EV-102": "workflow_states_register",
    "EV-106": "issues_register",
    "EV-145": "issues_register",
    "EV-147": "issues_register",
    "EV-153": "issues_register",
    "EV-159": "issues_register",
    "EV-213": "issues_register",
    "EV-220": "issues_register",
    "EV-221": "issues_register",
    "EV-229": "issues_register",
    "EV-270": "issues_register",
    "EV-277": "issues_register",
    "EV-278": "issues_register",
    "EV-324": "issues_register",
    "EV-325": "issues_register",
    "EV-329": "issues_register",
    "EV-330": "issues_register",
    "EV-338": "issues_register",
    "EV-347": "issues_register",
    "EV-351": "issues_register",
    "EV-373": "issues_register",
    "EV-381": "issues_register",
    "EV-387": "issues_register",
    "EV-394": "issues_register",
    "EV-408": "issues_register",
    "EV-414": "issues_register",
    "EV-437": "issues_register",
    "EV-444": "issues_register",
    "EV-473": "issues_register",
    "EV-489": "issues_register",
    "EV-507": "issues_register",
    "EV-519": "workflow_states_register",
    "EV-543": "issues_register",
    "EV-544": "issues_register",
    "EV-554": "issues_register",
    "EV-568": "issues_register",
}

REQUIRED_FIELDS: dict[LinearStrategy, tuple[str, ...]] = {
    "identity_viewer": ("id", "name", "email"),
    "users_register": ("id", "name", "email", "active"),
    "issues_register": ("id", "identifier", "title", "state.name", "url"),
    "projects_register": ("id", "name", "url"),
    "teams_register": ("id", "name", "key"),
    "workflow_states_register": ("id", "name", "type", "team.id"),
}

GRAPHQL_QUERY_DOC: dict[LinearStrategy, str] = {
    "identity_viewer": "query { viewer { id name email } }",
    "users_register": "query ($first: Int!) { users(first: $first) { nodes { id name email active admin } } }",
    "issues_register": (
        "query ($first: Int!) { issues(first: $first) { nodes { id identifier title state { name } url } } }"
    ),
    "projects_register": "query ($first: Int!) { projects(first: $first) { nodes { id name url } } }",
    "teams_register": "query ($first: Int!) { teams(first: $first) { nodes { id name key } } }",
    "workflow_states_register": (
        "query ($first: Int!) { workflowStates(first: $first) { nodes { id name type team { id name } } } }"
    ),
}


def resolve_strategy(evidence_code: str) -> LinearStrategy:
    code = (evidence_code or "").strip().upper()
    if code in EVIDENCE_CODE_STRATEGY:
        return EVIDENCE_CODE_STRATEGY[code]
    raise ValueError(
        f"Unmapped evidence code {code!r}. Add this code to EVIDENCE_CODE_STRATEGY for strict collection."
    )
