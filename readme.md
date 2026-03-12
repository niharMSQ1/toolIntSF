# GRC Tool Integrations – Architecture, Scenarios, and Control Automation

This document describes **building integrations for a GRC (Governance, Risk, and Compliance) platform**. It explains how integrations work, how evidence is collected and normalized, and how automated controls are evaluated for frameworks such as **SOC 2**, **ISO 27001**, **HIPAA**, **GDPR**, and **PCI-DSS**.

---

## Table of Contents

1. [What a GRC Platform Does](#1-what-a-grc-platform-does)
2. [Core Architecture of GRC Integrations](#2-core-architecture-of-grc-integrations)
3. [HRMS Integrations](#3-hrms-integrations)
4. [Identity Provider Integrations](#4-identity-provider-integrations)
5. [ITSM Integrations](#5-itsm-integrations)
6. [Detecting Deprovision / Offboarding Tickets](#6-detecting-deprovision--offboarding-tickets)
7. [Cloud Infrastructure Integrations](#7-cloud-infrastructure-integrations)
8. [Version Control Integrations](#8-version-control-integrations)
9. [Device Management Integrations](#9-device-management-integrations)
10. [Security Tool Integrations](#10-security-tool-integrations)
11. [Vulnerability Management Integrations](#11-vulnerability-management-integrations)
12. [Password Manager Integrations](#12-password-manager-integrations)
13. [Communication Tool Integrations](#13-communication-tool-integrations)
14. [Logging and Monitoring Integrations](#14-logging-and-monitoring-integrations)
15. [Example Automated Controls (End-to-End)](#15-example-automated-controls-end-to-end)
16. [Cross-Integration and Multi-Source Controls](#16-cross-integration-and-multi-source-controls)
17. [Evidence Normalization and Storage](#17-evidence-normalization-and-storage)
18. [Framework Mapping (SOC 2, ISO 27001, etc.)](#18-framework-mapping-soc-2-iso-27001-etc)
19. [Core Concept of Automated Compliance](#19-core-concept-of-automated-compliance)
20. [Implementation and Operational Guidance](#20-implementation-and-operational-guidance)
21. [Key Takeaways](#21-key-takeaways)

---

# 1. What a GRC Platform Does

A GRC platform automates compliance by **collecting evidence from different enterprise systems** and **evaluating it against defined compliance controls**. Instead of manual screenshots and spreadsheets, it uses **integrations** to pull data continuously and produce **audit-ready results**.

## Why Automate?

- **Continuous monitoring**: Controls are evaluated on a schedule (e.g., daily) rather than only at audit time.
- **Consistency**: Same logic applied every time; no human interpretation drift.
- **Traceability**: Evidence is timestamped, stored, and linked to control results.
- **Scalability**: One integration serves many controls and many frameworks.

## Typical Compliance Frameworks

| Framework   | Focus                                      | Common automated areas                    |
|------------|--------------------------------------------|-------------------------------------------|
| **SOC 2**  | Security, availability, processing integrity | Access, MFA, change management, logging   |
| **ISO 27001** | ISMS, risk treatment                    | Access control, asset management, crypto  |
| **HIPAA**  | PHI protection                             | Access, encryption, audit logs            |
| **GDPR**   | Personal data, rights, breach notification  | Access, retention, consent                |
| **PCI-DSS**| Cardholder data                             | Access, encryption, vulnerability management |

## Integrated Tool Categories

- **HR systems (HRMS)** – employee lifecycle, joiners/leavers
- **Identity providers** – accounts, MFA, roles
- **ITSM systems** – tickets, approvals, offboarding workflows
- **Cloud platforms** – IAM, storage, logging
- **Version control** – code review, branch protection
- **Device management** – encryption, patch, inventory
- **Security tools** – EDR, vuln scans, SIEM

Together these integrations provide **continuous compliance monitoring** and **automated control evaluation**.

---

# 2. Core Architecture of GRC Integrations

## High-Level Pipeline

```
External Tools (HRMS, IdP, ITSM, Cloud, etc.)
     ↓
Data Ingestion (APIs, OAuth, webhooks)
     ↓
Evidence Normalization (canonical schema per evidence type)
     ↓
Control Evaluation Engine (rules + thresholds)
     ↓
Compliance Result (PASS / FAIL / NOT_APPLICABLE / EXCEPTION)
     ↓
Evidence Storage (immutable, timestamped)
     ↓
Audit Reports & Dashboards
```

## Example End-to-End Flow

```
HRMS Integration (e.g. Zoho People)
     ↓
Detect employee exit (exit_date set)
     ↓
Check ITSM (e.g. Jira Service Management) for offboarding ticket
     ↓
Verify identity provider: account disabled
     ↓
Optionally: verify cloud IAM access removed
     ↓
Evaluate control: "Access removed within 24 hours"
     ↓
Mark compliance PASS or FAIL, attach evidence
```

## Implementation Notes (This Repo)

- **HRMS**: Zoho People – OAuth flow, evidence collected on callback and stored.
- **ITSM**: Jira Service Management – OAuth (Atlassian), cloud_id and tokens stored; evidence collected and persisted after successful auth.

---

# 3. HRMS Integrations

HRMS (Human Resource Management System) is the **source of truth for employment status**. It drives joiner/leaver and contractor lifecycle, which many access and offboarding controls depend on.

## Example Systems

- **Zoho People** (implemented in this repo)
- Workday
- BambooHR
- SAP SuccessFactors
- ADP

## Evidence Collected (Typical Fields)

| Field            | Description                    | Use in controls                    |
|------------------|--------------------------------|------------------------------------|
| `employee_id`    | Unique identifier              | Correlation with IdP, ITSM         |
| `name`           | Full name                      | Reporting, ticket matching         |
| `department`     | Org unit                       | Access by role/department          |
| `manager`        | Manager employee_id or email  | Approval workflows                 |
| `date_of_join`   | Start date                     | Joiner process, provisioning SLA  |
| `date_of_exit`   | Termination/exit date          | Offboarding, access removal SLA    |
| `employee_email` | Work email                     | Account matching across systems    |
| `employment_type`| Employee / Contractor / Intern | Contractor expiry, policy differences |
| `status`         | Active / Inactive / On Leave   | Active population for access review |

## Compliance Scenarios (Extensive)

### 3.1 Employee offboarding detection

- **What**: Identify when an employee has left the company.
- **Evidence**: `date_of_exit` (or equivalent) is set; `status` = Inactive/Terminated.
- **Logic**: `exit_date exists AND exit_date <= today` → employee has left.
- **Use**: Triggers downstream checks (access disabled, offboarding ticket, etc.).

### 3.2 Access removal validation (HR + IdP)

- **What**: After exit, ensure identity account is disabled.
- **Evidence**: HRMS exit date; IdP account status, last disabled timestamp.
- **Logic**: For each employee with `exit_date`, check IdP; account must be disabled and (if available) disabled within policy window (e.g. 24 hours).

### 3.3 Joiner process validation

- **What**: New hires get accounts and access in a defined process.
- **Evidence**: HRMS `date_of_join`, new employee list; IdP account creation date; ITSM onboarding/access tickets.
- **Logic**: New employee → account created within X days; onboarding ticket present (if required).

### 3.4 Contractor and temporary access

- **What**: Contractors and temps must have defined end dates; access should expire.
- **Evidence**: HRMS `employment_type`, `contract_end_date` or `date_of_exit`.
- **Logic**: Contractor accounts must have expiry; no active contractor without end date (or exception).

### 3.5 Manager assignment

- **What**: Every active employee has an assigned manager (for approval and accountability).
- **Evidence**: HRMS `manager` or `manager_id`.
- **Logic**: For all active employees, `manager` is not null and (optionally) manager is also active.

### 3.6 Department and role consistency

- **What**: Employee department/role in HRMS aligns with access and groups in IdP/ITSM.
- **Evidence**: HRMS department/role; IdP group membership; ITSM request type.
- **Logic**: Compare HRMS attributes to IdP/ITSM; flag mismatches for review.

### 3.7 Leave and return

- **What**: Extended leave might require access reduction or restoration on return.
- **Evidence**: HRMS status (On Leave), leave start/end dates.
- **Logic**: Optional controls: access suspended during leave; access restored when status back to Active.

### 3.8 Duplicate or ghost records

- **What**: No duplicate active employees for same person; no “ghost” accounts without HR record.
- **Evidence**: HRMS employee list (by email/employee_id); IdP user list.
- **Logic**: IdP users with work email should have matching HRMS record (for employees); no duplicate employee_id/email in HRMS.

---

# 4. Identity Provider Integrations

Identity providers (IdPs) manage **authentication and user accounts**. They are central to access control, MFA, and leaver validation.

## Example Systems

- Okta
- Microsoft Entra ID (Azure AD)
- Google Workspace
- OneLogin
- PingFederate

## Evidence Collected

| Data              | Description                     | Use in controls              |
|-------------------|----------------------------------|------------------------------|
| User accounts     | id, email, name, created/updated | Joiner/leaver, dormant       |
| Admin roles       | Super admin, group admin, etc.   | Privileged access            |
| MFA status        | Enrolled, enforced, method      | MFA enforcement              |
| Login history     | Last login, failed attempts     | Dormant, anomaly             |
| Account status    | Active, suspended, deprovisioned | Leaver validation            |
| Group membership  | Groups and roles                 | Access review, department    |

## Compliance Scenarios (Extensive)

### 4.1 MFA enforcement

- **What**: All users (or all non-excluded) must have MFA enabled.
- **Evidence**: IdP MFA status per user.
- **Logic**: For each active user, `mfa_enabled == true` (or equivalent). Exclude break-glass/service accounts per policy.
- **Frameworks**: SOC 2 (CC6.1), ISO 27001 (A.9.4.2).

### 4.2 Privileged access monitoring

- **What**: Know who has admin or high-privilege roles; review and justify.
- **Evidence**: IdP admin role assignments, role name, user list.
- **Logic**: List users with admin roles; optionally check last review date or approval ticket.
- **Frameworks**: SOC 2, ISO 27001 (A.9.2.3).

### 4.3 Dormant account detection

- **What**: Accounts with no login for X days (e.g. 90) should be disabled or flagged.
- **Evidence**: IdP last login (or last activity) per user.
- **Logic**: `last_login < (today - 90 days)` and account still active → FAIL or exception.
- **Frameworks**: SOC 2, ISO 27001 (A.9.2.6).

### 4.4 Leaver account validation (HR + IdP)

- **What**: After HR exit, account must be disabled/deprovisioned within SLA.
- **Evidence**: HRMS exit date; IdP account status and (if available) disabled timestamp.
- **Logic**: For each HR leaver, IdP account must be disabled; optionally `disabled_time <= exit_date + 24h`.
- **Frameworks**: SOC 2 (CC6.1), ISO 27001.

### 4.5 Shared accounts detection

- **What**: Shared/generic accounts (e.g. support@) should be identified and controlled.
- **Evidence**: IdP account type, naming patterns, or “shared” flag; login history (many distinct users).
- **Logic**: Flag accounts that are designated shared or show multiple distinct users; require justification and stricter controls.
- **Frameworks**: SOC 2, PCI-DSS.

### 4.6 Service and break-glass accounts

- **What**: Service accounts and break-glass must be inventoried and rarely used for interactive login.
- **Evidence**: IdP account type, last login, MFA (often not applicable).
- **Logic**: List service/break-glass accounts; alert if interactive login used without ticket.
- **Frameworks**: SOC 2, ISO 27001.

### 4.7 Password and authentication policy

- **What**: Password policy (length, complexity, expiry if used) and lockout settings.
- **Evidence**: IdP policy configuration (via API or export).
- **Logic**: Compare to policy standard (e.g. length ≥ 12, complexity on, lockout after 5 failures).
- **Frameworks**: SOC 2, ISO 27001 (A.9.4.3).

### 4.8 Session and timeout

- **What**: Session timeout and re-authentication for sensitive actions.
- **Evidence**: IdP session policy settings.
- **Logic**: Session timeout ≤ required value (e.g. 8 hours); re-auth for sensitive actions.
- **Frameworks**: SOC 2, HIPAA.

---

# 5. ITSM Integrations

ITSM systems manage **tickets and operational processes**: access requests, change management, incidents, and offboarding workflows. They provide proof that processes were followed.

## Example Systems

- Jira Service Management
- ServiceNow
- Freshservice
- Zendesk
- Cherwell

## Evidence Collected

| Data                    | Description                          | Use in controls              |
|-------------------------|--------------------------------------|------------------------------|
| Access request tickets  | Type, requester, approver, status    | Access approval              |
| Change tickets          | Type, risk, approval, schedule       | Change management            |
| Incident tickets        | Severity, assignee, resolution time  | Incident SLA                 |
| Offboarding tickets     | Linked to leaver, status, tasks      | Offboarding workflow         |
| Approval workflows      | Steps, approvers, outcomes           | Segregation of duties        |

## Compliance Scenarios (Extensive)

### 5.1 Access request approval

- **What**: Access requests must have manager (or designated) approval before grant.
- **Evidence**: Ticket type = Access Request; approval field or workflow state; approver identity.
- **Logic**: Each access ticket has at least one approval step completed by an allowed role (e.g. manager).
- **Frameworks**: SOC 2 (CC6.1), ISO 27001 (A.9.2.2).

### 5.2 Offboarding workflow (HR + ITSM)

- **What**: For every employee exit there must be an offboarding (deprovisioning) ticket.
- **Evidence**: HRMS exit list; ITSM tickets (type/summary/labels match offboarding).
- **Logic**: For each HR leaver (by email/employee_id), at least one offboarding ticket exists and is linked (e.g. by email or ID).
- **Frameworks**: SOC 2, ISO 27001.

### 5.3 Offboarding ticket created in time

- **What**: Offboarding ticket created within X hours/days of exit.
- **Evidence**: HRMS exit date; ITSM ticket created date.
- **Logic**: `ticket_created_date <= exit_date + 24 hours` (or policy window).
- **Frameworks**: SOC 2.

### 5.4 Change management

- **What**: Production (or high-risk) changes require a change ticket and approval.
- **Evidence**: Change tickets (type, environment, risk, approval).
- **Logic**: Production changes have linked change ticket with approval; optional: emergency change has post-implementation review.
- **Frameworks**: SOC 2 (CC8.1), ISO 27001 (A.12.1.2).

### 5.5 Incident management and tracking

- **What**: Security and major incidents are recorded and tracked.
- **Evidence**: Incident tickets (type, severity, security tag).
- **Logic**: Incidents classified as security or high severity exist in ITSM; no critical incidents without ticket.
- **Frameworks**: SOC 2 (CC7.2), ISO 27001 (A.16.1.5).

### 5.6 Incident resolution SLA

- **What**: Critical/high incidents resolved within defined SLA.
- **Evidence**: Incident ticket severity, resolution time, SLA field.
- **Logic**: For critical/high, `resolution_time <= SLA`; breach = FAIL.
- **Frameworks**: SOC 2, ISO 27001.

### 5.7 Request fulfillment SLA

- **What**: Access or service requests fulfilled within agreed time.
- **Evidence**: Request ticket created/resolved dates, SLA.
- **Logic**: `resolved_date - created_date <= SLA` per request type.
- **Frameworks**: Internal policy, SLAs.

### 5.8 Segregation of duties (SoD)

- **What**: Same person should not request and approve high-risk access.
- **Evidence**: Request ticket requester and approver.
- **Logic**: For sensitive request types, `approver_id != requester_id`.
- **Frameworks**: SOC 2, ISO 27001, financial controls.

### 5.9 Recurring access review tickets

- **What**: Periodic access reviews are requested and completed via ITSM.
- **Evidence**: Review request tickets, completion status, due date.
- **Logic**: Review tickets created on schedule; completion before due date.
- **Frameworks**: SOC 2 (CC6.1), ISO 27001 (A.9.2.2).

---

# 6. Detecting Deprovision / Offboarding Tickets

There is **no universal standard** for how ITSM systems tag offboarding or deprovisioning. Organizations use different request types, labels, and custom fields.

## Common Request Type Names

- Offboarding
- Employee Offboarding
- Access Removal
- User Deprovisioning
- Account Disable
- Employee Exit
- Terminate User Access
- Disable Account
- Leaver Process
- Access Revocation

## Detection Strategies

### 6.1 Request type / issue type matching

- **How**: Map ticket type (e.g. `request_type`, `issue_type`) to a list of known offboarding values.
- **Example**: `if request_type in ["Offboarding", "Employee Exit", "Disable Access"]`.

### 6.2 Keyword matching on summary or description

- **How**: Search summary/description for keywords (e.g. offboard, deprovision, disable, termination, access removal).
- **Risk**: False positives/negatives; use as supplement or with configurable list.

### 6.3 Ticket labels / tags

- **How**: Use labels such as `offboarding`, `access-removal`, `deprovision`.
- **Example**: `"offboarding" in labels`.

### 6.4 Summary text matching

- **How**: Match phrases like “Disable user access”, “Terminate employee account” in title/summary.
- **Example**: Regex or substring match on summary.

### 6.5 Custom fields

- **How**: Use custom fields (e.g. “Process type”, “Employee email”, “Termination type”) to identify offboarding and link to HRMS.
- **Example**: `custom_field_process_type == "Offboarding"` and `custom_field_employee_email` for correlation.

## Best Practice: Configurable Mapping

Allow **admin-configurable mapping** so each tenant can match their ITSM schema:

```json
{
  "deprovision_identifier": {
    "field": "request_type",
    "values": ["Offboarding", "Employee Exit", "Disable Access"]
  },
  "correlation_field": "employee_email",
  "optional_labels": ["offboarding", "access-removal"]
}
```

Support multiple strategies (e.g. type OR labels) and document which takes precedence.

---

# 7. Cloud Infrastructure Integrations

Cloud platforms provide evidence for **infrastructure security and configuration**: IAM, storage, logging, encryption.

## Example Systems

- AWS (IAM, S3, CloudTrail, Config)
- Azure (Entra ID, Storage, Monitor, Policy)
- Google Cloud (IAM, GCS, Cloud Audit Logs)

## Evidence Collected

| Data                 | Description                    | Use in controls        |
|----------------------|--------------------------------|------------------------|
| IAM users/roles      | Principals, policies, attachments | Least privilege, root  |
| Security groups / NSGs | Network rules                 | Network segmentation   |
| Storage permissions  | Bucket/container ACLs, public   | Public access          |
| Logging config       | CloudTrail, audit logs, retention | Audit logging        |
| Encryption config    | KMS, default encryption        | Encryption at rest     |

## Compliance Scenarios (Extensive)

### 7.1 Public storage detection

- **What**: No public read/write on storage (e.g. S3 buckets, GCS).
- **Evidence**: Bucket/container ACLs and policies.
- **Logic**: No bucket has public read or write; FAIL if any do (or exception required).
- **Frameworks**: SOC 2, ISO 27001, PCI-DSS.

### 7.2 Encryption at rest

- **What**: Data at rest encrypted (e.g. default encryption on, KMS).
- **Evidence**: Default encryption flag, KMS key for storage/DB.
- **Logic**: All relevant storage/DB resources have encryption enabled.
- **Frameworks**: SOC 2, ISO 27001 (A.10.1.2), HIPAA, PCI-DSS.

### 7.3 Audit logging enabled

- **What**: Cloud audit/log trails enabled and not disabled.
- **Evidence**: CloudTrail / audit log status, multi-region if required.
- **Logic**: Trail exists and is enabled; retention ≥ policy (e.g. 1 year).
- **Frameworks**: SOC 2 (CC7.2), ISO 27001 (A.12.4.1), HIPAA.

### 7.4 Root / default account usage

- **What**: Root (or equivalent) account not used for daily operations; only for account recovery.
- **Evidence**: IAM root login events, MFA on root.
- **Logic**: No root login in last X days (or only break-glass); root has MFA.
- **Frameworks**: SOC 2, CIS benchmarks.

### 7.5 Excessive IAM privileges

- **What**: No overly broad policies (e.g. `*:*, *`).
- **Evidence**: IAM policies attached to users/roles.
- **Logic**: Detect wildcard actions or resources; flag for review.
- **Frameworks**: SOC 2, least privilege (ISO 27001 A.9.2.3).

### 7.6 Unused credentials and roles

- **What**: Long-unused IAM users/keys/roles should be removed or disabled.
- **Evidence**: Last used for users/access keys/roles.
- **Logic**: Last used > 90 days → flag or FAIL.
- **Frameworks**: SOC 2, ISO 27001.

### 7.7 MFA for console (and privileged) access

- **What**: Human IAM users must have MFA for console (and optionally CLI if applicable).
- **Evidence**: IAM user MFA status.
- **Logic**: All console-capable users have MFA enabled.
- **Frameworks**: SOC 2, CIS benchmarks.

### 7.8 Log retention and immutability

- **What**: Logs retained for required period; optionally immutable.
- **Evidence**: Retention setting, lock/immutability on log storage.
- **Logic**: Retention ≥ 1 year (or policy); critical logs in locked storage.
- **Frameworks**: SOC 2, HIPAA, PCI-DSS.

---

# 8. Version Control Integrations

Code repositories provide evidence for **secure development**: access, review, and branch protection.

## Example Systems

- GitHub
- GitLab
- Bitbucket
- Azure Repos

## Evidence Collected

| Data                  | Description              | Use in controls        |
|-----------------------|--------------------------|------------------------|
| Repository access     | Users, teams, permissions| Access review          |
| Pull/Merge requests   | Approvals, reviewers     | Code review            |
| Branch protection    | Rules for main/default   | Branch protection      |
| Admin privileges      | Repo/org admins          | Privileged access       |
| Default branch        | Name, protection         | Main branch protection |

## Compliance Scenarios (Extensive)

### 8.1 Code review enforcement

- **What**: Changes to main/default require peer review (e.g. 1+ approval).
- **Evidence**: PR/MR approval count, branch protection rules.
- **Logic**: Branch protection requires N approvals; no direct push to main without PR.
- **Frameworks**: SOC 2 (CC8.1), ISO 27001 (A.14.2.4).

### 8.2 Branch protection (main/default)

- **What**: Main (or default) branch is protected: no force push, no delete, optional status checks.
- **Evidence**: Branch protection rules.
- **Logic**: Default branch has protection enabled; force push and delete disabled.
- **Frameworks**: SOC 2, secure SDLC.

### 8.3 Admin and override monitoring

- **What**: Who can bypass protections or has admin; review periodically.
- **Evidence**: Repo/org admin list, “bypass list” for branch protection.
- **Logic**: List admins and bypass users; require justification and review.
- **Frameworks**: SOC 2, least privilege.

### 8.4 Repository access review

- **What**: Periodic review of who has write/admin on repos.
- **Evidence**: Collaborators, team permissions, last review date.
- **Logic**: Access list exists; last review within last 90 days (or policy).
- **Frameworks**: SOC 2 (CC6.1), ISO 27001 (A.9.2.2).

### 8.5 Force push and history rewriting

- **What**: Force push and history rewriting disabled (or restricted).
- **Evidence**: Branch protection “allow force push” = false.
- **Logic**: Protected branches do not allow force push.
- **Frameworks**: SOC 2, integrity.

### 8.6 Default branch name and protection

- **What**: Default branch is consistently named (e.g. main/master) and protected.
- **Evidence**: Default branch name, protection rules.
- **Logic**: Default branch is main or master and has protection.
- **Frameworks**: Operational consistency.

### 8.7 Secrets and sensitive data

- **What**: No committed secrets or high-risk sensitive data (scan in pipeline or post-commit).
- **Evidence**: Scan results from integration or pipeline.
- **Logic**: No high/critical secret findings in default branch (or remediated).
- **Frameworks**: SOC 2, PCI-DSS, secure SDLC.

---

# 9. Device Management Integrations

Device management (MDM/EMM) tracks **corporate devices**: inventory, encryption, patch, policy.

## Example Systems

- Microsoft Intune
- Jamf (macOS/iOS)
- VMware Workspace ONE
- Google Workspace device management

## Evidence Collected

| Data                 | Description           | Use in controls      |
|----------------------|-----------------------|----------------------|
| Device inventory     | ID, type, OS, owner   | Inventory coverage   |
| OS version           | Version, build        | Patch compliance     |
| Disk encryption      | BitLocker, FileVault  | Encryption           |
| Screen lock          | Enabled, timeout      | Screen lock policy   |
| Compliance state     | Compliant / non-compliant | Policy compliance |
| Last sync / seen     | Last check-in         | Stale device         |

## Compliance Scenarios (Extensive)

### 9.1 Disk encryption enforcement

- **What**: All laptops (and optionally desktops) encrypted.
- **Evidence**: Encryption status per device.
- **Logic**: All managed laptops have encryption = true.
- **Frameworks**: SOC 2, ISO 27001 (A.10.1.2), HIPAA.

### 9.2 OS patch compliance

- **What**: Devices on supported OS version and (optionally) patch level.
- **Evidence**: OS version, patch level, EOL dates.
- **Logic**: OS not EOL; critical patches applied within policy window.
- **Frameworks**: SOC 2, ISO 27001 (A.12.6.1).

### 9.3 Device ownership mapping

- **What**: Each corporate device assigned to an employee (or pool).
- **Evidence**: Device owner (user or group).
- **Logic**: No unassigned corporate devices (or in designated pool).
- **Frameworks**: Asset management (ISO 27001 A.8.1.1).

### 9.4 Screen lock policy

- **What**: Screen lock enabled with max timeout (e.g. 5 minutes).
- **Evidence**: Screen lock on/off, timeout value.
- **Logic**: Screen lock enabled and timeout ≤ policy.
- **Frameworks**: SOC 2, physical security.

### 9.5 Device inventory tracking

- **What**: All corporate devices registered and visible in MDM.
- **Evidence**: Device count in MDM; optional HR/asset list.
- **Logic**: Device count matches expected (or variance explained).
- **Frameworks**: SOC 2, asset management.

### 9.6 Stale or inactive devices

- **What**: Devices not seen for X days should be investigated or removed.
- **Evidence**: Last sync / last seen.
- **Logic**: Last seen > 90 days → flag for review.
- **Frameworks**: Operational hygiene.

### 9.7 Jailbreak / root detection

- **What**: Devices must not be jailbroken/rooted for corporate use.
- **Evidence**: Compliance state or jailbreak flag from MDM.
- **Logic**: Compliant = no jailbreak/root.
- **Frameworks**: SOC 2, mobile security.

---

# 10. Security Tool Integrations

Security tools provide **threat detection and response** evidence: EDR, alerts, coverage.

## Example Systems

- CrowdStrike
- SentinelOne
- Microsoft Defender for Endpoint
- Carbon Black

## Evidence Collected

| Data                     | Description            | Use in controls     |
|--------------------------|------------------------|---------------------|
| Endpoint protection status | Installed, healthy   | Coverage            |
| Malware detections       | Count, severity, state | Response            |
| Security alerts          | Type, severity, status | Triage and response |
| Policy compliance        | Policy name, compliant | Policy enforcement  |

## Compliance Scenarios (Extensive)

### 10.1 Endpoint protection coverage

- **What**: All workstations/servers run approved EDR/EPP.
- **Evidence**: Agent installed and healthy per host.
- **Logic**: 100% of in-scope devices have active, healthy agent (or exception).
- **Frameworks**: SOC 2, ISO 27001 (A.12.2.1).

### 10.2 Malware detection response

- **What**: Malware alerts investigated and resolved.
- **Evidence**: Alert status (open/resolved), resolution time.
- **Logic**: Critical/high malware alerts resolved within SLA; no long-open critical.
- **Frameworks**: SOC 2 (CC7.2), ISO 27001 (A.12.2.1).

### 10.3 Security monitoring and response workflow

- **What**: Alerts trigger response (ticket, runbook, or closure with reason).
- **Evidence**: Alert → ticket or action; resolution notes.
- **Logic**: Each high/critical alert has linked ticket or documented resolution.
- **Frameworks**: SOC 2, incident response.

### 10.4 Real-time protection and signatures

- **What**: Real-time protection and signatures up to date.
- **Evidence**: Engine/signature version, last update.
- **Logic**: All agents report recent signature/engine update (e.g. last 7 days).
- **Frameworks**: SOC 2, malware defense.

### 10.5 Tamper protection

- **What**: Tamper protection enabled so agents cannot be disabled by users.
- **Evidence**: Tamper protection setting per policy.
- **Logic**: Policy has tamper protection on.
- **Frameworks**: SOC 2, ISO 27001.

---

# 11. Vulnerability Management Integrations

Vulnerability scanners and VM platforms provide **scan results and remediation status**.

## Example Systems

- Tenable (Nessus)
- Qualys
- Rapid7
- OpenVAS

## Evidence Collected

| Data                  | Description              | Use in controls      |
|-----------------------|---------------------------|---------------------|
| Scan results          | Host, asset, findings     | Coverage, remediation |
| Severity              | Critical, high, medium   | SLA by severity      |
| Patch status          | Fixed, open, accepted risk| Remediation          |
| Scan coverage         | Assets scanned, last scan| Coverage            |

## Compliance Scenarios (Extensive)

### 11.1 Critical vulnerability remediation

- **What**: Critical vulnerabilities fixed within SLA (e.g. 7 days).
- **Evidence**: Finding severity, first seen, resolved date (or risk acceptance).
- **Logic**: All critical findings either resolved within 7 days or have documented exception.
- **Frameworks**: SOC 2, ISO 27001 (A.12.6.1), PCI-DSS.

### 11.2 High vulnerability remediation

- **What**: High-severity findings remediated within longer SLA (e.g. 30 days).
- **Evidence**: Same as above.
- **Logic**: Same pattern with 30-day (or policy) window.
- **Frameworks**: SOC 2, ISO 27001, PCI-DSS.

### 11.3 Scan coverage

- **What**: All in-scope assets scanned at required frequency (e.g. monthly).
- **Evidence**: Last scan date per asset or asset group.
- **Logic**: Every in-scope asset has scan in last 30 days (or policy).
- **Frameworks**: SOC 2, PCI-DSS (11.2).

### 11.4 Scan frequency and schedule

- **What**: Scans run on schedule (e.g. weekly/monthly).
- **Evidence**: Scan history, schedule config.
- **Logic**: At least N scans in last 30 days for in-scope scope.
- **Frameworks**: SOC 2, PCI-DSS.

### 11.5 Risk acceptance and exceptions

- **What**: Open vulnerabilities beyond SLA must have formal risk acceptance.
- **Evidence**: Finding status, exception/risk-acceptance ticket or record.
- **Logic**: Any open critical/high past SLA has valid risk acceptance with expiry.
- **Frameworks**: SOC 2, ISO 27001 (risk treatment).

---

# 12. Password Manager Integrations

Password managers support **credential storage policy** and **shared credential controls**.

## Example Systems

- 1Password
- LastPass
- Bitwarden
- Dashlane
- Keeper

## Evidence Collected

| Data                    | Description                 | Use in controls        |
|-------------------------|-----------------------------|------------------------|
| User enrollment         | Users with vault/account   | Adoption               |
| Shared vaults/items     | Shared credentials, membership | Shared access       |
| Policy compliance       | Policy applied (length, MFA) | Policy enforcement  |
| Admin oversight         | Admin visibility, reports   | Oversight              |

## Compliance Scenarios (Extensive)

### 12.1 Corporate credential storage

- **What**: Employees store work credentials in approved password manager (no spreadsheets/shared docs).
- **Evidence**: Users in password manager; optional: policy attestation or SSO linkage.
- **Logic**: All employees have access to and (optionally) use corporate password manager.
- **Frameworks**: SOC 2, ISO 27001 (A.9.4.3).

### 12.2 Shared credentials restricted and tracked

- **What**: Shared credentials are limited and access is auditable.
- **Evidence**: Shared items, membership, access logs.
- **Logic**: Shared credentials have defined owner and membership list; no unrestricted sharing.
- **Frameworks**: SOC 2, least privilege.

### 12.3 Master password and MFA for vault

- **What**: Vault access protected by strong master password and MFA.
- **Evidence**: MFA status for vault access (from admin or API).
- **Logic**: All users have MFA enabled for password manager.
- **Frameworks**: SOC 2, ISO 27001.

### 12.4 Privileged credential handling

- **What**: Privileged credentials (admin, production) in password manager with approval/checkout.
- **Evidence**: Privileged vaults, checkout/approval logs.
- **Logic**: Privileged credentials require checkout or approval; usage logged.
- **Frameworks**: SOC 2, privileged access.

### 12.5 Offboarding and credential revocation

- **What**: When employee exits, vault access revoked and shared credentials rotated if needed.
- **Evidence**: HRMS exit; password manager access revoked; rotation logs.
- **Logic**: Leaver no longer has access to vault; critical shared credentials rotated (per policy).
- **Frameworks**: SOC 2, leaver process.

---

# 13. Communication Tool Integrations

Collaboration tools (Slack, Teams, etc.) are part of **access and data sharing** control.

## Example Systems

- Slack
- Microsoft Teams
- Google Workspace (Drive, Meet)
- Zoom

## Evidence Collected

| Data                    | Description              | Use in controls      |
|-------------------------|---------------------------|----------------------|
| User/guest list         | Members, guests, external | Guest and access     |
| Channels/teams          | Membership, visibility    | Access review        |
| Admin roles             | Workspace/tenant admins   | Privileged access    |
| Audit logs              | Join/leave, sharing       | Leaver, sharing      |

## Compliance Scenarios (Extensive)

### 13.1 External guests monitored and limited

- **What**: External guests are identified and their access is scoped and reviewed.
- **Evidence**: Guest list, channel/team membership, guest type.
- **Logic**: All guests listed; guest access limited to allowed channels/teams; periodic review.
- **Frameworks**: SOC 2, data sharing (ISO 27001).

### 13.2 Terminated employees removed

- **What**: When employee exits, they are removed from workspace/teams and lose access.
- **Evidence**: HRMS exit; comms tool membership; removal/disable timestamp.
- **Logic**: For each leaver, account disabled or removed from workspace within SLA.
- **Frameworks**: SOC 2 (CC6.1), leaver process.

### 13.3 Sensitive channel and team access

- **What**: Sensitive channels/teams have restricted membership and approval.
- **Evidence**: Channel/team list, membership, visibility (private/public).
- **Logic**: Sensitive channels are private and membership is documented/reviewed.
- **Frameworks**: SOC 2, access control.

### 13.4 Data retention and eDiscovery

- **What**: Retention policy applied; ability to retain/export for legal/audit.
- **Evidence**: Retention settings, export capability.
- **Logic**: Retention ≥ policy (e.g. 7 years for legal); eDiscovery or export available.
- **Frameworks**: SOC 2, legal hold, GDPR.

### 13.5 Admin and bot oversight

- **What**: Workspace/tenant admins and bots are inventoried and reviewed.
- **Evidence**: Admin list, bot/app list, permissions.
- **Logic**: Admin list current; third-party apps/bots approved and scoped.
- **Frameworks**: SOC 2, third-party risk.

---

# 14. Logging and Monitoring Integrations

SIEM and monitoring tools provide **log retention, availability, and alerting** evidence.

## Example Systems

- Splunk
- Datadog
- Elastic (ELK)
- Sumo Logic
- Microsoft Sentinel
- AWS CloudWatch

## Evidence Collected

| Data               | Description              | Use in controls     |
|--------------------|---------------------------|---------------------|
| Log sources        | Types, volume, retention | Retention, coverage |
| Retention settings | Retention period          | Retention policy    |
| Audit log config   | Enabled, immutable        | Audit logging       |
| Alert rules        | Existence, enabled       | Monitoring          |

## Compliance Scenarios (Extensive)

### 14.1 Log retention for required duration

- **What**: Security and audit logs retained for at least policy period (e.g. 1 year, 7 years).
- **Evidence**: Retention setting per log type or index.
- **Logic**: Retention ≥ 1 year (or 7 for legal); critical logs never below minimum.
- **Frameworks**: SOC 2 (CC7.2), ISO 27001 (A.12.4.1), HIPAA, PCI-DSS.

### 14.2 Audit logs enabled and protected

- **What**: Audit logging enabled for critical systems; logs tamper-resistant.
- **Evidence**: Audit log enabled flag; write-once or immutable storage.
- **Logic**: Audit enabled for in-scope systems; critical logs in immutable store.
- **Frameworks**: SOC 2, ISO 27001, HIPAA.

### 14.3 Log coverage (sources)

- **What**: All critical systems send logs to central SIEM/monitoring.
- **Evidence**: Log source list, last event per source.
- **Logic**: Every critical asset or app has active log source; no gap > 24 hours.
- **Frameworks**: SOC 2, CC7.2.

### 14.4 Alerting for critical events

- **What**: Critical security events (e.g. failed admin login, permission change) trigger alerts.
- **Evidence**: Alert rules, last fired, response.
- **Logic**: Defined critical events have corresponding enabled alert rule.
- **Frameworks**: SOC 2, incident detection.

### 14.5 Clock sync (time sources)

- **What**: Log sources use synchronized time (NTP) for accurate correlation.
- **Evidence**: NTP config or time source per host/source.
- **Logic**: All log sources use NTP or approved time source.
- **Frameworks**: SOC 2, forensic accuracy.

---

# 15. Example Automated Controls (End-to-End)

## Control A: Access removed within 24 hours of termination

**Control statement**: Access must be removed (or disabled) within 24 hours of employee termination.

**Evidence sources**:

- **HRMS** → employee exit date (`date_of_exit`), `employee_email`
- **ITSM** → offboarding ticket (created date, status, linked to employee)
- **Identity provider** → account disabled, (if available) disabled timestamp
- **Optional**: Cloud IAM, apps – access removed

**Evaluation logic**:

```
FOR each employee WHERE exit_date exists AND exit_date <= today:
  1. offboarding_ticket = find ITSM ticket (offboarding type, linked to employee email/id)
  2. IF no offboarding_ticket OR ticket created > exit_date + 24h → FAIL
  3. account_disabled = IdP account status = disabled (and optionally disabled_time)
  4. IF account not disabled → FAIL
  5. IF disabled_time > exit_date + 24h → FAIL
  6. ELSE → PASS (for this employee)
OVERALL: PASS only if all leavers in scope pass.
```

**Result**: PASS / FAIL per employee; aggregate PASS only if 100% compliant (or exceptions documented).

---

## Control B: All users have MFA

**Control statement**: All active human users must have multi-factor authentication enabled.

**Evidence sources**: Identity provider (user list, MFA status per user).

**Evaluation logic**:

```
FOR each active user (exclude service accounts per policy):
  IF mfa_enabled != true → FAIL for user
OVERALL: PASS if no failures; else FAIL and report user list.
```

**Result**: PASS / FAIL; on FAIL, list non-MFA users for remediation.

---

## Control C: Offboarding ticket exists for every leaver

**Control statement**: For every employee with an exit date, an offboarding (deprovisioning) ticket must exist in ITSM.

**Evidence sources**: HRMS (exit list, email/employee_id); ITSM (tickets matching offboarding config).

**Evaluation logic**:

```
leavers = HRMS employees WHERE date_of_exit is set AND date_of_exit <= today
FOR each leaver:
  ticket = find ITSM ticket where (type in offboarding_types OR labels match) AND (employee_email or employee_id matches leaver)
  IF no ticket → FAIL for leaver
OVERALL: PASS if every leaver has at least one matching ticket.
```

**Result**: PASS / FAIL; on FAIL, list leavers without ticket.

---

# 16. Cross-Integration and Multi-Source Controls

Many controls need **more than one integration**. Typical patterns:

| Control idea                         | HRMS | IdP | ITSM | Cloud | Other        |
|-------------------------------------|------|-----|------|-------|-------------|
| Leaver access removed in time       | ✓    | ✓   | ✓    | Optional | Comms, VPN |
| Access request approved             | ✓ (manager) | ✓ | ✓   | –     | –           |
| Joiner provisioning                 | ✓    | ✓   | ✓    | –     | –           |
| MFA for all                         | –    | ✓   | –    | –     | –           |
| Change management                   | –    | –   | ✓    | –     | –           |
| Public storage                      | –    | –   | –    | ✓     | –           |
| Dormant account                     | ✓ (optional) | ✓ | –   | –     | –           |

**Implementation**: Normalize evidence into a **canonical model** (e.g. “employee”, “user”, “ticket”, “finding”) and run control logic on normalized records. Correlation keys: `employee_id`, `email`, `account_id`, `ticket_id`.

---

# 17. Evidence Normalization and Storage

## Why normalize?

- Each tool has different field names and formats (e.g. `date_of_exit` vs `termination_date`).
- Controls should be written once against a **canonical schema**, not per-tool.
- Auditors and reports consume a **consistent** view.

## Normalization approach

1. **Ingest**: Fetch raw data from each integration (per org, per tool).
2. **Map**: Transform to canonical entities, e.g.:
   - HRMS employee → `Employee(employee_id, email, exit_date, manager_id, ...)`
   - IdP user → `User(account_id, email, mfa_enabled, last_login, ...)`
   - ITSM ticket → `Ticket(ticket_id, type, created_at, status, requester_email, ...)`
3. **Store**: Persist both **raw** (for audit trail) and **normalized** (for evaluation).
4. **Correlate**: Join on email, employee_id, or org-defined identifier.

## Storage requirements

- **Immutability**: Evidence records should not be edited; new collection overwrites or versions.
- **Timestamps**: Collection time and (if available) source system event time.
- **Link to result**: Each control result links to the evidence records that were used.
- **Retention**: Align with framework (e.g. 1–7 years) and legal hold.

---

# 18. Framework Mapping (SOC 2, ISO 27001, etc.)

| Control area           | SOC 2 (typical) | ISO 27001 (typical) | Example automated checks        |
|------------------------|-----------------|----------------------|----------------------------------|
| Access removal         | CC6.1            | A.9.2.6, A.9.2.3     | HR + IdP + ITSM leaver flow     |
| MFA                    | CC6.1            | A.9.4.2              | IdP MFA status                  |
| Access review          | CC6.1            | A.9.2.2              | IdP + HRMS; review tickets      |
| Change management      | CC8.1            | A.12.1.2             | ITSM change tickets             |
| Incident management   | CC7.2            | A.16.1.5             | ITSM incidents, SLA             |
| Logging and monitoring| CC7.2            | A.12.4.1             | SIEM retention, audit enabled   |
| Encryption             | CC6.1, CC6.6     | A.10.1.2             | Cloud + device encryption       |
| Vulnerability mgmt    | CC7.1, CC7.4     | A.12.6.1             | Vuln scan coverage, remediation |
| Secure development     | CC8.1            | A.14.2.4             | Version control review, branch  |

Mapping should be **configurable per organization** and **per framework** so the same evidence can support multiple frameworks.

---

# 19. Core Concept of Automated Compliance

Every automated compliance rule has **four components**:

1. **Control** – The requirement (e.g. “Access removed within 24 hours of termination”).
2. **Evidence sources** – Which integrations and which fields (e.g. HRMS exit date, ITSM ticket, IdP status).
3. **Evaluation logic** – The rule (thresholds, comparisons, correlation) that produces PASS/FAIL.
4. **Compliance result** – PASS, FAIL, NOT_APPLICABLE, or EXCEPTION, plus list of failing items and attached evidence.

**Example**:

- **Control**: All users must have MFA.
- **Evidence**: Identity provider user list and MFA status.
- **Logic**: For each active user (excluding allowed exceptions), MFA must be enabled.
- **Result**: PASS if no violations; FAIL with list of users without MFA.

---

# 20. Implementation and Operational Guidance

## Integration priority (recommended order)

1. **HRMS** – Source of truth for joiners/leavers.
2. **Identity provider** – Accounts, MFA, disable.
3. **ITSM** – Tickets, approvals, offboarding workflow.
4. **Cloud infrastructure** – IAM, storage, logging (if in scope).
5. **Version control** – If development is in scope.
6. **Device management** – If endpoint compliance is in scope.
7. **Security and vulnerability tools** – EDR, vuln scans, SIEM.

## Configuration and operations

- **Deprovision/offboarding detection**: Use **configurable mapping** (request types, labels, custom fields) so each tenant can match their ITSM.
- **Correlation**: Define **primary keys** (e.g. work email, employee_id) and use them consistently across HRMS, IdP, ITSM.
- **Scheduling**: Run evidence collection and control evaluation on a **schedule** (e.g. daily); support on-demand for testing.
- **Exceptions**: Support **risk acceptance** and **exceptions** with expiry and approval; do not treat as PASS without documentation.
- **Refresh and tokens**: Handle **OAuth refresh** and **token expiry** so integrations stay active; alert on auth failures.
- **Rate limits and errors**: Respect API rate limits; retry with backoff; log and alert on persistent failures.

## Edge cases to handle

- **New integrations**: No historical evidence yet → NOT_APPLICABLE or “pending first run”.
- **Missing data**: Optional field missing → use default or skip that part of logic; document.
- **Time zones**: Normalize all dates to UTC (or org standard) for comparison.
- **Multiple accounts per person**: One employee may have multiple IdP accounts (e.g. legacy); correlate by email or defined rule.
- **Contractors and non-employees**: Define whether they are in scope and how they map (e.g. contractor table in HRMS or separate source).

---

# 21. Key Takeaways

1. **Integrations collect raw evidence** from HRMS, IdP, ITSM, cloud, version control, device, security, and other tools.
2. **Evidence must be normalized** into a canonical model so controls can be written once and applied across tenants and tools.
3. **Controls evaluate compliance logic** using thresholds, correlation, and time windows (e.g. 24 hours for access removal).
4. **Results generate audit-ready evidence** when stored immutably with timestamps and linked to control results.
5. **Cross-integration controls** (e.g. leaver access removal) require HRMS + IdP + ITSM (and optionally cloud, comms) and a clear correlation strategy.
6. **Framework mapping** (SOC 2, ISO 27001, HIPAA, etc.) should be explicit so the same evidence supports multiple frameworks.
7. **Configurable detection** (e.g. for offboarding ticket type) and **exception handling** are essential for real-world deployment.

This document and the scenarios above cover **all major integration categories and typical compliance scenarios** for building a GRC platform with automated control evaluation and extensive, framework-aligned evidence collection.

---


