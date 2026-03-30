# Microsoft Planner (Microsoft Graph) — integration

Code: [`app/integrations/categories/project_management/microsoft_planner/`](../app/integrations/categories/project_management/microsoft_planner/).

**Microsoft Project (desktop/Project Online)** uses different APIs than **Planner**; this module implements **Planner** via [Microsoft Graph Planner](https://learn.microsoft.com/en-us/graph/api/resources/planner-overview).

---

## API findings (official)

| Topic | Documented |
|-------|------------|
| **Base URL** | `https://graph.microsoft.com/v1.0` |
| **Auth** | Microsoft Entra **OAuth 2.0** — client credentials (`/.default`) or refresh token flow ([Get access](https://learn.microsoft.com/en-us/graph/auth/auth-concepts)). |
| **Planner** | Plans: `/groups/{id}/planner/plans`, tasks: `/planner/plans/{plan-id}/tasks` ([plannerPlan](https://learn.microsoft.com/en-us/graph/api/resources/plannerplan), [plannerTask](https://learn.microsoft.com/en-us/graph/api/resources/plannertask)). |
| **Permissions** | e.g. `Group.Read.All`, `Tasks.Read.All`, `Planner.Read.All` — see Graph documentation for your tenant/app registration. |

---

## Authentication setup

`configuration_data` supports either:

1. **Client credentials** (recommended for unattended): `tenant_id`, `client_id`, `client_secret` — token acquired for `https://graph.microsoft.com/.default`.
2. **Static access token** (testing): `access_token` (+ optional `access_token_expires_at`, `refresh_token`).

**POST** `/api/v1/integrations/project-management/microsoft-planner/configure` with the above fields.

**POST** `/api/v1/integrations/project-management/microsoft-planner/refresh-tokens` refreshes or obtains tokens when using client credentials / refresh.

---

## Routes

| Method | Path |
|--------|------|
| POST | `.../configure`, `.../integrations` |
| GET | `.../flow`, `.../status` |
| POST | `.../refresh-tokens` |
| GET | `.../me` |
| GET | `.../groups/{group_id}/plans` |
| GET | `.../plans/{plan_id}` |
| GET | `.../plans/{plan_id}/tasks` |

`group_id` is an Entra **group** id that owns Planner plans.

---

## Unified mapping

| Unified | Graph |
|---------|--------|
| **UnifiedUser** | `/me` |
| **UnifiedProject** | `plannerPlan` (`id`, `title`) |
| **UnifiedTask** | `plannerTask` (`id`, `title`, `planId`, `percentComplete`, `assignments`, `bucketId`, `dueDateTime`) |

---

## Limitations

- **Project for the web / Project Online** REST surfaces differ; use Graph **Planner** / **roster** docs for your scenario.
- Required **permissions** must be granted on the Entra app registration.
