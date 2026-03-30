# ClickUp — integration

Code: [`app/integrations/categories/project_management/clickup/`](../app/integrations/categories/project_management/clickup/).

---

## API findings (official)

| Topic | Documented |
|-------|------------|
| **Base** | `https://api.clickup.com/api/v2/` ([ClickUp API](https://clickup.com/api)) |
| **Auth** | Personal token in **`Authorization`** header (token value; not always prefixed with `Bearer` in examples) |

---

## Authentication setup

Create a **personal API token** in ClickUp workspace settings. Configure:

```json
"configuration_data": { "api_token": "<token>" }
```

Aliases: `clickup_token`, `personal_token`.

---

## Routes

| Path | Purpose |
|------|---------|
| GET | `.../me` |
| GET | `.../teams` |
| GET | `.../lists/{list_id}/tasks` |

---

## Unified mapping

- **UnifiedUser** ← `/user` response `user` object
- **UnifiedTask** ← task (`name`, `status`, `due_date`, `assignees`, `url`)

---

## Limitations

- Listing tasks requires a **list_id** (from UI or other API calls such as spaces/folders).
