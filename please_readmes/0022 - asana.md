# Asana — project management integration

This document describes the **Asana** integration under [`app/integrations/categories/project_management/asana/`](../app/integrations/categories/project_management/asana/). Generic persistence (G1–G2) is in **[0001 - initialising.md](0001%20-%20initialising.md)**. This provider focuses on **REST data + webhooks**, not GRC **`evidence_masters`** / unified sync.

---

## Tool overview

[Asana](https://asana.com/) is a work management platform. The official developer documentation is at [developers.asana.com](https://developers.asana.com/docs). The REST API is versioned under **`/api/1.0/`** on host **`app.asana.com`**.

---

## API findings (official documentation)

| Topic | Documented fact |
|--------|-----------------|
| **Authentication** | **Personal Access Token (PAT)** or **OAuth 2.0** bearer tokens; requests use `Authorization: Bearer <token>`. Service Accounts exist for Enterprise (separate product surface). |
| **OAuth authorize** | `GET https://app.asana.com/-/oauth_authorize` |
| **OAuth token** | `POST https://app.asana.com/-/oauth_token` (form-encoded body; `grant_type` `authorization_code` or `refresh_token`) |
| **OAuth revoke** | `POST https://app.asana.com/-/oauth_revoke` |
| **Base URL** | `https://app.asana.com/api/1.0` |
| **Core resources** | Workspaces, teams, projects, tasks, stories (incl. comments), users, tags, sections, webhooks, events |
| **Webhooks** | Create via API; **handshake** uses `X-Hook-Secret` echo; events use **`X-Hook-Signature`** = HMAC-SHA256 over raw body with the shared secret |
| **JSON shape** | Typical envelope `{"data": ...}` with `next_page` for collections |
| **Rate limits** | Documented per-token limits (e.g. free vs paid requests/minute), **429** with **`Retry-After`**; separate limits for search and concurrent requests — see [Rate limits](https://developers.asana.com/docs/rate-limits) |

---

## Authentication setup

### Personal Access Token (PAT)

1. Open [Developer Console](https://app.asana.com/0/my-apps) → create or select an app → generate a **personal access token** (documented in [Personal access token](https://developers.asana.com/docs/personal-access-token)).
2. **POST** `/api/v1/integrations/project-management/asana/configure` with:

```json
{
  "org_id": "<uuid>",
  "user_id": "<uuid>",
  "tool_id": "<uuid>",
  "configuration_data": {
    "personal_access_token": "<pat>"
  }
}
```

### OAuth 2.0 (authorization code)

1. Register an app in the Developer Console; set **redirect URL** (must be **https** for non-native apps per Asana OAuth docs, except the documented native `urn:ietf:wg:oauth:2.0:oob` case).
2. Pre-register **OAuth scopes** for the app; request scopes on authorize (this codebase defaults to read scopes — see `DEFAULT_ASANA_SCOPES` in [`constants.py`](../app/integrations/categories/project_management/asana/constants.py)).
3. **POST** `/configure` with `client_id`, `client_secret`, `redirect_uri`.
4. **GET** `/api/v1/oauth/asana/authorize?org_id=&tool_id=` → open `authorization_url`.
5. User is redirected to **`GET /project-management/asana/callback?code=&state=`** on this API host; tokens are stored in **`configuration_data`** (`access_token`, `refresh_token`, `access_token_expires_at`).

**Refresh:** **POST** `/api/v1/integrations/project-management/asana/refresh-tokens` with `{ "org_id", "tool_id", "force": false }`.

---

## Supported HTTP API (this repo)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/integrations/project-management/asana/configure` | Upsert integration (PAT or OAuth client settings). |
| POST | `/project-management/asana/integrations` | Alias of configure. |
| GET | `/api/v1/integrations/project-management/asana/flow` | Flow / auth URL when needed. |
| GET | `/api/v1/integrations/project-management/asana/status` | Masked `configuration_data`. |
| POST | `/api/v1/integrations/project-management/asana/refresh-tokens` | OAuth refresh. |
| GET | `/api/v1/oauth/asana/authorize` | JSON with `authorization_url` + `state`. |
| GET | `/project-management/asana/callback` | OAuth callback. |
| GET | `/api/v1/integrations/project-management/asana/me` | Current user (`/users/me`) + **UnifiedUser**. |
| GET | `/api/v1/integrations/project-management/asana/workspaces` | Raw workspace list. |
| GET | `/api/v1/integrations/project-management/asana/projects` | Query `workspace_gid` — **UnifiedProject** list. |
| GET | `/api/v1/integrations/project-management/asana/projects/{project_gid}` | Project detail. |
| GET | `/api/v1/integrations/project-management/asana/tasks` | Query `project_gid` — **UnifiedTask** list. |
| GET | `/api/v1/integrations/project-management/asana/tasks/{task_gid}` | Task detail. |
| GET | `/api/v1/integrations/project-management/asana/tasks/{task_gid}/stories` | Stories / activity → **UnifiedActivity**. |
| GET | `/api/v1/integrations/project-management/asana/users/{user_gid}` | User profile. |
| POST | `/api/v1/integrations/project-management/asana/webhooks/register` | Calls Asana `POST /webhooks` (query `org_id`, `tool_id`). |
| POST | `/api/v1/webhooks/asana/{org_id}/{tool_id}` | Webhook receiver (handshake + signed events). |

---

## Data mapping (Asana → internal schema)

Defined in [`common_schema.py`](../app/integrations/categories/project_management/common_schema.py) and [`normalize.py`](../app/integrations/categories/project_management/asana/normalize.py).

| Internal | Asana source |
|----------|----------------|
| **UnifiedProject** | Project `gid`, `name`, `archived`, `permalink_url` |
| **UnifiedTask** | Task `gid`, `name`, `completed`, `due_on` / `due_at`, `assignee.gid`, `memberships[].project.gid`, section name → **UnifiedStatus** |
| **UnifiedUser** | User `gid`, `name`, `email` |
| **UnifiedStatus** | First task **membership** section `name` when present |
| **UnifiedActivity** | Story `gid`, `type`, `text`, `created_at`, `created_by.gid` |

Other PM tools should extend the same **`Unified*`** models for consistency.

---

## Webhook setup

1. Expose **`POST /api/v1/webhooks/asana/{org_id}/{tool_id}`** on the public internet (e.g. reverse proxy + HTTPS).
2. Register the webhook with Asana (**POST** `/webhooks` via **`POST .../webhooks/register`** in this API, or in Asana), using that URL as **`target`**.
3. **Handshake:** Asana sends **`X-Hook-Secret`** without **`X-Hook-Signature`**; this service echoes the header and stores **`webhook_secret`** on the integration row.
4. **Events:** Verify **`X-Hook-Signature`** against the raw body using the stored secret ([Security](https://developers.asana.com/docs/webhooks-guide#security)).
5. Respond with **200** or **204** within **10 seconds** (documented delivery window).

---

## Sample requests / responses

**Configure (PAT)** — request body:

```json
{
  "org_id": "…",
  "user_id": "…",
  "tool_id": "…",
  "configuration_data": { "personal_access_token": "…" }
}
```

**GET …/me** — response shape:

```json
{
  "unified": {
    "id": "…",
    "name": "…",
    "email": "…",
    "provider": "asana",
    "raw": { }
  },
  "raw": { "data": { … } }
}
```

**Webhook event** (illustrative; compact event objects per [events](https://developers.asana.com/reference/events)):

```json
{
  "events": [
    {
      "user": { "gid": "…", "resource_type": "user" },
      "action": "changed",
      "resource": { "gid": "…", "resource_type": "task" },
      "parent": null,
      "created_at": "…"
    }
  ]
}
```

---

## Limitations / edge cases

- **Not** wired into **`POST /api/v1/integrations/sync`** or **`evidence_masters`** — use REST routes above for PM data.
- **Rate limits** and **cost-based limits** apply; client retries **429** using **`Retry-After`** (see [`api_client.py`](../app/integrations/categories/project_management/asana/api_client.py)).
- **Webhooks** are **at-most-once**; use polling or `/events` as a fallback if you need stronger guarantees (per Asana docs).
- **OAuth scopes** must match what is enabled on the app in the Developer Console.
- **Task “status”** in the unified model is mapped from the **section name** of the first membership when present; custom rules may differ from Asana UI columns.

---

## Postman

Collection: [`postman/ToolIntegrations.postman_collection.json`](../postman/ToolIntegrations.postman_collection.json) — folder **Asana**. Variables: `asana_pat`, `asana_workspace_gid`, `asana_project_gid`, `asana_task_gid`, `asana_webhook_target_url`.
