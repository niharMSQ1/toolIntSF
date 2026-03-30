# Google Workspace / Cloud Identity — Directory API (IAM)

Code: [`app/integrations/categories/idp/google_workspace/`](../app/integrations/categories/idp/google_workspace/).

Uses **Google OAuth 2.0** (refresh token or optional static `access_token`) and the **Admin SDK Directory API** (`users.list`) for the primary domain. Admin consent and Directory API scopes are required in the Google Cloud OAuth client. See **[0001 - initialising.md](0001%20-%20initialising.md)** for G1–G5.

---

## Registry

| Item | Value |
|------|--------|
| `evidence_masters.source` | `iam` (shared catalog; legacy `google_workspace` possible) |
| Unified sync `provider_key` | `google_workspace` |
| Inference | `google_workspace_domain` or `primary_domain` in `configuration_data` |

---

## Configuration (`configuration_data`)

| Field | Description |
|-------|-------------|
| `google_workspace_domain` | Primary Workspace domain (alias: `primary_domain`). **Required** for Directory calls. |
| `client_id` / `client_secret` | Google OAuth client (aliases: `google_client_id`, `google_client_secret`). |
| `refresh_token` | Offline refresh token (preferred for long-lived access). |
| `access_token` | Optional; if set with `skip_token_exchange: true`, refresh may be skipped. |
| `skip_token_exchange` | When true, use stored `access_token` without calling Google token endpoint. |

---

## HTTP routes

| Method | Path |
|--------|------|
| POST | `/api/v1/integrations/google-workspace/configure` |
| POST | `/idp/google-workspace/integrations` |
| GET | `/api/v1/integrations/google-workspace/flow` |
| GET | `/api/v1/integrations/google-workspace/status` |
| GET | `/api/v1/integrations/google-workspace/users` |
| POST | `/api/v1/evidence/google-workspace/collect` |

---

## Evidence catalog

Shared IAM **`EV-*`** codes in [`iam_evidence_catalog.py`](../app/integrations/categories/idp/iam_evidence_catalog.py). Seed: [`seed_service.py`](../app/integrations/categories/idp/google_workspace/seed_service.py).

---

## Limitations

- Requires a **Google Admin** with Directory API access and a correctly scoped OAuth client.
- Pagination and large directories: collector uses Directory API paging as implemented in [`api_client.py`](../app/integrations/categories/idp/google_workspace/api_client.py).

---

## References

- [Google Workspace Admin SDK — Directory API](https://developers.google.com/admin-sdk/directory)
- [OAuth 2.0 for Web Server Applications](https://developers.google.com/identity/protocols/oauth2/web-server)
