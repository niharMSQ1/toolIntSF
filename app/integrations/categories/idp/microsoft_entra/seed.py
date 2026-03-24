from __future__ import annotations

ENTRA_EVIDENCE_SEED_ROWS: list[dict[str, str]] = [
    {
        "code": "IDP_DIRECTORY_USERS",
        "name": "Directory Users",
        "category": "IDP_DIRECTORY",
        "api": "/users",
        "collector_key": "directory_users",
    },
    {
        "code": "IDP_DIRECTORY_GROUPS",
        "name": "Directory Groups",
        "category": "IDP_DIRECTORY",
        "api": "/groups",
        "collector_key": "directory_groups",
    },
]

EVIDENCE_MASTER_NAME_ORDER: tuple[str, ...] = tuple(row["name"] for row in ENTRA_EVIDENCE_SEED_ROWS)

CODE_TO_COLLECTOR: dict[str, str] = {row["code"]: row["collector_key"] for row in ENTRA_EVIDENCE_SEED_ROWS}
