"""
Maps evidence_masters.code (EV-604..EV-650) to Wiz GraphQL collection strategies.

Wiz API (public patterns): OAuth2 client credentials → `auth.app.wiz.io/oauth/token` with
`audience=wiz-api`; GraphQL POST to tenant URL (`https://api.<region>.app.wiz.io/graphql`).
Service accounts need scopes such as read:issues, read graph resources, read vulnerabilities
(Microsoft / Wiz docs). The schema is tenant-specific; we query `issues`, `vulnerabilityFindings`,
`cloudResources`, `projects`, and `users` with Relay-style `nodes` or `edges` fallbacks.

Collectability summary (EV-604..EV-650):
- **GraphQL-backed (issues / findings / inventory / users):** Most codes use Issues,
  VulnerabilityFindings, CloudResources/Projects, or Users — aligned to Wiz security graph data.
- **integration_config (EV-622):** Stored integration + masked secrets (no portal-only matrix).
- **export_only (EV-620,636,637,643,648,649,650):** Formal reports, executive PDFs, NTP,
  pentest records, legal packs — collect from Wiz UI or GRC; API returns structured "not via API"
  payloads with guidance.
"""

from __future__ import annotations

from typing import Literal

WizStrategy = Literal[
    "cloud_inventory",
    "issues",
    "issues_critical_high",
    "vulnerability_findings",
    "vulnerability_findings_container",
    "users",
    "integration_config",
    "export_only",
    "partial_metadata",
]

# Names and codes must match seeded evidence_masters for the CSPM domain (source=wiz).
CSPM_WIZ_SEED_ROWS: list[dict[str, str]] = [
    {"code": "EV-604", "name": "Multi-cloud and account inventory", "category": "CSPM"},
    {"code": "EV-605", "name": "Cloud asset and resource inventory", "category": "CSPM"},
    {"code": "EV-606", "name": "Security posture and misconfiguration findings", "category": "CSPM"},
    {"code": "EV-607", "name": "Compliance framework and policy coverage", "category": "CSPM"},
    {"code": "EV-608", "name": "Critical and high-severity issue summary", "category": "CSPM"},
    {"code": "EV-609", "name": "Workload and VM vulnerability findings", "category": "CSPM"},
    {"code": "EV-610", "name": "Container image vulnerability findings", "category": "CSPM"},
    {"code": "EV-611", "name": "Kubernetes cluster security posture", "category": "CSPM"},
    {"code": "EV-612", "name": "Cloud IAM and excessive permissions review", "category": "CSPM"},
    {"code": "EV-613", "name": "Secrets and sensitive data exposure findings", "category": "CSPM"},
    {"code": "EV-614", "name": "Network exposure and public attack surface", "category": "CSPM"},
    {"code": "EV-615", "name": "Data store encryption and protection posture", "category": "CSPM"},
    {"code": "EV-616", "name": "Storage bucket and object exposure posture", "category": "CSPM"},
    {"code": "EV-617", "name": "Serverless and managed service security posture", "category": "CSPM"},
    {"code": "EV-618", "name": "IaC and build pipeline security findings", "category": "CSPM"},
    {"code": "EV-619", "name": "Issue lifecycle and remediation tracking", "category": "CSPM"},
    {"code": "EV-620", "name": "Risk scoring and organizational risk snapshot", "category": "CSPM"},
    {"code": "EV-621", "name": "Custom policy and organizational control violations", "category": "CSPM"},
    {"code": "EV-622", "name": "Cloud connector and integration configuration", "category": "CSPM"},
    {"code": "EV-623", "name": "Audit and activity logging for CSPM platform access", "category": "CSPM"},
    {"code": "EV-624", "name": "Logical access — cloud identity inventory (SOC 2 CC6.1 / ISO A.5.16)", "category": "CSPM"},
    {"code": "EV-625", "name": "Authentication strength and risky auth configs (SOC 2 CC6.1 / ISO A.5.17)", "category": "CSPM"},
    {"code": "EV-626", "name": "Privileged access paths in cloud (SOC 2 CC6.2 / ISO A.5.18)", "category": "CSPM"},
    {"code": "EV-627", "name": "Data classification and sensitive asset tagging (SOC 2 CC6.7 / ISO A.5.12)", "category": "CSPM"},
    {"code": "EV-628", "name": "Encryption and key management posture (SOC 2 CC6.6 / ISO A.8.24)", "category": "CSPM"},
    {"code": "EV-629", "name": "Vulnerability management program metrics (SOC 2 CC7.1 / ISO A.8.8)", "category": "CSPM"},
    {"code": "EV-630", "name": "Security monitoring and detection coverage (SOC 2 CC7.2 / ISO A.8.16)", "category": "CSPM"},
    {"code": "EV-631", "name": "Incident response readiness — cloud blast radius (SOC 2 CC7.3 / ISO A.5.24)", "category": "CSPM"},
    {"code": "EV-632", "name": "Change management drift — config vs baseline (SOC 2 CC8.1 / ISO A.8.32)", "category": "CSPM"},
    {"code": "EV-633", "name": "Malware and unwanted software on workloads (SOC 2 CC7.1 / ISO A.8.7)", "category": "CSPM"},
    {"code": "EV-634", "name": "Backup and recovery visibility for cloud data (SOC 2 CC9.1 / ISO A.8.13)", "category": "CSPM"},
    {"code": "EV-635", "name": "Vendor and third-party integration risk (SOC 2 CC9.2 / ISO A.5.19)", "category": "CSPM"},
    {"code": "EV-636", "name": "Regulatory and industry control mapping report (SOC 2 CC2.2 / ISO A.5.31)", "category": "CSPM"},
    {"code": "EV-637", "name": "Management review of cloud security posture (SOC 2 CC3.2 / ISO A.5.35)", "category": "CSPM"},
    {"code": "EV-638", "name": "Network segmentation and security group posture (ISO A.8.20 / SOC 2 CC6.6)", "category": "CSPM"},
    {"code": "EV-639", "name": "API and service endpoint exposure (ISO A.8.26 / SOC 2 CC6.1)", "category": "CSPM"},
    {"code": "EV-640", "name": "Logging and audit trail enablement for cloud (ISO A.8.15 / SOC 2 CC7.2)", "category": "CSPM"},
    {"code": "EV-641", "name": "Secure development and pipeline integration (ISO A.8.25 / SOC 2 CC8.1)", "category": "CSPM"},
    {"code": "EV-642", "name": "Separation of production and non-production (ISO A.8.31 / SOC 2 CC6.1)", "category": "CSPM"},
    {"code": "EV-643", "name": "Clock synchronization and time integrity (ISO A.8.17 / SOC 2 CC7.2)", "category": "CSPM"},
    {"code": "EV-644", "name": "Web filtering and egress control posture (ISO A.8.23 / SOC 2 CC6.6)", "category": "CSPM"},
    {"code": "EV-645", "name": "Data retention and secure deletion posture (ISO A.8.10 / SOC 2 CC6.7)", "category": "CSPM"},
    {"code": "EV-646", "name": "Business continuity — multi-region and redundancy (ISO A.8.14 / SOC 2 CC9.1)", "category": "CSPM"},
    {"code": "EV-647", "name": "Outsourced development and supply chain visibility (ISO A.8.30 / SOC 2 CC9.2)", "category": "CSPM"},
    {"code": "EV-648", "name": "Protection of information during penetration testing (ISO A.8.34 / SOC 2 CC4.1)", "category": "CSPM"},
    {"code": "EV-649", "name": "Legal and regulatory evidence export for cloud (ISO A.5.31 / SOC 2 CC2.2)", "category": "CSPM"},
    {"code": "EV-650", "name": "Continuous compliance monitoring dashboard snapshot (SOC 2 CC4.2 / ISO A.8.16)", "category": "CSPM"},
]

