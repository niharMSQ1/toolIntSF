# Tool integrations — documentation index

This folder documents **implemented** GRC tool integrations mounted from [`app/integrations/api.py`](../app/integrations/api.py). The **generic** data model (G1–G5), table rules, and control mapping are in **[0001 - initialising.md](0001%20-%20initialising.md)**.

---

## Quick reference

| Integration | Category | `evidence_masters.source` | `provider_key` (unified sync) | Primary doc |
|-------------|----------|---------------------------|-------------------------------|-------------|
| **Zoho People** | HRMS (HR / Employee Management) | `zoho_people` | `zoho_people` | [0002 - zoho_integration.md](0002%20-%20zoho_integration.md) |
| **Workday** | HRMS | — (not on unified sync) | — | [0035 - workday.md](0035%20-%20workday.md) |
| **SAP SuccessFactors** | HRMS | — | — | [0036 - sap-successfactors.md](0036%20-%20sap-successfactors.md) |
| **ADP** | HRMS | — | — | [0037 - adp.md](0037%20-%20adp.md) |
| **UKG** | HRMS | — | — | [0038 - ukg.md](0038%20-%20ukg.md) |
| **BambooHR** | HRMS | — | — | [0039 - bamboohr.md](0039%20-%20bamboohr.md) |
| **Paycom** | HRMS | — | — | [0040 - paycom.md](0040%20-%20paycom.md) |
| **Rippling** | HRMS | — | — | [0041 - rippling.md](0041%20-%20rippling.md) |
| **Microsoft Entra** (commercial) | IDP | `iam` (shared IAM catalog; legacy `microsoft_entra` possible) | `microsoft_entra` | [0004 - microsoft_entra_integration.md](0004%20-%20microsoft_entra_integration.md) |
| **Microsoft Entra** (GCC High) | IDP | `iam` / legacy `microsoft_entra_gcc_high` | `microsoft_entra_gcc_high` | [0004 - microsoft_entra_integration.md](0004%20-%20microsoft_entra_integration.md) |
| **Bitbucket Cloud** | DevTools | `bitbucket_cloud` | `bitbucket_cloud` | [0005 - bitbucket_integration.md](0005%20-%20bitbucket_integration.md) |
| **GitHub** | DevTools | — (data + webhooks; not on unified sync) | — | [0029 - github.md](0029%20-%20github.md) |
| **Azure DevOps** | DevTools | — | — | [0030 - azure-devops.md](0030%20-%20azure-devops.md) |
| **Jenkins** | DevTools | — | — | [0031 - jenkins.md](0031%20-%20jenkins.md) |
| **CircleCI** | DevTools | — | — | [0032 - circleci.md](0032%20-%20circleci.md) |
| **Argo CD** | DevTools | — | — | [0033 - argocd.md](0033%20-%20argocd.md) |
| **TeamCity** | DevTools | — | — | [0034 - teamcity.md](0034%20-%20teamcity.md) |
| **Wiz CSPM** | CSPM | `wiz` | `wiz` | [0006 - wiz_cspm_integration.md](0006%20-%20wiz_cspm_integration.md) |
| **Prisma Cloud** | CSPM | `prisma_cloud` | `prisma_cloud` | [0009 - prisma-cloud.md](0009%20-%20prisma-cloud.md) |
| **Microsoft Defender for Cloud** | CSPM | `defender_cloud` | `defender_cloud` | [0010 - defender-cloud.md](0010%20-%20defender-cloud.md) |
| **Orca Security** | CSPM | `orca_security` | `orca_security` | [0011 - orca-security.md](0011%20-%20orca-security.md) |
| **Lacework** | CSPM | `lacework` | `lacework` | [0012 - lacework.md](0012%20-%20lacework.md) |
| **Aqua Security** (self-hosted CSP) | CSPM | `aqua_security` | `aqua_security` | [0013 - aqua-security.md](0013%20-%20aqua-security.md) |
| **Sysdig Secure** | CSPM | `sysdig_secure` | `sysdig_secure` | [0014 - sysdig-secure.md](0014%20-%20sysdig-secure.md) |
| **CrowdStrike Falcon** | EDR / VM | `crowdstrike_falcon` | `crowdstrike_falcon` | [0015 - crowdstrike-falcon.md](0015%20-%20crowdstrike-falcon.md) |
| **Microsoft Defender for Endpoint** | EDR / VM | `defender_for_endpoint` | `defender_for_endpoint` | [0016 - defender-for-endpoint.md](0016%20-%20defender-for-endpoint.md) |
| **SentinelOne** | EDR / VM | `sentinelone` | `sentinelone` | [0017 - sentinelone.md](0017%20-%20sentinelone.md) |
| **Tenable.io** | VM | `tenable_io` | `tenable_io` | [0018 - tenable-io.md](0018%20-%20tenable-io.md) |
| **Qualys VMDR / VM** | VM | `qualys` | `qualys` | [0019 - qualys.md](0019%20-%20qualys.md) |
| **Rapid7 InsightVM** | VM | `rapid7_insightvm` | `rapid7_insightvm` | [0020 - rapid7-insightvm.md](0020%20-%20rapid7-insightvm.md) |
| **Tanium** | EDR | `tanium` | `tanium` | [0021 - tanium.md](0021%20-%20tanium.md) |
| **Asana** | Project management | — (not on unified sync) | — | [0022 - asana.md](0022%20-%20asana.md) |
| **Monday.com** | Project management | — | — | [0023 - monday.md](0023%20-%20monday.md) |
| **Microsoft Planner** (Graph) | Project management | — | — | [0024 - microsoft-planner.md](0024%20-%20microsoft-planner.md) |
| **Smartsheet** | Project management | — | — | [0025 - smartsheet.md](0025%20-%20smartsheet.md) |
| **ClickUp** | Project management | — | — | [0026 - clickup.md](0026%20-%20clickup.md) |
| **Notion** | Project management | — | — | [0027 - notion.md](0027%20-%20notion.md) |
| **Linear** | Project management | — | — | [0028 - linear.md](0028%20-%20linear.md) |
| **Jira Cloud** | ITSM | `jira_cloud` | `jira_cloud` | [0007 - jira_cloud_integration.md](0007%20-%20jira_cloud_integration.md) |
| **Okta** | IAM / IDP | `iam` (shared IAM catalog; legacy `okta` possible) | `okta` | [0008 - okta_iam_integration.md](0008%20-%20okta_iam_integration.md) |
| **Ping Identity (PingOne)** | IAM / IDP | `iam` / `ping_identity` | `ping_identity` | [0042 - ping-identity.md](0042%20-%20ping-identity.md) |
| **CyberArk Identity** | IAM / IDP | `iam` / legacy `cyberark_identity` | `cyberark_identity` | [0043 - cyberark-identity.md](0043%20-%20cyberark-identity.md) |
| **SailPoint IdentityNow** | IAM / IDP | `iam` / legacy `sailpoint_identitynow` | `sailpoint_identitynow` | [0044 - sailpoint-identity.md](0044%20-%20sailpoint-identity.md) |
| **Google Workspace** | IAM / IDP | `iam` / legacy `google_workspace` | `google_workspace` | [0045 - google-workspace.md](0045%20-%20google-workspace.md) |
| **ForgeRock** | IAM / IDP | `iam` / legacy `forgerock` | `forgerock` | [0046 - forgerock.md](0046%20-%20forgerock.md) |
| **OneLogin** | IAM / IDP | `iam` / legacy `onelogin` | `onelogin` | [0047 - onelogin.md](0047%20-%20onelogin.md) |
| **JumpCloud** | IAM / IDP | `iam` / legacy `jumpcloud` | `jumpcloud` | [0048 - jumpcloud.md](0048%20-%20jumpcloud.md) |

