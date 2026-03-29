# Orca Security — integration

## Overview

This integration calls the Orca Security **REST API** using an **API token** and optional **regional API host**. Authentication and the alert query path follow the public **Cortex XSOAR / Demisto Orca** integration (`Authorization: Token <api_token>`, `POST` `/automations/query/alerts`). Reference implementation:

- [Demisto `Orca.py`](https://github.com/demisto/content/blob/master/Packs/Orca/Integrations/Orca/Orca.py)

The app builds the base URL as **`https://{api_host}/api`** when only a host is supplied (default **`api.orcasecurity.io`**).

## Authentication setup

1. In Orca Security, create or obtain an **API token** with permission to query alerts (per your tenant policy).
2. If your tenant uses a non-default API host, set **`api_host`** (hostname only, e.g. `api.orcasecurity.io`).

## Application configuration (`tool_integrations.configuration_data`)

| Field | Description |
|--------|-------------|
| `provider_key` | Optional; `orca_security`. |
| `api_token` | Orca API token. Alias: `orca_api_token`. |
| `api_host` | API hostname (no scheme). Alias: `orca_api_host`. Default: `api.orcasecurity.io`. |
| `api_base_url` | Optional full HTTPS base including `/api` if you prefer not to use host. Alias: `orca_api_base_url`. |

## Integrated endpoints (this repo)

| App route | Purpose |
|-----------|---------|
| POST `/api/v1/integrations/cspm/orca-security/configure` | Save config, validate token (minimal alert query), optional background collect. |
| GET `/api/v1/integrations/cspm/orca-security/flow` | Readiness. |
| GET `/api/v1/integrations/cspm/orca-security/status` | Masked config. |
| POST `/api/v1/evidence/orca-security/collect` | Evidence collection. |
| POST `/api/v1/integrations/sync` | `provider_key`: `orca_security`. |

### Orca APIs used (Demisto-aligned)

| Operation | HTTP | Path (under base `.../api`) |
|-----------|------|------------------------------|
| Query alerts (collection + validation) | POST | `/automations/query/alerts` |

Request body includes **`limit`**, **`page`**; responses are expected to include JSON with **`status`** == **`success`** on success for validation.

## Evidence codes

| Code | Strategy |
|------|----------|
| EV-721 | Cloud alerts (query) |
| EV-722 | API connectivity (minimal query) |
| EV-723 | Integration metadata |

Seed with `seed_orca_security_evidence_masters(session, tool_id)` (or equivalent SQL). **`evidence_masters.source`** = **`orca_security`**.

## Limitations

- **Pagination** is applied in code with bounded page/limit; very large alert volumes may require tuning or date filters in a future iteration.
- **Official public OpenAPI** for Orca may differ by region; this integration matches the widely used Demisto connector behavior.

## Related

- [0000 - integrations_index.md](0000%20-%20integrations_index.md)
- [CSPM handoff backup](CSPM_INTEGRATION_BACKUP.md)
- [Postman collection](../postman/ToolIntegrations.postman_collection.json) — folder **Orca Security**
