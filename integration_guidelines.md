# GRC Integration Evidence Collection Guide

This document describes **how a GRC platform integrates with enterprise tools** to automatically collect compliance evidence and validate controls for frameworks such as:

* SOC 2
* ISO 27001
* HIPAA
* PCI-DSS

Each integration defines:

* **WHAT** evidence to collect
* **WHY** it matters for compliance
* **WHEN** it should be collected
* **HOW** the integration should be implemented

---

# Integration Architecture Model

Each integration follows this structure:

```
Integration Source
      ↓
Evidence Collection
      ↓
Normalization
      ↓
Control Mapping
      ↓
Compliance Evaluation
      ↓
Evidence Storage (Tamper-proof)
```

---

# 1. Cloud Providers

Examples: AWS / GCP / Azure

## WHAT (Evidence to Collect)

* IAM user & role lists
* MFA status
* CloudTrail / audit logs
* Storage encryption status (S3 / GCS / Azure Blob)
* Storage access controls
* Security group / firewall rules
* KMS keys
* Infrastructure-as-code snapshots (CloudFormation / Terraform state)

## WHY (Audit Value)

Demonstrates:

* Encryption at rest
* Access control enforcement
* Logging & monitoring
* Least-privilege permissions
* Secure infrastructure configuration

## WHEN

* Config snapshots → Daily
* Audit logs → Near real-time
* Drift checks → Hourly or on deployment events

## HOW

Implementation steps:

1. Create restricted service account or cross-account role.
2. Grant minimal read permissions.
3. Pull configuration snapshots.
4. Store signed, timestamped artifacts.
5. Map resources to compliance controls.
6. Store artifacts in tamper-evident storage.

Example controls:

```
S3 encryption enabled
CloudTrail logging active
IAM root access not used
```

Fallback options:

* Scheduled screenshots
* CSV exports

Important considerations:

* Handle API rate limits
* Use pagination for large accounts

---

# 2. Source Control / Code Repositories

Examples:

* GitHub
* GitLab
* Bitbucket

## WHAT

* Repository list
* Branch protection rules
* Commit history
* Pull request approvals
* CODEOWNERS configuration
* Secret scanning reports
* Software composition analysis results

## WHY

Validates **secure development lifecycle controls**.

Proves:

* Code review enforcement
* Change control
* Secure repository configuration

## WHEN

* Repo metadata sync → Daily
* Branch protection updates → Webhooks
* Secret scan results → On scan completion

## HOW

1. Integrate using OAuth or access tokens.
2. Fetch repositories via REST or GraphQL APIs.
3. Subscribe to repository webhooks.
4. Normalize configuration evidence.
5. Map repository policies to compliance controls.

Example evidence:

```
branch_protection = true
required_reviews = 2
timestamp = 2026-03-12
```

Security considerations:

* Rotate tokens regularly
* Apply least privilege access

---

# 3. Identity Providers / SSO

Examples:

* Okta
* Azure AD
* Google Workspace

## WHAT

* User directory
* Group memberships
* MFA enrollment
* Admin role assignments
* SSO application configurations
* Login logs

## WHY

Proves:

* MFA enforcement
* Access governance
* User provisioning & deprovisioning
* Admin privilege monitoring

## WHEN

* User list sync → Nightly
* Admin changes → Immediate alert
* MFA changes → Webhook triggered

## HOW

1. Use SCIM or Admin APIs.
2. Fetch users and authentication metadata.
3. Store access snapshots.
4. Cross-check with HR system.
5. Detect orphan accounts.

Fallback:

* CSV exports from admin console.

Security features:

* Snapshot hashing
* Timestamp verification

---

# 4. HR / People Systems

Examples:

* BambooHR
* Rippling
* Workday

## WHAT

* Employee directory
* Hire dates
* Termination dates
* Role and department
* Security training completion
* Policy acknowledgment records

## WHY

Supports controls related to:

* Access provisioning
* Offboarding verification
* Security awareness training
* Policy attestations

## WHEN

* Employee sync → Nightly
* Termination event → Immediate
* Training completion → Event-driven

## HOW

1. Integrate using vendor APIs.
2. Map HR user ID to identity provider account.
3. Detect joiners and leavers.
4. Verify training completion records.
5. Store policy acknowledgment evidence.

Privacy considerations:

* PII protection
* Data retention policies

Fallback:

* HR exports uploaded manually.

---

# 5. Endpoint / Device Security

Examples:

* Jamf
* CrowdStrike
* Microsoft Defender

## WHAT

