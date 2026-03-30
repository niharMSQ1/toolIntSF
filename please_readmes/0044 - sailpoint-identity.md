# SailPoint Identity Security Cloud — IdentityNow (IAM)

Code: [`app/integrations/categories/idp/sailpoint/`](../app/integrations/categories/idp/sailpoint/).

Uses **OAuth 2.0 client credentials** at `{base}/oauth/token` and the **IdentityNow V3 API** (default **`GET …/v3/public-identities`**) to list identities. See **[0001 - initialising.md](0001%20-%20initialising.md)** for G1–G5.

---

## Registry

| Item | Value |
|------|--------|
| `evidence_masters.source` | `iam` (shared catalog; legacy `sailpoint_identitynow` possible) |
| Unified sync `provider_key` | `sailpoint_identitynow` |
| Inference | `sailpoint_base_url` (or `identitynow_base_url`) in `configuration_data` |

---

## Configuration (`configuration_data`)

| Field | Description |
|-------|-------------|
| `sailpoint_base_url` | API base, e.g. `https://tenant.api.identitynow.com`. **Required.** |
| `client_id` / `client_secret` | OAuth client (aliases: `sailpoint_client_id`, `sailpoint_client_secret`). |
| `access_token` | Optional; use with `skip_token_exchange: true` if you manage tokens externally. |
| `sailpoint_identities_path` | Optional path override (default `/v3/public-identities`). |

---

## HTTP routes

| Method | Path |
|--------|------|
| POST | `/api/v1/integrations/sailpoint-identity/configure` |
| POST | `/idp/sailpoint-identity/integrations` |
| GET | `/api/v1/integrations/sailpoint-identity/flow` |
| GET | `/api/v1/integrations/sailpoint-identity/status` |
| GET | `/api/v1/integrations/sailpoint-identity/users` |
| POST | `/api/v1/evidence/sailpoint-identity/collect` |

---

## Evidence catalog

Shared IAM **`EV-*`** codes in [`iam_evidence_catalog.py`](../app/integrations/categories/idp/iam_evidence_catalog.py). Seed: [`seed_service.py`](../app/integrations/categories/idp/sailpoint/seed_service.py).

---

## Limitations

- **Public identities** endpoint only in the default path; private APIs or custom reports need collector extensions.
- OAuth client must be allowed to call the chosen identities API per SailPoint tenant policy.

---

## References

- [SailPoint Developer](https://developer.sailpoint.com/) (IdentityNow API and OAuth).
