# Linear — integration

Code: [`app/integrations/categories/project_management/linear/`](../app/integrations/categories/project_management/linear/).

---

## API findings (official)

| Topic | Documented |
|-------|------------|
| **Endpoint** | `POST https://api.linear.app/graphql` ([GraphQL API](https://developers.linear.app/docs/graphql/working-with-the-graphql-api)) |
| **Auth** | **Personal API key** in `Authorization` header (raw key, not `Bearer`) |

---

## Authentication setup

Settings → API → **Personal API keys**. Configure:

```json
"configuration_data": { "api_key": "<key>" }
```

Aliases: `linear_api_key`, `access_token`.

---

## Routes

`.../configure`, `.../flow`, `.../status`, `GET .../me`, `GET .../issues`, `GET .../projects`

---

## Unified mapping

- **UnifiedUser** ← `viewer { id name email }`
- **UnifiedProject** ← `projects { nodes { id name url } }`
- **UnifiedTask** ← `issues { nodes { id title url state { name } } }`

---

## Limitations

- GraphQL schema evolves; adjust queries if Linear deprecates fields.
