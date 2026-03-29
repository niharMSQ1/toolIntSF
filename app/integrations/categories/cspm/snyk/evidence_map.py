"""
Maps evidence_masters.code (Security / Vulnerability Management) to Snyk REST strategies.

Uses GET /rest/orgs/{org_id}/issues, /rest/orgs/{org_id}/projects, and optionally
GET /rest/groups/{group_id}/issues. Org list via GET /v1/orgs.
"""

from __future__ import annotations

from typing import Literal

SnykStrategy = Literal[
    "dependency_issues",
    "projects_config",
    "issues_summary",
    "remediation",
    "code_issues",
    "integration_config",
    "vuln_scan_summary",
]

# Names must match mappings.txt for domain cd545de5-0565-447b-89ef-f137d2267a70 (source=snyk).
SNYK_SEED_ROWS: list[dict[str, str]] = [
    {
        "code": "EV-122",
        "name": "Dependency Vulnerability Scan Reports — Security",
        "category": "Security",
    },
    {
        "code": "EV-123",
        "name": "Dependency Scan Configuration Records — Security",
        "category": "Security",
    },
    {
        "code": "EV-139",
        "name": "Vulnerability Scan Reports — Security",
        "category": "Security",
    },
    {
        "code": "EV-142",
        "name": "Vulnerability Remediation Reports — Security",
        "category": "Security",
    },
    {
        "code": "EV-97",
        "name": "Web Application Vulnerability Scan Reports — Security",
        "category": "Security",
    },
    {
        "code": "EV-98",
        "name": "Vulnerability Scan Configuration Records — Security",
        "category": "Security",
    },
    {
        "code": "EV-SEC-VULN-SCAN",
        "name": "Vulnerability scan results",
        "category": "Security",
    },
]

ALL_SNYK_EVIDENCE_CODES: tuple[str, ...] = tuple(r["code"] for r in SNYK_SEED_ROWS)
EVIDENCE_MASTER_NAME_ORDER: tuple[str, ...] = tuple(r["name"] for r in SNYK_SEED_ROWS)

EVIDENCE_CODE_STRATEGY: dict[str, SnykStrategy] = {
    "EV-122": "dependency_issues",
    "EV-123": "projects_config",
    "EV-139": "issues_summary",
    "EV-142": "remediation",
    "EV-97": "code_issues",
    "EV-98": "integration_config",
    "EV-SEC-VULN-SCAN": "vuln_scan_summary",
}
