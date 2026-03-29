# Sysdig Secure — integration

## Overview

This integration uses the **Sysdig HTTP API** with a **Bearer API token** (user token or service account) against your **regional API hostname** (SaaS) or **on-prem API** host. Request shapes follow the same conventions as **sysdig-sdk-python** `sdcclient` (`Authorization: Bearer`, `GET /api/user/me`, etc.).

Official references:

- [Sysdig API](https://docs.sysdig.com/en/developer-tools/sysdig-api/) — authentication and regional endpoints
- [Retrieve the Sysdig API Token](https://docs.sysdig.com/en/administration/retrieve-the-sysdig-api-token)
- [sysdig-sdk-python — `_SdcCommon`](https://github.com/sysdiglabs/sysdig-sdk-python/blob/master/sdcclient/_common.py) (headers and `/api/user/me`)

## Authentication setup

1. In Sysdig Secure (or your admin), create or copy an **API token** (user profile or service account per your policy).
2. Set **`api_base_url`** to the **API** hostname for your region (SaaS), for example:
   - US East: `https://api.us1.sysdig.com`
   - EU Central: `https://api.eu1.sysdig.com`  
   See the Sysdig docs table for other regions.
3. For **on-premises**, use the form `https://api.sysdig.<dnsName>` from your installation (per Sysdig documentation).

## Application configuration (`tool_integrations.configuration_data`)

| Field | Description |
|--------|-------------|
| `provider_key` | Optional; `sysdig_secure`. |
| `api_token` | Sysdig API token. Aliases: `sysdig_api_token`, `token`. |
| `api_base_url` | Regional API origin (no path). Aliases: `sysdig_api_base_url`, `sdc_url`. Default in app: `https://api.us1.sysdig.com` if omitted. |
| `verify_tls` | Optional bool (default `true`); set `false` only for private CAs if needed. |

## Integrated endpoints (this repo)

| App route | Purpose |
|-----------|---------|
| POST `/api/v1/integrations/cspm/sysdig-secure/configure` | Save config, validate (GET `/api/user/me`), optional background collect. |
| GET `/api/v1/integrations/cspm/sysdig-secure/flow` | Readiness. |
| GET `/api/v1/integrations/cspm/sysdig-secure/status` | Masked config. |
| POST `/api/v1/evidence/sysdig-secure/collect` | Evidence collection. |
| POST `/api/v1/integrations/sync` | `provider_key`: `sysdig_secure`. |

### Sysdig APIs used

| Operation | HTTP | Path |
|-----------|------|------|
| Validate (configure) | GET | `/api/user/me` |
| Connected agents (EV-751) | GET | `/api/agents/connected` |
| Current user (EV-752) | GET | `/api/user/me` |

## Evidence codes

| Code | Strategy |
|------|----------|
| EV-751 | Connected agents inventory |
| EV-752 | Current user / API connectivity |
| EV-753 | Integration metadata |

Seed with `seed_sysdig_secure_evidence_masters(session, tool_id)`. **`evidence_masters.source`** = **`sysdig_secure`**.

## Limitations

- **Response shapes** vary by Sysdig product version; large lists are not paginated in this phase.
- **EV-752** returns user context — treat as sensitive and redact in downstream reporting if required.

## Related

- [0000 - integrations_index.md](0000%20-%20integrations_index.md)
- [CSPM handoff backup](CSPM_INTEGRATION_BACKUP.md)
- [Postman collection](../postman/ToolIntegrations.postman_collection.json) — folder **Sysdig Secure**