ALL_CSPM_WIZ_EVIDENCE_CODES: tuple[str, ...] = tuple(r["code"] for r in CSPM_WIZ_SEED_ROWS)
EVIDENCE_MASTER_NAME_ORDER: tuple[str, ...] = tuple(r["name"] for r in CSPM_WIZ_SEED_ROWS)

# Per-code strategy for the collector.
EVIDENCE_CODE_STRATEGY: dict[str, WizStrategy] = {
    "EV-604": "cloud_inventory",
    "EV-605": "cloud_inventory",
    "EV-606": "issues",
    "EV-607": "issues",
    "EV-608": "issues_critical_high",
    "EV-609": "vulnerability_findings",
    "EV-610": "vulnerability_findings_container",
    "EV-611": "issues",
    "EV-612": "issues",
    "EV-613": "issues",
    "EV-614": "issues",
    "EV-615": "issues",
    "EV-616": "issues",
    "EV-617": "issues",
    "EV-618": "issues",
    "EV-619": "issues",
    "EV-620": "export_only",
    "EV-621": "issues",
    "EV-622": "integration_config",
    "EV-623": "users",
    "EV-624": "issues",
    "EV-625": "issues",
    "EV-626": "issues",
    "EV-627": "issues",
    "EV-628": "issues",
    "EV-629": "issues",
    "EV-630": "issues",
    "EV-631": "issues",
    "EV-632": "issues",
    "EV-633": "issues",
    "EV-634": "issues",
    "EV-635": "issues",
    "EV-636": "export_only",
    "EV-637": "export_only",
    "EV-638": "issues",
    "EV-639": "issues",
    "EV-640": "issues",
    "EV-641": "issues",
    "EV-642": "issues",
    "EV-643": "export_only",
    "EV-644": "issues",
    "EV-645": "issues",
    "EV-646": "issues",
    "EV-647": "issues",
    "EV-648": "export_only",
    "EV-649": "export_only",
    "EV-650": "export_only",
}

COLLECTABILITY_NOTES: dict[str, str] = {
    "EV-620": "Organizational risk scorecards are typically exported from the Wiz UI or executive reports; not a single GraphQL field.",
    "EV-636": "Formal control-mapping reports: export from Wiz Compliance / Reports.",
    "EV-637": "Management review minutes: procedural evidence; supplement with Wiz dashboard exports.",
    "EV-643": "NTP/time sync is not exposed as a dedicated Wiz API artifact; collect from cloud provider or VM agents.",
    "EV-648": "Pentest scope and safeguards: procedural; Wiz API does not replace engagement records.",
    "EV-649": "Legal/regulatory packs: export manually from Wiz or GRC tooling.",
    "EV-650": "Dashboard snapshots: screenshot or export from Wiz portal; API provides issue aggregates, not PNG/PDF.",
}
