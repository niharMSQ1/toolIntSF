# Tool integrations — documentation index

This folder documents **implemented** GRC tool integrations mounted from [`app/integrations/api.py`](../app/integrations/api.py). The **generic** data model (G1–G5), table rules, and control mapping are in **[0001 - initialising.md](0001%20-%20initialising.md)**.

---

## Quick reference

| Integration | Category | `evidence_masters.source` | `provider_key` (unified sync) | Primary doc |
|-------------|----------|---------------------------|-------------------------------|-------------|
| **Zoho People** | HRMS (HR / Employee Management) | `zoho_people` | `zoho_people` | [0002 - zoho_integration.md](0002%20-%20zoho_integration.md) |
| **Microsoft Entra** (commercial) | IDP | `iam` (shared IAM catalog; legacy `microsoft_entra` possible) | `microsoft_entra` | [0004 - microsoft_entra_integration.md](0004%20-%20microsoft_entra_integration.md) |
| **Microsoft Entra** (GCC High) | IDP | `iam` / legacy `microsoft_entra_gcc_high` | `microsoft_entra_gcc_high` | [0004 - microsoft_entra_integration.md](0004%20-%20microsoft_entra_integration.md) |
| **Bitbucket Cloud** | DevTools | `bitbucket_cloud` | `bitbucket_cloud` | [0005 - bitbucket_integration.md](0005%20-%20bitbucket_integration.md) |
| **Wiz CSPM** | CSPM | `wiz` | `wiz` | [0006 - wiz_cspm_integration.md](0006%20-%20wiz_cspm_integration.md) |
| **Jira Cloud** | ITSM | `jira_cloud` | `jira_cloud` | [0007 - jira_cloud_integration.md](0007%20-%20jira_cloud_integration.md) |
| **Okta** | IAM / IDP | `iam` (shared IAM catalog; legacy `okta` possible) | `okta` | [0008 - okta_iam_integration.md](0008%20-%20okta_iam_integration.md) |

**Zoho-only note:** [0003 - zoho_people_bottlenecks.md](0003%20-%20zoho_people_bottlenecks.md) — performance and API caveats.

---

## Unified sync (all providers)

One endpoint runs the same collection logic as each provider’s **collect** route when you know `org_id`, `user_id`, and `tool_id`:

| Method | Path |
|--------|------|
| POST | `/api/v1/integrations/sync` |

**Body** (`SyncIntegrationBody`): `org_id`, `user_id`, `tool_id`, optional `provider_key`, optional `evidence_codes`, optional `date_from` / `date_to`.

- If **`provider_key` is omitted**, it is inferred from **`evidence_masters.source`** for that tool’s **`domain_id`**, and for generic IAM (`iam`) from **`configuration_data`** (Okta vs Entra) when needed (see [`sync_dispatch.py`](../app/integrations/core/sync_dispatch.py)).
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
