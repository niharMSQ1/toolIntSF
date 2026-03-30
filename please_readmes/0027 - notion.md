# Notion — integration

Code: [`app/integrations/categories/project_management/notion/`](../app/integrations/categories/project_management/notion/).

---

## API findings (official)

| Topic | Documented |
|-------|------------|
| **Base** | `https://api.notion.com/v1` ([Notion API](https://developers.notion.com/reference)) |
| **Auth** | `Authorization: Bearer <internal_integration_secret>` |
| **Versioning** | Required header **`Notion-Version`** ([Versioning](https://developers.notion.com/reference/versioning)) — see `notion/constants.py`. |
| **Search** | `POST /v1/search` |

---

## Authentication setup

Create an **internal integration** in Notion, copy the secret, share pages/databases with the integration. Configure:

```json
"configuration_data": { "integration_secret": "<secret>" }
```

Aliases: `notion_token`, `api_token`, `access_token`.

---

## Routes

`.../configure`, `.../flow`, `.../status`, `GET .../me`, `GET .../search`, `GET .../pages/{page_id}`

---

## Unified mapping

- **UnifiedUser** ← `/users/me` (bot user for integrations)
- **UnifiedTask** ← page object (title from `properties` title field when present)

---

## Limitations

- Notion’s model (pages, databases, blocks) does not map 1:1 to “tasks”; normalization is **best-effort** for search/page results.
