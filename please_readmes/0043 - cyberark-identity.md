# CyberArk Identity (IAM)

Code: [`app/integrations/categories/idp/cyberark/`](../app/integrations/categories/idp/cyberark/).

Uses **OAuth 2.0 client credentials** against the CyberArk Identity tenant and **SCIM 2.0** (`GET …/scim/Users`) to list users for IAM evidence. Generic G1–G5 flow is in **[0001 - initialising.md](0001%20-%20initialising.md)**.

---

## Registry

| Item | Value |
|------|--------|
| `evidence_masters.source` | `iam` (shared catalog; legacy `cyberark_identity` possible) |
| Unified sync `provider_key` | `cyberark_identity` |
| Inference from `configuration_data` | `cyberark_identity_base_url` present (see `sync_dispatch.py`) |

---

## Configuration (`configuration_data`)

| Field | Description |
|-------|-------------|
| `cyberark_identity_base_url` | Tenant origin (no trailing path), e.g. `https://your-tenant.identity.cyberark.cloud`. **Required.** |
| `client_id` / `client_secret` | OAuth confidential client (aliases: `cyberark_client_id`, `cyberark_client_secret`). |
| `access_token` | Optional; use with `skip_token_exchange: true` to skip token POST. |
| `cyberark_scim_users_path` | Optional SCIM path override (default `/scim/Users`). |
| `oauth_scope` | Optional scope for token request. |

Secrets are masked in configure responses (`access_token`, `client_secret`, etc.).

---

## HTTP routes

| Method | Path |
|--------|------|
| POST | `/api/v1/integrations/cyberark-identity/configure` |
| POST | `/idp/cyberark-identity/integrations` |
| GET | `/api/v1/integrations/cyberark-identity/flow` |
| GET | `/api/v1/integrations/cyberark-identity/status` |
| GET | `/api/v1/integrations/cyberark-identity/users` |
| POST | `/api/v1/evidence/cyberark-identity/collect` |

---

## Evidence catalog

Same **`EV-*`** IAM codes as **[`iam_evidence_catalog.py`](../app/integrations/categories/idp/iam_evidence_catalog.py)**. Seed helpers: [`seed_service.py`](../app/integrations/categories/idp/cyberark/seed_service.py).

---

## Limitations

- **CyberArk Identity** tenant URL and SCIM availability; OAuth scopes must allow SCIM read.
- Deployment-specific SCIM paths may require `cyberark_scim_users_path`.

---

## References

- [CyberArk Identity / SCIM developer documentation](https://docs.cyberark.com/) (verify current token and SCIM URLs for your tenant).
