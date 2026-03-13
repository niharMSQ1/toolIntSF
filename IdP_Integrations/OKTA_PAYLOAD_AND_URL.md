# Okta integration – payload and URL

## Base URL (Okta Admin API)

- **Base URL:** `https://{org_domain}/api/v1`
- **Example:** `https://dev-12345.okta.com/api/v1` or `https://company.okta.com/api/v1`
- **Auth:** API token in header: `Authorization: SSWS {api_token}`

`org_domain` is your Okta org domain **without** `https://` (e.g. `dev-12345.okta.com`).

---

## Backend routes (this app)

| Method | URL (relative to app base) | Description |
|--------|---------------------------|-------------|
| POST   | `/idp/okta/integrations`   | Create/update Okta integration (body below) |
| POST   | `/idp/okta/integrations/{integration_id}/collect` | Run evidence collection for that integration |
| POST   | `/integrations/{integration_id}/refresh-and-collect` | Refresh (N/A for Okta) + collect; works for Okta using stored API token |

**App base URL** is whatever you run (e.g. `http://localhost:8005`). So full URL for creating integration:  
`POST http://localhost:8005/idp/okta/integrations`

---

## Payload: create/update Okta integration

**POST** `/idp/okta/integrations`

**Request body (JSON):**

```json
{
  "org_id": "YOUR_ORGANIZATION_UUID",
  "user_id": "YOUR_USER_UUID",
  "tool_id": "OKTA_TOOL_UUID",
  "configuration_data": {
    "org_domain": "dev-12345.okta.com",
    "api_token": "YOUR_OKTA_ADMIN_API_TOKEN"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | UUID | Yes | Your organization id (from `organizations` table). |
| `user_id` | UUID | Yes | User performing the integration (from `users` table). |
| `tool_id` | UUID | Yes | Okta tool id (from `tools` table). After running `migrations/003_seed_okta_tool_and_control_scenarios.sql`, get it with `SELECT id FROM tools WHERE name = 'Okta';` (or use the seeded id `019cd289-2611-7398-a647-0ed60bd3742e` if the migration inserted that row). |
| `configuration_data.org_domain` | string | Yes | Okta org domain, e.g. `dev-12345.okta.com` or `company.okta.com` (no `https://`). |
| `configuration_data.api_token` | string | Yes | Okta Admin API token (created in Okta Admin → Security → API → Tokens). |

**Example (replace UUIDs and token):**

```json
{
  "org_id": "019cd289-0000-7000-8000-000000000001",
  "user_id": "019cd289-0000-7000-8000-000000000002",
  "tool_id": "019cd289-2611-7398-a647-0ed60bd3742e",
  "configuration_data": {
    "org_domain": "dev-12345.okta.com",
    "api_token": "00abc..."
  }
}
```

**Response (201 / 200):**

```json
{
  "status": "ok",
  "integration_id": "uuid-of-tool-integration",
  "message": "Okta integration saved. Call POST /integrations/{integration_id}/refresh-and-collect to collect evidence."
}
```

---

## Payload: trigger evidence collection

**POST** `/integrations/{integration_id}/refresh-and-collect`

- **URL:** e.g. `POST http://localhost:8005/integrations/019cd289-xxxx-xxxx-xxxx-xxxxxxxxxxxx/refresh-and-collect`
- **Body:** none
- **Response:** `{ "status": "ok", "integration_id": "...", "evidence_collected": true }`

Or use the Okta-specific collect endpoint:

**POST** `/idp/okta/integrations/{integration_id}/collect`

- **Body:** none
- **Response:** same as above.

---

## Okta API endpoints used (MVP)

| # | Evidence name        | Okta API path | Method |
|---|----------------------|---------------|--------|
| 1 | Users                | `/api/v1/users` | GET |
| 2 | User Factors (MFA)   | `/api/v1/users/{userId}/factors` | GET |
| 3 | Groups               | `/api/v1/groups` | GET |
| 4 | Group Members        | `/api/v1/groups/{groupId}/users` | GET |
| 5 | Applications         | `/api/v1/apps` | GET |
| 6 | App Users            | `/api/v1/apps/{appId}/users` | GET |
| 7 | App Groups           | `/api/v1/apps/{appId}/groups` | GET |
| 8 | System Logs         | `/api/v1/logs` | GET |
| 9 | Policies             | `/api/v1/policies` | GET |
|10 | User Admin Roles     | `/api/v1/users/{userId}/roles` | GET |

Full URL for each is: `https://{org_domain}{path}` (e.g. `https://dev-12345.okta.com/api/v1/users`).

---

## Optional config: incremental logs

You can store a `since` timestamp for logs in integration config (e.g. after first run, set `logs_since` to the last event timestamp). The service reads `configuration_data.logs_since` and passes it as `since` to `GET /api/v1/logs?since=...` for incremental log collection.