* Device inventory
* Agent version
* Disk encryption status
* Firewall configuration
* Patch level
* Endpoint alerts

## WHY

Proves:

* Endpoint security enforcement
* Patch management
* Device hardening

## WHEN

* Agent heartbeat → Hourly
* Critical alerts → Immediate

## HOW

1. Deploy endpoint agent.
2. Collect telemetry via secure channel.
3. Normalize device evidence.
4. Correlate with asset inventory.

Fallback:

* Manual device inventory
* Screenshot evidence

Security requirements:

* Mutual TLS for telemetry
* Agent integrity validation

---

# 6. CI/CD Pipelines

Examples:

* Jenkins
* CircleCI
* GitHub Actions

## WHAT

* Build logs
* Pipeline definitions
* Artifact signatures
* Dependency scanning results
* Test coverage reports

## WHY

Demonstrates:

* Secure build pipeline
* Dependency vulnerability management
* Artifact integrity

## WHEN

* Build completion → Webhook
* Pipeline configuration sync → Daily

## HOW

1. Register CI integration with read-only access.
2. Subscribe to build completion events.
3. Fetch pipeline configuration.
4. Verify artifact signatures.
5. Store build logs as evidence.

---

# 7. ITSM / Ticketing Systems

Examples:

* Jira
* ServiceNow

## WHAT

* Compliance remediation tickets
* Ticket status
* SLA information
* Attached evidence

## WHY

Proves remediation workflow and accountability.

Demonstrates:

* Issue tracking
* Assigned ownership
* Audit trail of fixes

## WHEN

* Create ticket when noncompliance detected
* Sync updates in real time

## HOW

1. Create tickets automatically from compliance alerts.
2. Attach evidence snapshots.
3. Track resolution status.
4. Close control findings when ticket resolved.

Requirements:

* Idempotent ticket creation
* Traceable remediation history

---

# 8. Logging / SIEM / Monitoring

Examples:

* Splunk
* ELK
* Datadog

## WHAT

* Log ingestion evidence
* Alert history
* Saved queries
* Log retention policy

## WHY

Demonstrates:

* Monitoring coverage
* Incident detection
* Log retention compliance

## WHEN

* Log ingestion → Real-time
* Retention policy verification → Weekly

## HOW

1. Validate log sources configured.
2. Export saved searches.
3. Capture alert history.
4. Store signed query results.

---

# 9. Vulnerability Scanners

Examples:

* Qualys
* Nessus

## WHAT

* Vulnerability reports
* Scan schedules
* CVE severity levels
* Patch deployment evidence

## WHY

Supports vulnerability management lifecycle:

```
Discovery → Remediation → Verification
```

## WHEN

* Critical systems → Daily scans
* Normal assets → Weekly scans
* Re-scan after patch

## HOW

1. Fetch scan reports via API.
2. Map vulnerabilities to assets.
3. Generate remediation tickets.
4. Verify remediation via re-scan.

Features:

* CVE correlation
* Patch-first filtering

---

# 10. Document Stores / Knowledge Systems

Examples:

* SharePoint
* Google Drive
* Confluence

## WHAT

* Policy documents
* Version history
* Attestation records
* Access logs

## WHY

Provides **policy evidence for audits**.

Supports:

* Policy management
* Employee acknowledgment
* Document version tracking

## WHEN

* Document sync → Nightly
* Critical policy changes → Immediate capture

## HOW

1. Fetch document metadata.
2. Store version history.
3. Hash signed policy versions.
4. Provide read-only auditor access.

Fallback:

* Export PDF versions

---

# 11. Vendor Risk / Third-Party Management

## WHAT

* Vendor SOC reports
* Contracts
* Access logs
* Security questionnaires

## WHY

Demonstrates third-party risk management controls.

## WHEN

* Vendor onboarding
* Quarterly vendor review
* When vendor reports updated

## HOW

1. Ingest vendor attestations.
2. Link documents to vendor profiles.
3. Schedule reassessment reminders.
4. Map vendor controls to internal control framework.

---

# Evidence Storage Requirements

Evidence collected must be:

* **Timestamped**
* **Digitally signed**
* **Immutable**
* **Tamper-evident**

Recommended storage mechanisms:

```
Object storage with versioning
WORM storage
Signed artifact hashes
```

---

# Summary

A GRC platform works by:

```
Integrations
     ↓
Evidence collection
     ↓
Control mapping
     ↓
Automated compliance evaluation
     ↓
Audit-ready reports
```

Well-designed integrations ensure **continuous compliance monitoring** without manual evidence collection.
