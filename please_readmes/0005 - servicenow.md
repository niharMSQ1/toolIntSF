# ServiceNow — ITSM integration (complete flow)

This document describes the **ServiceNow** integration implemented under [`app/integrations/categories/itsm/servicenow/`](../app/integrations/categories/itsm/servicenow/). The generic table rules, uniqueness constraints, and control mapping flow still come from **[0001 - initialising.md](0001%20-%20initialising.md)**. Generic steps are labeled **G1–G5** below.

---

## Relationship to `0001 - initialising.md`

| Generic step | What it means for ServiceNow |
|--------------|------------------------------|
| **G1** — User selects tool and supplies data | User picks the **ServiceNow** tool and sends `ToolIntegrationPayload` to configure the integration. |
| **G2** — Persist in `tool_integrations` | One row per `(organization_id, tool_id)` is stored in `tool_integrations`; updates are full replace on `configuration_data`. |
| **G3** — Resolve `evidence_masters` | The app resolves the tool's `domain_id` from `tools`, then uses ITSM evidence masters already present for that domain. Configure also runs an idempotent ServiceNow seed step for any ServiceNow-specific codes missing from the catalog. |
| **G4** — `evidence` + `evidence_collection` | For each supported evidence master, the app fetches ServiceNow data, upserts `evidence`, and inserts `evidence_collections` with only the raw ServiceNow records in `tool_evidence`. Failed fetches are not persisted. |
| **G5** — `evidence_mappeds` | The saved `evidence.id` is remapped to controls via `control_evidence_master` using the selected `evidence_master_id`. |

**Uniqueness and update rules**

- `tool_integrations`: unique by `(organization_id, tool_id)` and updated in place.
- `evidence`: unique by `(organization_id, title)` and updated in place.
- `evidence_masters`: in this database, `code` is globally unique, so ServiceNow seed logic must skip any code that already exists anywhere.

---

## Provider registry and code layout

| Item | Value |
|------|-------|
| Registry key | `servicenow` ([`registry.py`](../app/integrations/core/registry.py)) |
| Category | `itsm` |
| Package | [`app/integrations/categories/itsm/servicenow/`](../app/integrations/categories/itsm/servicenow/) |
| Configure routes | [`routers/configure.py`](../app/integrations/categories/itsm/servicenow/routers/configure.py) |
| Collect route | [`routers/evidence.py`](../app/integrations/categories/itsm/servicenow/routers/evidence.py) |
| Orchestration | [`collection_runner.py`](../app/integrations/categories/itsm/servicenow/collection_runner.py) |
| Collector + field mapping | [`collector.py`](../app/integrations/categories/itsm/servicenow/collector.py) |
| ServiceNow API / mock client | [`client.py`](../app/integrations/categories/itsm/servicenow/client.py) |
| ServiceNow seed inventory | [`seed.py`](../app/integrations/categories/itsm/servicenow/seed.py), [`seed_service.py`](../app/integrations/categories/itsm/servicenow/seed_service.py) |
| Unified sync entry | [`sync_dispatch.py`](../app/integrations/core/sync_dispatch.py) |

Routes are mounted from [`app/integrations/api.py`](../app/integrations/api.py).

---

## HTTP API reference

Assume base URL `http://localhost:8002` for local testing in this repo.

### Configure

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/integrations/servicenow/configure` | Save integration config, seed any missing ServiceNow evidence masters, and start background collection. |
| POST | `/itsm/servicenow/integrations` | Alias route for the same behavior. |

**Request body**

```json
{
  "org_id": "<organization UUID>",
  "user_id": "<user UUID>",
  "tool_id": "<ServiceNow tool UUID>",
  "configuration_data": {}
}
```

### Collect

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/evidence/servicenow/collect` | Run ServiceNow evidence collection manually. |

**Request body**

```json
{
  "org_id": "<organization UUID>",
  "user_id": "<user UUID>",
  "tool_id": "<ServiceNow tool UUID>",
  "evidence_codes": ["EV-31", "EV-5"],
  "date_from": "2026-01-01",
  "date_to": "2026-12-31"
}
```

- `evidence_codes` is optional; omit it to collect all supported ServiceNow masters for the tool's domain.
- `date_from` and `date_to` are optional and filter records by source-specific date fields.

### Unified sync

| Method | Path |
|--------|------|
| POST | `/api/v1/integrations/sync` |

Use `provider_key = "servicenow"` when calling the unified sync route.

---

## `configuration_data` fields

Current ServiceNow integration supports these fields in `tool_integrations.configuration_data`:

| Field | Required | Purpose |
|-------|----------|---------|
| `base_url` | No | Optional override for the ServiceNow instance URL. If omitted, the current testing defaults in `client.py` are used. |
| `username` | No | Optional override for basic auth username. |
| `password` | No | Optional override for basic auth password. |
| `sysparm_limit` | No | Optional row limit for Table API requests. Default is `100`. |
| `timeout_seconds` | No | Optional HTTP timeout. Default is `20`. |

**Important note**

- For local testing in the current codebase, ServiceNow credentials are hardcoded in [`client.py`](../app/integrations/categories/itsm/servicenow/client.py) and can be overridden by `configuration_data`.
- Configure responses mask secrets like `password`, but stored `configuration_data` still contains the actual value unless you avoid sending it.

---

## How evidence collection works

### 1. Configure creates the integration shell

When `POST /api/v1/integrations/servicenow/configure` is called:

