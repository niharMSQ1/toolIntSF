# Initialising — generic tool integrations & evidence flow

This document is the **canonical** description of how integrations use the GRC tables and persistence layer. **Per-product** setup (OAuth URLs, env vars, routes) lives in **[0000 - integrations_index.md](0000%20-%20integrations_index.md)** and the numbered guides it links to.

**Code entry points**

- HTTP routes: [`app/integrations/api.py`](../app/integrations/api.py)
- Shared persistence: [`app/integrations/core/persistence/tool_integration_service.py`](../app/integrations/core/persistence/tool_integration_service.py)
- Unified sync dispatcher: [`app/integrations/core/sync_dispatch.py`](../app/integrations/core/sync_dispatch.py)

---

## 1. Request shape (all integrations)

Clients send a common envelope; only **`configuration_data`** changes by product.

```json
{
  "org_id": "<uuid>",
  "user_id": "<uuid>",
  "tool_id": "<uuid>",
  "configuration_data": { }
}
```

- **`org_id`** — Organization the evidence belongs to.
- **`user_id`** — Actor for audit fields (e.g. **`evidence_collections.updated_by`**).
- **`tool_id`** — Which catalog **`tools`** row this integration uses (also drives **`evidence.domain_id`** resolution via **`tools.domain_id`**).
- **`configuration_data`** — Vendor-specific JSON (tokens, URLs, OAuth state, API keys, etc.). Stored on **`tool_integrations`**, not on **`evidence_masters`**.

---

## 2. Tables and roles (mental model)

| Table | Role |
|--------|------|
| **`domains`** | Business/domain boundary; **`tools`** and **`evidence_masters`** hang off **`domain_id`**. |
| **`tools`** | Product definition (`name`, `domain_id`, …). **`tool_id`** in requests points here. |
| **`organizations`** | Tenant; **`org_id`** scopes **`evidence`**. |
| **`tool_integrations`** | One row per **`(organization_id, tool_id)`**: saved credentials/config. **Upsert only** — never duplicate the pair. |
| **`evidence_masters`** | Catalog of what *can* be collected for a **domain**: `code`, `name`, `description`, **`source`** (catalog tag), `domain_id`. **Not** the live payload. |
| **`control_evidence_master`** | Links an **`evidence_masters.id`** to one or more **`controls.id`**. |
| **`evidence`** | Org-scoped “current” evidence record per logical item (see uniqueness below). |
| **`evidence_collections`** | **One new row per collect run** — history / snapshot (`tool_evidence` JSON). |
| **`evidence_mappeds`** | Links **`evidence.id`** to **`controls`** (polymorphic `evidenceable_type` / `evidenceable_id`). |

Reference ERDs (if present): folder **`db_structure`**.

---

## 3. Uniqueness and upsert rules

### `tool_integrations`

- **`(organization_id, tool_id)`** must be unique.
- On re-configure: **update** the existing row; **`configuration_data`** is replaced in full (no partial merge of stale keys unless the product explicitly merges).

**Reconfiguring (operational note)** — When you need a clean re-setup for a given **organization** and **tool**, **delete** the existing row from **`tool_integrations`** for that **`(organization_id, tool_id)`** first, **then** run **configure** again with the new credentials/config. Do not rely on partial updates alone if you must drop stale OAuth state, tokens, or other fields that would otherwise linger in JSON.

### `evidence`

- For a given **`organization_id`**, **`title`** is treated as the stable key for “this evidence line item” (title comes from **`evidence_masters.name`** on collect).
- When the same master is collected again: **update** the same **`evidence`** row (**`upsert_evidence_full_replace`** in code).
- Updates are **full replace** for the fields the service sets (`code`, `description`, `status`, `tool_id`, …).

### `evidence_collections`

- **Always insert** a **new** row for each successful (or failed) collection attempt for that evidence. This preserves **history**; multiple rows can share the same **`evidence_id`**.

---

## 4. Configure vs catalog (`evidence_masters`)

**Configure** (`POST …/configure` per product) **persists `tool_integrations` only** — it does **not** automatically insert **`evidence_masters`**.

- **Catalog rows** are created **when you choose** (manual SQL, admin script, or calling the product **`seed_*_evidence_masters`** helpers in code — see each integration’s `seed_service.py`).
- Until **`evidence_masters`** exist for the tool’s **`domain_id`**, collect will fail with a message to seed the catalog first.

### `evidence_masters.source` (catalog tag)

