# Lacework — integration

## Overview

This integration uses **Lacework API v2** on your tenant host `https://{account}.lacework.net`. Authentication follows the official client pattern (see **lacework/go-sdk**): exchange API credentials for a short-lived access token, then call read APIs with the `Authorization` header.

Official references:

- [Lacework API v2 documentation](https://docs.lacework.net/api/v2/docs/) (OpenAPI on your tenant)
- [Generate API access keys and tokens](https://docs.lacework.net/docs/generate-api-access-keys-and-tokens) (Fortinet / Lacework docs)
- [lacework/go-sdk — auth](https://github.com/lacework/go-sdk/blob/main/api/auth.go) and [http](https://github.com/lacework/go-sdk/blob/main/api/http.go) (request shapes)

## Authentication setup

1. In the Lacework / FortiCNAPP console, create an **API key** (typically a JSON file with **key id** and **secret**).
2. Note your **account subdomain** (the hostname prefix before `.lacework.net`).

### Token exchange

- **POST** `https://{account}.lacework.net/api/v2/access/tokens`
- **Headers:** `Content-Type: application/json`, `Accept: application/json`, **`X-LW-UAKS: <secret>`**
- **Body:** `{ "keyId": "<key id>", "expiryTime": 3600 }` (seconds; default one hour in SDKs)
- **Response:** JSON with **`token`** and **`expiresAt`**

Subsequent API calls use **`Authorization: <token>`** (the go-sdk sends the raw JWT string without a `Bearer` prefix).

## Application configuration (`tool_integrations.configuration_data`)

| Field | Description |
|--------|-------------|
| `provider_key` | Optional; `lacework`. |
| `account` | Subdomain only (e.g. `mycompany` for `https://mycompany.lacework.net`). Aliases: `lacework_account`, `account_name`. |
| `key_id` | API key id from the console. Aliases: `api_key_id`, `lacework_key_id`. |
| `secret` | API secret. Aliases: `api_secret`, `lacework_secret`. |
| `api_base_url` | Optional full origin `https://{account}.lacework.net` if you prefer not to pass `account` alone. |

## Integrated endpoints (this repo)

| App route | Purpose |
|-----------|---------|
| POST `/api/v1/integrations/cspm/lacework/configure` | Save config, validate (token + GET UserProfile), optional background collect. |
| GET `/api/v1/integrations/cspm/lacework/flow` | Readiness. |
| GET `/api/v1/integrations/cspm/lacework/status` | Masked config. |
| POST `/api/v1/evidence/lacework/collect` | Evidence collection. |
| POST `/api/v1/integrations/sync` | `provider_key`: `lacework`. |

### Lacework APIs used

| Operation | HTTP | Path |
|-----------|------|------|
| Access token | POST | `/api/v2/access/tokens` |
| Validate (configure) | GET | `/api/v2/UserProfile` |
| Alerts (EV-731) | GET | `/api/v2/Alerts` |
| Organization info (EV-732) | GET | `/api/v2/OrganizationInfo` |

## Evidence codes

| Code | Strategy |
|------|----------|
| EV-731 | Security alerts list |
| EV-732 | Organization info (connectivity) |
| EV-733 | Integration metadata |

Seed with `seed_lacework_evidence_masters(session, tool_id)`. **`evidence_masters.source`** = **`lacework`**.

## Limitations

- Tokens are **short-lived**; each collect run obtains a fresh token (no cached token persistence in `configuration_data` in this phase).
- **Alert list** returns the **first page** as returned by the API; full pagination can be added later if needed.

## Related

- [0000 - integrations_index.md](0000%20-%20integrations_index.md)
- [CSPM handoff backup](CSPM_INTEGRATION_BACKUP.md)
- [Postman collection](../postman/ToolIntegrations.postman_collection.json) — folder **Lacework**
