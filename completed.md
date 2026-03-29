# Completed integrations — Vanta-style model vs this repo

## How Vanta structures it (reference)

Vanta’s marketplace uses a consistent pattern:

1. **Category** — e.g. *Cloud Infrastructure*, *Identity Provider*, *Vulnerability Scanner*, *Ticketing*.
2. **Integration (tool)** — one vendor connector (e.g. **AWS**) under that category.
3. **Scope** — what to pull in (accounts, orgs, projects, groups, regions).
4. **Supported resources / capabilities** — many asset or control types behind one connector (EC2, S3, IAM, GuardDuty, … for AWS).
5. **Evidence** — continuous checks and collected proof mapped to frameworks (SOC 2, ISO 27001, etc.).

So it is **category → one or many tools → scoped sync → many evidence rows / controls**.

## How this repo aligns (your requirement)

| Vanta idea | This codebase |
| :-- | :-- |
| Category | Domains in `mappings.txt` (e.g. *CSPM*, *Security / Vulnerability Management*, *ITSM*) — GRC **category** |
| Integration card | A **tool** row + `tool_integrations` with `configuration_data` |
| Connect / credentials | `POST .../configure` per provider (OAuth, API token, service account, IAM role ARN, etc.) |
| Resource filter (orgs, accounts, …) | Provider-specific scope: e.g. Snyk `org_ids` / `group_id`, Bitbucket workspaces, Entra cloud, **AWS `role_arn`** (AssumeRole) |
| Pull data / tests | `POST .../evidence/.../collect` or `POST /api/v1/integrations/sync` (`provider_key` or inferred from `evidence_masters.source`) |
| Evidence for audits | `evidence_masters` (codes like `EV-*`) → `evidence_collections.tool_evidence` |

Unified sync is implemented in `app/integrations/core/sync_dispatch.py` (`provider_key` ↔ `evidence_masters.source`).

---

## Category → tools (one-to-many)

Each **category** can list **multiple tools**. Each tool is one connector; bullets summarize **what it is used for** (Vanta’s “capabilities / supported resources” analogue — not an exhaustive asset list).

| Category | Tools | Scope & capabilities (summary) |
| :-- | :-- | :-- |
| **CSPM** | **Wiz** | Cloud security posture: GraphQL API — issues, vulnerability findings, cloud resources / projects, users; service account OAuth to Wiz tenant. |
| **Cloud / Infrastructure** | **Wiz**, **AWS** | **Wiz:** same as CSPM for cloud-aligned evidence. **AWS:** `configuration_data.role_arn` (STS AssumeRole) + optional `external_id`, `region`; boto3 collectors cover a Vanta-core-style slice: compute (EC2, Lambda, ECS), IAM users, S3, RDS, DynamoDB, SageMaker, SSM, Resource Groups Tagging, Config, Organizations, Macie, GuardDuty, and STS identity. Grant the assumed role broad read-only access (e.g. AWS managed `ReadOnlyAccess`) or a custom policy listing those service actions; optional services (Organizations, Macie, Config, GuardDuty) return structured “not enabled” or permission errors when unavailable. |
| **Security / Vulnerability Management** | **Snyk** | Snyk REST + v1 — org or group scope, projects, issues (dependency / code-style); token or OAuth client credentials; regional API host. |
| **DevOps / CI-CD / Source Control** | **Bitbucket Cloud** | Repositories, pipelines, pull requests, workspaces (OAuth + workspace selection). |
| **HR / Employee Management** | **Zoho People** | HR evidence via Zoho People APIs (OAuth to People). |
| **IAM / Identity Compliance** | **Okta** | SSWS / org URL — users, groups, policies, apps (per your Okta evidence map). |
| | **Microsoft Entra** | Microsoft Graph — commercial + GCC High variants; directory, sign-in, conditional access, etc. |
| **ITSM** | **Jira Cloud** | Jira Cloud REST — tickets aligned to ITSM evidence codes. |
| **Compliance / GRC** | — | No separate “GRC platform” connector; policy-style evidence may be manual or future tool. |
| **Project Management / Productivity** | — | No PM connector yet. |
| **Physical Security System** | — | No connector yet. |

---

## AWS payload (configure)

`POST /api/v1/integrations/cloud/aws/configure` accepts a body like:

```json
{
  "org_id": "<uuid>",
  "user_id": "<uuid>",
  "tool_id": "<uuid>",
  "configuration_data": {
    "provider_key": "aws",
    "role_arn": "arn:aws:iam::<account-id>:role/<role-name>",
    "region": "us-east-1",
    "external_id": ""
  }
}
```

**Regions vs `role_arn`:** IAM role ARNs are **account-scoped** (`arn:aws:iam::123456789012:role/...`) and **do not contain a region**. The account ID can be parsed from the ARN; regions cannot. To **discover region names** after AssumeRole, set **`"region": "auto"`** — the integration calls EC2 `DescribeRegions` (requires `ec2:DescribeRegions`) and uses that list for multi-region EC2 evidence. If `region` is omitted, it defaults to **`us-east-1`** (single-region behavior).

Optional **`sts_region`**: regional endpoint used only for the STS `AssumeRole` call (defaults to `us-east-1`).

The server process must have **AWS credentials** (env, shared profile, or instance role) that are allowed to call `sts:AssumeRole` into `role_arn`. Optional `external_id` for cross-account trust.

---

*Wiz is listed under both **CSPM** and **Cloud / Infrastructure** because one connector serves both mapping domains. Categories marked “—” have no dedicated connector in this repo yet.*