This column is a **generic label** for the *type* of catalog row (e.g. `zoho_people`, `jira_cloud`, `wiz`, **`iam`** for shared IAM EV-* codes across Okta and Microsoft Entra). It is **not** the human display name of the tool.

Collection code filters masters by **`source`** (and by **`tools.domain_id`** via **`tool_id`**).

---

## 5. End-to-end collection flow (generic)

Applies to every integration that uses the shared persistence helpers.

1. **Resolve integration** — Load **`tool_integrations`** for **`(org_id, tool_id)`**; read **`configuration_data`** for API calls.
2. **Resolve domain** — From **`tools`**, read **`domain_id`** for **`tool_id`**.
3. **Load masters** — Select **`evidence_masters`** where **`domain_id`** matches, and **`source`** matches what that integration expects (e.g. `zoho_people`, or IAM tuple including `iam`).
4. **For each master** (usually ordered by product-defined name/code order):
   - Call the vendor API and build a JSON payload.
   - **`upsert_evidence_full_replace`** → **`evidence`**  
     - `organization_id` ← `org_id`  
     - `title` ← master **`name`**  
     - `code` ← master **`code`**  
     - `description` ← master **`description`** (nullable)  
     - `status` ← `collected`  
     - `tool_id` ← request **`tool_id`**  
     - **`due_date`** — on **first insert only**, default is **UTC today + 30 days**; subsequent collects **do not** move `due_date` on update.  
   - **`remap_evidence_to_controls`** → delete old **`evidence_mappeds`** for that **`evidence_id`**, then insert rows from **`control_evidence_master`** for this **`evidence_master_id`**.  
     - **`evidenceable_type`** = `App\Models\Control`  
     - **`evidenceable_id`** = each **`control_id`** linked to that master.  
   - **`insert_evidence_collection`** → new **`evidence_collections`** row:  
     - **`evidence_id`** — the evidence row above  
     - **`evidence_from`** — `tool` (CHECK constraint in DB)  
     - **`source`** — **`tools.name`** for **`tool_id`** (resolved in code; not the API vendor string)  
     - **`name`** — master **`name`**  
     - **`tool_evidence`** — collected JSON  
     - **`updated_by`** — **`user_id`** from the request  

On **failure** for a master, the code may create a failed **`evidence`** row and still append an **`evidence_collections`** row with error metadata (see **`insert_evidence_collection_after_failed_collect`**).

---

## 6. Two ways to trigger collection

| Mechanism | Purpose |
|-----------|---------|
| **Provider-specific** `POST …/evidence/.../collect` | Directly runs that product’s `run_*_evidence_collection`. |
| **Unified** `POST /api/v1/integrations/sync` | Same runners; **`provider_key`** optional when it can be inferred from **`evidence_masters.source`** and (for IAM) **`configuration_data`**. |

Details: [0000 - integrations_index.md](0000%20-%20integrations_index.md).

---

## 7. Sample payload (Zoho-style)

`configuration_data` is only an example; each tool has its own keys.

```json
{
  "org_id": "019ce23e-66b9-71fa-8223-8d66f1925bd5",
  "user_id": "019ce23e-67e0-702e-957d-ab3af1f8a619",
  "tool_id": "019ce23d-c16d-7304-8a5b-3500e3cbadbc",
  "configuration_data": {
    "client_id": "1000.xxx",
    "client_secret": "***",
    "redirect_uri": "http://localhost:8006/hrms/zoho-people/callback",
    "region": "in"
  }
}
```

---

## 8. `evidence_mappeds` — mapping evidence to controls (summary)

1. After **`evidence`** exists, use **`evidence_master_id`** from the **`evidence_masters`** row that was collected.
2. Query **`control_evidence_master`** for that **`evidence_master_id`** → list of **`control_id`** values.
3. Insert **`evidence_mappeds`**: **`evidence_id`**, **`evidenceable_type`** = `App\Models\Control`, **`evidenceable_id`** = each **`control_id`**.

Relationship: one master → many controls; one collect → many **`evidence_mappeds`** rows (one per control).

---

## 9. Checklist for new integrations

1. Register routers in [`app/integrations/api.py`](../app/integrations/api.py).
2. Implement **`run_*_evidence_collection`** using **`list_evidence_masters`** → **`upsert_evidence_full_replace`** → **`remap_evidence_to_controls`** → **`insert_evidence_collection`** (with **`tool_id`**).
3. Define **`evidence_masters.source`** value(s) and seed catalog rows for the domain when needed.
4. Document configure/OAuth/collect in a new `please_readmes` file and add a row to **[0000](0000%20-%20integrations_index.md)**.
