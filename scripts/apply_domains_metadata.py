"""
One-shot: add evidence metadata columns to `domains` and populate from product taxonomy.
Run from project root: python scripts/apply_domains_metadata.py
"""
from __future__ import annotations

from sqlalchemy import text

from app.database import engine

# (uuid, domain_group, evidence_sources, primary_evidence, secondary_evidence, common_tools)
ROWS: list[tuple[str, str, str, str, str, str]] = [
    (
        "1721b991-e491-4953-b2bb-ca35d815024f",
        "Cloud & Infrastructure",
        "Cloud platforms, IaC, CSPM",
        "Config exports, access logs, drift reports, posture scores",
        "Architecture diagrams, change history, benchmark reports",
        "AWS, Azure, GCP, Terraform, Wiz",
    ),
    (
        "311fd3a8-255b-4bc8-b6a0-0fe625d81341",
        "Identity & Access Management",
        "IAM, IGA, PAM",
        "User provisioning logs, role assignments, access reviews, PAM session logs",
        "Orphaned account reports, privilege summaries, recertification records",
        "Okta, Azure AD, JumpCloud, CyberArk",
    ),
    (
        "cd545de5-0565-447b-89ef-f137d2267a70",
        "Security Management",
        "Vuln management, SIEM, Endpoint",
        "Scan reports, SIEM alerts, EDR policy configs, remediation tickets",
        "Trend reports, patch compliance, asset coverage, threat detection logs",
        "Tenable, Splunk, CrowdStrike, Sentinel",
    ),
    (
        "70b4419c-8544-47be-9f13-bc21356bd897",
        "Compliance & GRC",
        "Policy, Risk, Audit tools",
        "Approved policies, risk registers, audit findings, control test results",
        "Exception logs, remediation tracking, risk scoring history",
        "Vanta, Drata, ServiceNow GRC, AuditBoard",
    ),
    (
        "6874f3ab-44fc-4b3e-a95e-bd01e03bf933",
        "DevOps & DevSecOps",
        "Source control, CI/CD, SAST/DAST, Secrets, Containers",
        "Commit history, build logs, code scan results, secrets detection logs, image scan results",
        "PR approvals, rollback logs, dependency reports, pipeline configs",
        "GitHub, Jenkins, Snyk, SonarQube, Trivy",
    ),
    (
        "cd4015e2-8a3f-4f54-a3ee-9dfddb048f84",
        "IT Service Management",
        "Incident, Change, Problem management",
        "Incident tickets, change approvals, SLA records, root cause docs",
        "MTTR reports, change success rates, postmortem records",
        "ServiceNow, Jira, PagerDuty, Freshservice",
    ),
    (
        "465c7082-4a36-4567-b535-e6fe16994eec",
        "HRMS",
        "HRMS, Project management",
        "Joiner/mover/leaver records, offboarding checklists, task approvals",
        "Headcount reports, org chart exports, milestone logs",
        "Workday, BambooHR, Rippling, Jira",
    ),
    (
        "55890cf9-a72e-4a13-a9bd-2da8d02d8968",
        "Project Management / Productivity",
        "HRMS, Project management",
        "Joiner/mover/leaver records, offboarding checklists, task approvals",
        "Headcount reports, org chart exports, milestone logs",
        "Workday, BambooHR, Rippling, Jira",
    ),
    (
        "2e615251-860d-4f37-9c1e-7334b67fdff4",
        "Physical Security",
        "Access control, Surveillance",
        "Badge access logs, entry/exit records, CCTV retention configs",
        "Visitor logs, after-hours reports, camera health records",
        "Verkada, Genetec, Brivo",
    ),
    (
        "f3c7a9d4-8e21-4b6f-9c3a-2d5e7f8a1b90",
        "CSPM",
        "Cloud platforms, IaC, CSPM",
        "Config exports, access logs, drift reports, posture scores",
        "Architecture diagrams, change history, benchmark reports",
        "AWS, Azure, GCP, Terraform, Wiz",
    ),
]


def main() -> None:
    alters = [
        "ALTER TABLE domains ADD COLUMN IF NOT EXISTS evidence_sources TEXT",
        "ALTER TABLE domains ADD COLUMN IF NOT EXISTS primary_evidence TEXT",
        "ALTER TABLE domains ADD COLUMN IF NOT EXISTS secondary_evidence TEXT",
        "ALTER TABLE domains ADD COLUMN IF NOT EXISTS common_tools TEXT",
    ]
    upd = text(
        """
        UPDATE domains SET
            domain_group = :domain_group,
            evidence_sources = :evidence_sources,
            primary_evidence = :primary_evidence,
            secondary_evidence = :secondary_evidence,
            common_tools = :common_tools,
            updated_at = NOW()
        WHERE id = CAST(:id AS uuid)
        """
    )
    with engine.begin() as conn:
        for stmt in alters:
            conn.execute(text(stmt))
        for row in ROWS:
            conn.execute(
                upd,
                {
                    "id": row[0],
                    "domain_group": row[1],
                    "evidence_sources": row[2],
                    "primary_evidence": row[3],
                    "secondary_evidence": row[4],
                    "common_tools": row[5],
                },
            )
    print(f"Applied metadata to {len(ROWS)} domain rows.")


if __name__ == "__main__":
    main()
