# Prisma Cloud (Palo Alto Networks) — CSPM integration

## Overview

This integration uses the **Prisma Cloud CSPM REST API** documented on **Palo Alto Networks developer documentation** ([pan.dev](https://pan.dev/prisma-cloud/api/cspm/)). It authenticates with an **access key** (Access Key ID + Secret Key), obtains a **JWT**, and calls selected read endpoints to populate GRC evidence (`evidence_masters` with `source=prisma_cloud`).

The in-app integration does **not** invent API paths: it implements the same flows described in the official docs (login, optional session extend, cloud inventory, alerts, compliance posture).

## Authentication setup

1. **Create an access key** in the Prisma Cloud administrative console (see Palo Alto’s documentation for *create access keys* for your product edition).
2. Determine your **API base URL** from the cluster that hosts your tenant. Console URL and API URL pairs are listed under **API URLs** on pan.dev (e.g. `https://app.prismacloud.io` → `https://api.prismacloud.io`; `https://app2.prismacloud.io` → `https://api2.prismacloud.io`; EU, Gov, and other regions have matching `api.*` hosts).
3. **POST /login** (on that API base URL) with JSON body:
   - `username`: Access Key ID  
   - `password`: Secret Key  
   Response includes a `token` (JWT). Official docs state this JWT is valid for **10 minutes**; the app stores the JWT and refreshes via **GET /auth_token/extend** when possible, falling back to **POST /login**.
4. All other requests require header **`x-redlock-auth: <JWT>`** (documented under **API Headers** on pan.dev).

### Application configuration (`tool_integrations.configuration_data`)

| Field | Description |
|--------|-------------|
| `provider_key` | Optional; use `prisma_cloud` for clarity. |
| `api_base_url` | HTTPS API base for your tenant (no trailing path), e.g. `https://api.prismacloud.io`. |
| `access_key_id` | Access Key ID (`username` in POST /login). |
| `secret_key` | Secret Key (`password` in POST /login). |

After a successful configure, the server may persist `prisma_jwt` and `prisma_jwt_obtained_at` (masked in status responses).

## Integrated endpoints (this repo)

HTTP routes:

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/integrations/cspm/prisma-cloud/configure` | Save credentials, validate via POST /login, optional background collect. |
| GET | `/api/v1/integrations/cspm/prisma-cloud/flow` | Readiness. |
| GET | `/api/v1/integrations/cspm/prisma-cloud/status` | Masked config. |
| POST | `/api/v1/evidence/prisma-cloud/collect` | Evidence collection. |
| POST | `/api/v1/integrations/sync` | Unified sync with `provider_key`: `prisma_cloud`. |

Prisma Cloud REST APIs used by the collector (see pan.dev for full contract):

| Endpoint | Method | Notes |
|----------|--------|--------|
| `/login` | POST | Credentials → JWT. |
| `/auth_token/extend` | GET | Refresh JWT when cached token is near expiry. |
| `/cloud` | GET | Cloud accounts onboarded. |
| `/v2/alert` | GET | Alerts list (documented **rate limits**: 2/sec sustained, 10/sec burst on the List Alerts V2 page). |
| `/v2/compliance/posture` | GET | Compliance statistics breakdown V2. |

## Evidence codes (seed)

Codes **EV-701**–**EV-704** are defined in `app/integrations/categories/cspm/prisma_cloud/evidence_map.py` with `source=prisma_cloud`. Run `seed_prisma_cloud_evidence_masters(session, tool_id)` (or insert equivalent rows) **before** collect so `evidence_masters` exist for the tool’s domain.

## Sample requests / responses

### Configure (this app)

```http
POST /api/v1/integrations/cspm/prisma-cloud/configure
Content-Type: application/json

{
  "org_id": "<uuid>",
  "user_id": "<uuid>",
  "tool_id": "<uuid>",
  "configuration_data": {
    "provider_key": "prisma_cloud",
    "api_base_url": "https://api.prismacloud.io",
    "access_key_id": "<access-key-id>",
    "secret_key": "<secret-key>"
  }
}
```

### Login (direct tenant API — from official getting-started example)

```http
POST https://api.prismacloud.io/login
Content-Type: application/json

{"username":"<access-key-id>","password":"<secret-key>"}
```

Example success shape (token abbreviated):

```json
{"token":"<jwt>","message":"login_successful"}
```

### Authenticated GET (direct tenant API)

```http
GET https://api.prismacloud.io/cloud
Content-Type: application/json
x-redlock-auth: <jwt from login>
```

Response body is tenant-specific JSON (account list / summary per Prisma Cloud API).

## Limitations and notes

- **Tenant URL**: You must use the API hostname that matches your Prisma Cloud cluster; wrong host will fail login.
- **Roles**: API access requires Cloud Security roles with sufficient permissions (see pan.dev *Cloud Security APIs require right privileges*).
- **JWT lifetime**: 10-minute validity is documented; plan for refresh or re-login.
- **Rate limits**: **GET /v2/alert** has documented limits (2/sec, burst 10/sec); heavy parallel jobs may receive HTTP 429 — retry with backoff per pan.dev error guidance.
- **Evidence scope**: This phase maps a small set of CSPM endpoints to EV-701–704; expanding coverage requires additional documented endpoints and seed rows.

## References (official)

- [Cloud Security API (CSPM)](https://pan.dev/prisma-cloud/api/cspm/)
- [Login](https://pan.dev/prisma-cloud/api/cspm/app-login/)
- [Refresh session](https://pan.dev/prisma-cloud/api/cspm/extend-session/)
- [API URLs](https://pan.dev/prisma-cloud/api/cspm/api-urls/)
- [API headers](https://pan.dev/prisma-cloud/api/cspm/api-headers/)
- [List Alerts V2](https://pan.dev/prisma-cloud/api/cspm/get-alerts-v-2/)
- [Get all Cloud Accounts](https://pan.dev/prisma-cloud/api/cspm/get-cloud-accounts/)
- [Compliance posture V2](https://pan.dev/prisma-cloud/api/cspm/get-compliance-posture-v-2/)
- [Get started (JWT + cURL)](https://pan.dev/prisma-cloud/docs/cspm/cspm-gs/)
