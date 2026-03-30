# OneLogin — OAuth 2.0 + Users API (IAM)

Code: [`app/integrations/categories/idp/onelogin/`](../app/integrations/categories/idp/onelogin/).

Uses **OAuth 2.0 client credentials** at `https://api.{region}.onelogin.com/auth/oauth2/v2/token` and the **Users** API (default **`GET …/api/1/users`**). Region selects the API host (`us`, `eu`, etc.). See **[0001 - initialising.md](0001%20-%20initialising.md)** for G1–G5.

---

## Registry

| Item | Value |
|------|--------|
| `evidence_masters.source` | `iam` (shared catalog; legacy `onelogin` possible) |
| Unified sync `provider_key` | `onelogin` |
| Inference | `onelogin_client_id` **or** a non-empty `onelogin_region` key in `configuration_data` (see `sync_dispatch.py`) |

If you only use generic `client_id` without those fields, **pass `provider_key` explicitly** on unified sync.

---

## Configuration (`configuration_data`)

| Field | Description |
|-------|-------------|
| `onelogin_region` | API region (default `us` when resolving host). Set explicitly for inference. |
| `client_id` / `client_secret` | OAuth client (aliases: `onelogin_client_id`, `onelogin_client_secret`). |
| `access_token` | Optional; use with `skip_token_exchange: true`. |
| `onelogin_users_path` | Optional path override (default `/api/1/users`). |

---

## HTTP routes

| Method | Path |
|--------|------|
| POST | `/api/v1/integrations/onelogin/configure` |
| POST | `/idp/onelogin/integrations` |
| GET | `/api/v1/integrations/onelogin/flow` |
| GET | `/api/v1/integrations/onelogin/status` |
| GET | `/api/v1/integrations/onelogin/users` |
| POST | `/api/v1/evidence/onelogin/collect` |

---

## Evidence catalog

Shared IAM **`EV-*`** codes in [`iam_evidence_catalog.py`](../app/integrations/categories/idp/iam_evidence_catalog.py). Seed: [`seed_service.py`](../app/integrations/categories/idp/onelogin/seed_service.py).

---

## Limitations

- OneLogin **API credentials** and OAuth client must be allowed to read users.
- Token and user response shapes follow OneLogin API versioning; extend [`normalize.py`](../app/integrations/categories/idp/onelogin/normalize.py) if your tenant returns variants.

---

## References

- [OneLogin Developers](https://developers.onelogin.com/) (API authentication and Users).