**Zoho-only note:** [0003 - zoho_people_bottlenecks.md](0003%20-%20zoho_people_bottlenecks.md) — performance and API caveats.

---

## Unified sync (all providers)

One endpoint runs the same collection logic as each provider’s **collect** route when you know `org_id`, `user_id`, and `tool_id`:

| Method | Path |
|--------|------|
| POST | `/api/v1/integrations/sync` |

**Body** (`SyncIntegrationBody`): `org_id`, `user_id`, `tool_id`, optional `provider_key`, optional `evidence_codes`, optional `date_from` / `date_to`.

- If **`provider_key` is omitted**, it is inferred from **`evidence_masters.source`** for that tool’s **`domain_id`**, and for generic IAM (`iam`) from **`configuration_data`** when needed (PingOne, CyberArk, SailPoint, Google Workspace, ForgeRock, JumpCloud, OneLogin, Okta, Microsoft Entra—see [`sync_dispatch.py`](../app/integrations/core/sync_dispatch.py)).
- If ambiguous, pass the matching **`provider_key`** explicitly.

---

## Typical end-to-end flow (all tools)

1. **G1** — User selects a tool and submits credentials/config (`ToolIntegrationPayload` for configure routes).
2. **G2** — **`POST …/configure`** upserts **`tool_integrations`** (one row per `(organization_id, tool_id)`; **`configuration_data`** full replace on update).
3. **G3** — **`evidence_masters`** for the tool’s **`domain_id`** must exist before collect (seed **manually** or via product **`seed_*`** helpers when needed — **not** automatically on configure).
4. **OAuth tools** — User completes browser OAuth where applicable; callback stores tokens in **`configuration_data`**.
5. **G4** — Evidence collection (background after configure and/or **`POST …/collect`** / **`POST /integrations/sync`**) calls vendor APIs, **`upsert_evidence_full_replace`** on **`evidence`**, **`insert_evidence_collection`** ( **`source`** = **`tools.name`**) for each run.
6. **G5** — **`remap_evidence_to_controls`** links **`evidence`** to controls via **`control_evidence_master`** for the **`evidence_master_id`**.

---

## Where routes are registered

[`app/integrations/api.py`](../app/integrations/api.py) — `mount_integration_routes(app)`.

**Postman:** [`postman/ToolIntegrations.postman_collection.json`](../postman/ToolIntegrations.postman_collection.json).

**Local tester UI:** [`static/index.html`](../static/index.html) (subset of providers).
