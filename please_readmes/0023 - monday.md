# Monday.com — integration

Code: [`app/integrations/categories/project_management/monday/`](../app/integrations/categories/project_management/monday/).

---

## API findings (official)

| Topic | Documented |
|-------|------------|
| **Auth** | Personal **V2 API token** in `Authorization` header (same value as token string; not always `Bearer`). |
| **Endpoint** | Single GraphQL endpoint **`POST https://api.monday.com/v2`** |
| **Headers** | `Content-Type: application/json`, optional **`API-Version`** (see [API versioning](https://developer.monday.com/api-reference/docs/api-versioning)). |
| **Body** | JSON `{"query": "...", "variables": {...}}` |
| **Webhooks** | URL verification: echo JSON `{"challenge": "<token>"}`; events per [Webhooks](https://developer.monday.com/api-reference/docs/webhooks). |

---

## Authentication setup

1. Developer Center → **API token** → copy ([Authentication](https://developer.monday.com/api-reference/docs/authentication)).
2. **POST** `/api/v1/integrations/project-management/monday/configure` with:

```json
{
  "org_id": "...",
  "user_id": "...",
  "tool_id": "...",
  "configuration_data": { "api_token": "<token>" }
}
```

Aliases: `monday_api_token`, `personal_api_token`.

---

## Routes (this repo)

| Method | Path |
|--------|------|
| POST | `/api/v1/integrations/project-management/monday/configure` |
| POST | `/project-management/monday/integrations` |
| GET | `/api/v1/integrations/project-management/monday/flow` |
| GET | `/api/v1/integrations/project-management/monday/status` |
| GET | `/api/v1/integrations/project-management/monday/me` |
| GET | `/api/v1/integrations/project-management/monday/boards` |
| GET | `/api/v1/integrations/project-management/monday/boards/{board_id}/items` |
| POST | `/api/v1/webhooks/monday/{org_id}/{tool_id}` |

---

## Unified schema mapping

| Unified | Monday |
|---------|--------|
| **UnifiedUser** | `me { id name email }` |
| **UnifiedProject** | Board `id`, `name`, `state` |
| **UnifiedTask** | Item `id`, `name`, `state`; status column preferred when `type == status` |

---

## Limitations

- **OAuth for marketplace apps** uses monday Apps OAuth ([Apps docs](https://developer.monday.com/apps/docs/oauth)); this integration uses **personal token** by default.
- GraphQL field availability depends on **`API-Version`** (`constants.MONDAY_API_VERSION`).
