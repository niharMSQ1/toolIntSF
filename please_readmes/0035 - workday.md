# Workday integration (HR)

## Overview

This integration uses the **Workday REST API** with **OAuth 2.0** access tokens and maps responses into **`app/integrations/categories/hrms/common_schema.py`** (employees, departments, events).

**Official documentation (must follow for your tenant):**

- REST API: [Workday Developers — REST API](https://developer.workday.com/en-us/docs/rest-api)
- OAuth 2.0 token endpoint pattern: `POST https://{hostname}/ccx/oauth2/{tenant}/token` (client credentials and refresh flows are documented for API clients for integrations).
- REST resource URL pattern: `https://{hostname}/api/{version}/{tenant}/...` (resource paths and query parameters are defined in Workday’s REST API reference for your tenant).

---

## Step 1 — API findings summary (documented)

| Topic | Documented behavior |
|--------|---------------------|
| **Authentication** | OAuth 2.0: `client_credentials` and `refresh_token` grants against `/ccx/oauth2/{tenant}/token`; REST calls use `Authorization: Bearer {access_token}`. |
| **Base URL** | Tenant-specific hostname (e.g. implementation services host); **no single global URL** — use the hostname Workday provides for your tenant. |
| **API version** | REST path segment `api/{version}` (e.g. `v1`); pin `api_version` in configuration. |
| **Workers** | Workers resource is a common REST entry point for worker data; exact fields and query parameters depend on the REST API reference and your security domains. |
| **Organizations** | Organizations REST resource may be available depending on tenant subscription; **not** guaranteed to return 200 for all tenants. |
| **Pagination / limits** | `limit` / `offset` query parameters are passed through when supported by the resource; see Workday REST reference for limits and supported parameters. |
| **Webhooks** | Native Workday **outbound** integrations use Workday’s integration framework, not a generic public HTTPS webhook format. This app exposes a **custom** receiver for payloads forwarded by your integration layer (optional `Authorization: Bearer` matching `webhook_secret`). |

---

## Step 2 — Implementation (this codebase)

| Module | Purpose |
|--------|---------|
| `hrms/common_schema.py` | `HREmployee`, `HRDepartment`, `HRRole`, `HRManagerRelationship`, `HREmploymentStatus`, `HRCompensation`, `HRTimeOffBalance`, `HREvent` |
| `hrms/workday/constants.py` | Default API version |
| `hrms/workday/credentials.py` | Hostname, tenant, OAuth client, tokens |
| `hrms/workday/oauth.py` | Client credentials + refresh token exchange |
| `hrms/workday/api_client.py` | Bearer GET, `GET /workers`, `GET /workers/{id}`, `GET /organizations`, 429 retry |
| `hrms/workday/normalize.py` | Map Workday JSON → unified schema (best-effort; WIDs vary) |
| `hrms/workday/session.py` | Load `access_token` |
| `hrms/workday/routers/configure.py` | Configure, flow, status |
| `hrms/workday/routers/data.py` | Employees + organizations |
| `hrms/workday/routers/refresh.py` | Refresh OAuth refresh token |
| `hrms/workday/routers/webhook.py` | Custom inbound webhook |

**Logging:** `logging.getLogger("app.integrations.workday")` for API debug (no PII in logs by default).

**PII:** Responses may contain employee PII; **mask secrets** in configure responses; **do not log** full bodies unless `WORKDAY_DEBUG_HTTP` is set for troubleshooting.

---

## Configuration (`configuration_data`)

| Field | Description |
|-------|-------------|
| `workday_hostname` | HTTPS origin (e.g. `https://impl-services1.workday.com`) |
| `workday_tenant` | Tenant name used in OAuth and REST paths |
| `client_id` / `client_secret` | OAuth API client for integrations (optional if `access_token` supplied manually) |
| `access_token` (optional) | Pre-issued bearer token; use with `skip_token_exchange: true` to avoid re-exchange |
| `skip_token_exchange` | If `true`, skips OAuth exchange on configure (use only when `access_token` is already set) |
| `oauth_scope` / `scope` | Optional OAuth scope string |
| `api_version` | REST segment (default `v1`) |
| `webhook_secret` | Optional secret for custom webhook `Authorization: Bearer` |

---

## Routes

| Method | Path |
|--------|------|
| POST | `/api/v1/integrations/hrms/workday/configure` |
| GET | `/api/v1/integrations/hrms/workday/flow` |
| GET | `/api/v1/integrations/hrms/workday/status` |
| GET | `/api/v1/integrations/hrms/workday/employees` |
| GET | `/api/v1/integrations/hrms/workday/employees/{worker_id}` |
| GET | `/api/v1/integrations/hrms/workday/organizations` |
| POST | `/api/v1/integrations/hrms/workday/refresh-tokens` |
| POST | `/api/v1/webhooks/workday/{org_id}/{tool_id}` |

---

## Unified schema mapping

- **HREmployee** — Worker fields (`personInformation`, `employmentInformation`, etc.) when present.
- **HRDepartment** — Organization resource when `GET /organizations` succeeds.
- **HREvent** — Custom webhook payload subset.

**Compensation / payroll / time-off** — Not hard-coded in this pass; extend `normalize.py` when your tenant exposes specific REST resources permitted by policy.

---

## Sample configure (OAuth client credentials)

```json
{
  "org_id": "<org-uuid>",
  "user_id": "<user-uuid>",
  "tool_id": "<tool-uuid>",
  "configuration_data": {
    "workday_hostname": "https://<your-hostname>.workday.com",
    "workday_tenant": "<tenant>",
    "client_id": "<api-client-id>",
    "client_secret": "<api-client-secret>",
    "api_version": "v1"
  }
}
```

---

## Compliance / security notes

- Store **least privilege** Integration System User and API client scopes per Workday security best practices.
- **Rotate** client secrets and tokens per organizational policy.
- **Encrypt** data at rest in your database; restrict access to `tool_integrations.configuration_data`.
- This integration **does not** implement Workday-specific outbound signing; use Workday’s documented integration patterns for production event delivery.

---

## Limitations

- Field normalization is **best-effort**; tenant-specific JSON shapes may require mapping adjustments.
- `GET /organizations` may **404** if not enabled for your tenant.
- Query parameters (`limit`/`offset`) must match **your** resource’s documented contract.

---

## Postman

See folder **Workday (HRMS)** in `postman/ToolIntegrations.postman_collection.json` and variables `workday_hostname`, `workday_tenant`, `workday_client_id`, `workday_client_secret`, `workday_worker_id`.
