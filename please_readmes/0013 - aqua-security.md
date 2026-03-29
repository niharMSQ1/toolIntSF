# Aqua Security — integration (self-hosted CSP)

## Overview

This integration targets **self-hosted Aqua CyberCenter (CSP)** with the **REST API v1** on your console origin (for example `https://aqua.example.com:8443`). Authentication follows the same pattern as **aquasecurity/terraform-provider-aquasec** `GetCspAuthToken`: **POST** `/api/v1/login` with JSON `id` and `password`, then **Bearer** token on subsequent requests.

References:

- [Aqua API / developer documentation](https://cloud.aquasec.com/developers/) (product-specific; your console may expose Swagger/OpenAPI).
- [terraform-provider-aquasec — `GetCspAuthToken`](https://github.com/aquasecurity/terraform-provider-aquasec/blob/main/client/client.go) (login request/response shape).

**Not in scope here:** Aqua **SaaS** (Wave) uses a different **sign-in** and token flow against regional hosts; use a product-specific connector or extend this integration later if needed.

## Authentication setup

1. Use an Aqua console user allowed to call the API (per your RBAC).
2. Collect:
   - **Console base URL** — HTTPS origin only (no `/api` path), e.g. `https://aqua.example.com:8443`.
   - **Login id** — maps to JSON field `id` on `POST /api/v1/login`.
   - **Password** — maps to JSON field `password`.

Optional: **`verify_tls`** (default `true`). Set to `false` only if you use a private CA and accept TLS verification disabled client-side.

## Application configuration (`tool_integrations.configuration_data`)

| Field | Description |
|--------|-------------|
| `provider_key` | Optional; `aqua_security`. |
| `api_base_url` | Console origin. Aliases: `aqua_api_base_url`, `console_url`. |
| `login_id` | User id for login. Aliases: `id`, `username`, `aqua_username`. |
| `password` | Password. Alias: `aqua_password`. |
| `verify_tls` | Optional bool; default verify server certificate. |

## Integrated endpoints (this repo)

| App route | Purpose |
|-----------|---------|
| POST `/api/v1/integrations/cspm/aqua-security/configure` | Save config, validate (login + GET hosts), optional background collect. |
| GET `/api/v1/integrations/cspm/aqua-security/flow` | Readiness. |
| GET `/api/v1/integrations/cspm/aqua-security/status` | Masked config. |
| POST `/api/v1/evidence/aqua-security/collect` | Evidence collection. |
| POST `/api/v1/integrations/sync` | `provider_key`: `aqua_security`. |

### Aqua CSP APIs used

| Operation | HTTP | Path |
|-----------|------|------|
| Login | POST | `/api/v1/login` |
| Hosts (EV-741) | GET | `/api/v1/hosts` |
| Images (EV-742) | GET | `/api/v1/images` |

## Evidence codes

| Code | Strategy |
|------|----------|
| EV-741 | Registered hosts |
| EV-742 | Container images |
| EV-743 | Integration metadata |

Seed with `seed_aqua_security_evidence_masters(session, tool_id)`. **`evidence_masters.source`** = **`aqua_security`**.

## Limitations

- **Self-hosted CSP only** in this phase (see SaaS note above).
- JWT from login is **not** persisted; each run logs in again (same pattern as other short-lived token integrations).
- Response shapes depend on your Aqua version; large inventories may require pagination enhancements later.

## Related

- [0000 - integrations_index.md](0000%20-%20integrations_index.md)
- [CSPM handoff backup](CSPM_INTEGRATION_BACKUP.md)
- [Postman collection](../postman/ToolIntegrations.postman_collection.json) — folder **Aqua Security**
