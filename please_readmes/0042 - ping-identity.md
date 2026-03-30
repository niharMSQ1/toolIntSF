# Ping Identity — PingOne Platform (IAM)

Code: [`app/integrations/categories/idp/ping_identity/`](../app/integrations/categories/idp/ping_identity/).

This integration targets **PingOne Platform APIs** (PingOne cloud directory and management), documented at [PingOne Platform APIs](https://developer.pingidentity.com/pingone-api/platform/working-with-pingone-apis.html). On‑prem products (e.g. PingFederate server admin APIs) use different endpoints and are **not** covered here.

---

## 1. API documentation review (verified)

### Authentication

| Mechanism | Details (source: PingOne docs) |
|-----------|--------------------------------|
| **OAuth 2.0 client credentials** | `POST {authPath}/{environmentId}/as/token` with `grant_type=client_credentials`. Client authentication via **HTTP Basic** (`client_id:client_secret`) is shown in [Step 1: Get a PingOne access token](https://developer.pingidentity.com/pingone-api/getting-started/create-a-test-environment/step-1-get-access-token.html). |
| **Resource calls** | `Authorization: Bearer {access_token}` per [RFC 6750](https://tools.ietf.org/html/rfc6750), as stated under “Authorization” in [API requests](https://developer.pingidentity.com/pingone-api/foundations/conventions/pingone-api-requests.html). |

### Base URLs and regions

| Service | Pattern (from [Working with PingOne APIs](https://developer.pingidentity.com/pingone-api/platform/working-with-pingone-apis.html)) |
|---------|--------------------------------------------------------------------------------------------------------------------------------------|
| **Management API** | `https://api.pingone.{tld}/v1` — `tld` is region-specific (`com`, `ca`, `eu`, `com.au`, `sg`, `asia`, …). |
| **Authorization server** | `https://auth.pingone.{tld}` — **no** `/v1` on `authPath`. |
| **SCIM** | `https://scim-api.pingone.{tld}` — separate service; not implemented in this module (see below). |

### Core endpoints used in code

| Domain | HTTP | Path (after `/v1`) | Notes |
|--------|------|----------------------|--------|
| Users | GET | `/environments/{envID}/users` | [Users](https://developer.pingidentity.com/pingone-api/platform/users.html); `limit` query documented. |
| Populations | GET | `/environments/{envID}/populations` | [Read All Populations](https://developer.pingidentity.com/pingone-api/platform/populations/read-all-populations.html); `limit`, `filter`. |
| Applications | GET | `/environments/{envID}/applications` | [Read all applications](https://developer.pingidentity.com/pingone-api/platform/applications/applications-1/read-all-applications.html). |
| Audit activities | GET | `/environments/{envID}/activities` | [Audit Activities](https://developer.pingidentity.com/pingone-api/platform/audit-activities.html); **filter including a date range** is required; rate limits lower than other APIs. |

### SCIM

PingOne exposes SCIM at **`scim-api.pingone.{tld}`** (same regional TLD table). This codebase does **not** ship a SCIM client yet; provisioning via SCIM should use Ping’s SCIM API reference when you add it.

### Webhooks / event streams

Real-time login streaming is **not** implemented here. PingOne documents **Subscriptions** and audit **activities** for reporting; `/activities` is used for evidence where a date-bounded filter is applied.

### Pagination / limits

Collection responses use **`_embedded`** (see conventions in [API requests](https://developer.pingidentity.com/pingone-api/foundations/conventions/pingone-api-requests.html)). List operations support `limit` (e.g. populations default 250 in docs).

---

## 2. Integration implementation

| Module | Purpose |
|--------|---------|
| `credentials.py` | `pingone_environment_id`, `pingone_region_tld`, optional `pingone_api_base` / `pingone_auth_base`, Worker `client_id` / `client_secret`, optional `pingone_token_environment_id`. |
| `oauth.py` | Client credentials token exchange. |
| `api_client.py` | Bearer GET for users, populations, applications, activities. |
| `normalize.py` | Maps PingOne JSON → `common_iam_schema` (`IAMIdentity`, …). |
| `collector.py` | Evidence fetch plan per `EV-*` code (documented paths only). |
| `collection_runner.py` | Persists evidence like Okta. |
| `seed_service.py` | Optional IAM `evidence_masters` seed (`iam` source). |
| `routers/configure.py` | Configure, flow, status, `/idp/ping-identity` alias. |
| `routers/data.py` | `GET .../users` → `unified_identities`. |
| `routers/evidence.py` | `POST .../evidence/ping-identity/collect`. |

Secrets are masked in configure responses (`access_token`, `client_secret`).

---

## 3. Configuration (`configuration_data`)

| Field | Description |
|-------|-------------|
| `pingone_environment_id` | Environment UUID (resource API path). **Required.** |
| `pingone_region_tld` | Region TLD (default `com`). |
| `pingone_auth_base` | Override auth host (default `https://auth.pingone.{tld}`). |
| `pingone_api_base` | Override Management API base (default `https://api.pingone.{tld}/v1`). |
| `pingone_token_environment_id` | If Worker app lives in a different env, set for token URL only; else omit. |
| `client_id` / `client_secret` | PingOne **Worker** application (confidential client). |
| `oauth_scope` / `scope` | Optional scope string for token request. |
| `access_token` | Optional pre-issued token; use with `skip_token_exchange: true`. |

---

## 4. Routes

| Method | Path |
|--------|------|
| POST | `/api/v1/integrations/ping-identity/configure` |
| POST | `/idp/ping-identity/configure` |
| GET | `/api/v1/integrations/ping-identity/flow` |
| GET | `/api/v1/integrations/ping-identity/status` |
| GET | `/api/v1/integrations/ping-identity/users` |
| POST | `/api/v1/evidence/ping-identity/collect` |

Unified sync: `provider_key`: `ping_identity` (see `sync_dispatch.py`).

---

## 5. Sample requests / responses

**Configure (body):**

```json
{
  "org_id": "<org-uuid>",
  "user_id": "<user-uuid>",
  "tool_id": "<tool-uuid>",
  "configuration_data": {
    "pingone_environment_id": "<env-uuid>",
    "pingone_region_tld": "com",
    "client_id": "<worker-client-id>",
    "client_secret": "<worker-client-secret>"
  }
}
```

**Token response (PingOne):** JSON with `access_token`, `token_type` (Bearer), `expires_in` (see PingOne token docs).

**Users list (Management API):** JSON with `_embedded.users` per PingOne response model.

---

## 6. Compliance / security

- Use a **Worker** (or equivalent) app with least-privilege **roles** for Management API (PingOne documents role requirements per resource, e.g. Identity Data Admin for users).
- Do not log raw tokens or full PII payloads in production.
- `/activities` has **stricter rate limits** and **retention/query window** rules—see Audit Activities documentation before automation.

---

## 7. Limitations

- **PingOne only** (not PingFederate/PingDirectory on-prem REST in this package).
- **SCIM** and **OIDC browser flows** are not implemented; client credentials + Management API only.
- Evidence codes without a mapped fetch plan return a **not collectable** message until extended using only documented endpoints.
- `activities` filter uses `recordedAt` bounds over **7 days** (within documented max window constraints); adjust in `collector.py` if your tenant requires different SCIM filter syntax.

---

## 8. Postman

Folder **Ping Identity — PingOne (IAM)** in [`postman/ToolIntegrations.postman_collection.json`](../postman/ToolIntegrations.postman_collection.json).
