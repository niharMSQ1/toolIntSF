# Tanium — integration

## 1. API documentation review

Tanium’s REST API is hosted under **`/api/v2`** on the Tanium Console host. Official reference documentation may require a Tanium developer login; integrator-facing summaries agree on:

- **Authentication:** API token in the HTTP header **`session`** (not `Authorization: Bearer` — that pattern returns 401 in common setups).
- **Token creation:** Tanium Console → Administration → Permissions → API Tokens.

Example patterns (community / integrator docs):

| Endpoint | Use in this repo |
|----------|------------------|
| `GET /api/v2/session/info` | Validate token / current principal (EV-821) |
| `GET /api/v2/users` | User list with `limit` / `offset` (EV-822) |
| `GET /api/v2/roles` | Role list (EV-823) |

Responses commonly wrap payloads in a **`data`** field (object or array).

---

## 2. Implementation (this codebase)

Package: `app/integrations/categories/vulnerability_management/tanium/` (HTTP routes under `/integrations/endpoint/tanium` alongside other endpoint tools).

Routes:

- `POST /api/v1/integrations/endpoint/tanium/configure`
- `GET .../flow`, `GET .../status`
- `POST /api/v1/evidence/tanium/collect`
- `POST /api/v1/integrations/sync` — `provider_key`: `tanium`

`configuration_data`: `api_token`, `api_base_url` (console origin; `/api/v2` is appended if not present).

Seed: `seed_tanium_evidence_masters(session, tool_id)` — **`source`** = **`tanium`**.

---

## 3. Postman

Folder **Tanium** — `tan_api_base_url`, `tan_api_token`.