1. `upsert_tool_integration(...)` saves or updates the `(organization_id, tool_id)` row.
2. `seed_servicenow_evidence_masters(...)` checks the ServiceNow seed inventory and inserts only codes that do not already exist in `evidence_masters`.
3. A background task starts `run_servicenow_evidence_collection_after_configure_background(...)`.

This logic lives in [`routers/configure.py`](../app/integrations/categories/itsm/servicenow/routers/configure.py).

### 2. Collection loads only supported ServiceNow masters

`run_servicenow_evidence_collection(...)` does this:

1. Loads the integration row from `tool_integrations`.
2. Reads `configuration_data`.
3. Lists `evidence_masters` for the tool's domain.
4. Filters them so only masters with:
   - `source` in `{"itsm_catalog", "servicenow"}`
   - and a matching schema in `CODE_TO_SCHEMA`
   are processed.

This avoids trying to collect unsupported `domain_object` masters through the ServiceNow API.

### 3. Each evidence master maps to a ServiceNow source

The collector uses `CODE_TO_SCHEMA` and `SERVICENOW_MAPPING_CONFIG` from:

- [`seed.py`](../app/integrations/categories/itsm/servicenow/seed.py)
- [`collector.py`](../app/integrations/categories/itsm/servicenow/collector.py)

Each supported evidence code resolves to a source such as:

- `incidents`
- `changes`
- `requests`
- `tasks`
- `problems`
- `users`
- `assets`

That source then maps to one ServiceNow table fetcher in [`client.py`](../app/integrations/categories/itsm/servicenow/client.py):

- `incident`
- `change_request`
- `sc_request`
- `task`
- `problem`
- `sys_user`
- `alm_asset`

### 4. Client fetches records from real ServiceNow

`_fetch_table_records(...)` in [`client.py`](../app/integrations/categories/itsm/servicenow/client.py) behaves like this:

- Call ServiceNow Table API using:
  - normalized `base_url`
  - basic auth username/password
  - `Accept: application/json`
  - `sysparm_limit`

Only HTTP 200-style successful responses continue, because `response.raise_for_status()` raises on non-2xx.

### 5. Collector maps raw ServiceNow records into evidence fields

For each evidence master:

1. Fetch source rows.
2. Apply optional date filtering.
3. Map raw ServiceNow fields to the evidence schema using `field_map`.
4. Return:
   - `raw_records`: actual ServiceNow rows
   - `records`: mapped evidence rows

The API response for Swagger now includes a ServiceNow-style payload under:

```json
{
  "service_now_response": {
    "result": [ ...raw ServiceNow rows... ]
  }
}
```

### 6. Persistence only happens on success

For each successful evidence master:

1. `upsert_evidence_full_replace(...)`
2. `remap_evidence_to_controls(...)`
3. `insert_evidence_collection(...)`

Current ServiceNow-specific persistence behavior:

- only successful collections are saved
- failed collections are returned in the API response but are **not** saved to DB
- `tool_evidence` stores only the raw ServiceNow rows, not our wrapper metadata

This success-only behavior is implemented in [`collection_runner.py`](../app/integrations/categories/itsm/servicenow/collection_runner.py).

---

## What gets stored in DB

### `tool_integrations`

Stores:

- `organization_id`
- `tool_id`
- `user_id`
- `configuration_data`

### `evidence`

For each successful evidence master:

- `title` = `evidence_masters.name`
- `code` = `evidence_masters.code`
- `tool_id` = ServiceNow tool id

### `evidence_collections`

For each successful evidence master:

- `source` = `ServiceNow API`
- `name` = evidence master name
- `tool_evidence` = raw ServiceNow records only

Example shape of `tool_evidence`:

```json
[
  {
    "sys_id": "INC-SYS-1001",
    "number": "INC0010001",
    "short_description": "Backup failure on production database"
  }
]
```

### `evidence_mappeds`

After saving evidence, the app remaps controls based on:

- `evidence_master_id`
- `control_evidence_master`

This matches the generic G5 flow from **[0001 - initialising.md](0001%20-%20initialising.md)**.

---

## Swagger behavior

In Swagger UI:

1. Call **configure** first.
2. Then call **collect**.
3. The collect response now shows:
   - app summary fields (`org_id`, `tool_id`, `user_id`)
   - per-evidence status
   - raw ServiceNow payload under `service_now_response.result`

If Swagger becomes slow, pass only a few `evidence_codes` so the response stays small.

---

## Practical test payloads

### Configure — real ServiceNow

```json
{
  "org_id": "019d2487-4c5c-70ce-9dff-ab323084796f",
  "user_id": "019d28d7-0aff-7278-af01-219b95500fed",
  "tool_id": "429e6821-5d20-4792-be43-f2511fdcaf16",
  "configuration_data": {}
}
```

### Collect — small Swagger-friendly test

```json
{
  "org_id": "019d2487-4c5c-70ce-9dff-ab323084796f",
  "user_id": "019d28d7-0aff-7278-af01-219b95500fed",
  "tool_id": "429e6821-5d20-4792-be43-f2511fdcaf16",
  "evidence_codes": ["EV-31", "EV-5", "EV-71"]
}
```

---

## Current implementation notes

- ServiceNow uses the real Table API only.
- ServiceNow uses hardcoded fallback credentials in `client.py` for temporary testing unless overridden in `configuration_data`.
- Repeated configure calls are safe against duplicate `evidence_masters.code` values.
- Unsupported domain-only ITSM objects are intentionally excluded from ServiceNow collection.
- Failed ServiceNow fetches are visible in API output but are not saved to DB.
