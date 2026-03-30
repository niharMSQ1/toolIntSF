# ForgeRock — OpenIDM / AM REST (IAM)

Code: [`app/integrations/categories/idp/forgerock/`](../app/integrations/categories/idp/forgerock/).

This integration is **deployment-flexible**: you supply the full **OAuth 2.0 token URL** and **REST API base** for your ForgeRock stack (e.g. **OpenIDM** managed users query, or AM endpoints your deployment exposes). Default user path is OpenIDM-style **`/openidm/managed/user?_queryFilter=true`**. See **[0001 - initialising.md](0001%20-%20initialising.md)** for G1–G5.

---

## Registry

| Item | Value |
|------|--------|
| `evidence_masters.source` | `iam` (shared catalog; legacy `forgerock` possible) |
| Unified sync `provider_key` | `forgerock` |
| Inference | `forgerock_token_url` **and** `forgerock_api_base` in `configuration_data` |

---

## Configuration (`configuration_data`)

| Field | Description |
|-------|-------------|
| `forgerock_token_url` | Full URL for `POST` OAuth token (client credentials). **Required.** |
| `forgerock_api_base` | Origin for REST user reads (alias: `api_base_url`). **Required.** |
| `client_id` / `client_secret` | OAuth client (aliases: `forgerock_client_id`, `forgerock_client_secret`). |
| `access_token` | Optional; use with `skip_token_exchange: true`. |
| `forgerock_users_path` | Optional path override (default `/openidm/managed/user?_queryFilter=true`). |
| `forgerock_oauth_scope` | Optional scope for token request. |

---

## HTTP routes

| Method | Path |
|--------|------|
| POST | `/api/v1/integrations/forgerock/configure` |
| POST | `/idp/forgerock/integrations` |
| GET | `/api/v1/integrations/forgerock/flow` |
| GET | `/api/v1/integrations/forgerock/status` |
| GET | `/api/v1/integrations/forgerock/users` |
| POST | `/api/v1/evidence/forgerock/collect` |

---

## Normalization

[`normalize.py`](../app/integrations/categories/idp/forgerock/normalize.py) maps typical **`result`** (OpenIDM) or **`Resources`** (SCIM-like) arrays to `IAMIdentity`. If your deployment returns a different JSON shape, extend `extract_forgerock_users`.

---

## Evidence catalog

Shared IAM **`EV-*`** codes in [`iam_evidence_catalog.py`](../app/integrations/categories/idp/iam_evidence_catalog.py). Seed: [`seed_service.py`](../app/integrations/categories/idp/forgerock/seed_service.py).

---

## Limitations

- **Not** a single fixed product URL; you must align `forgerock_token_url`, `forgerock_api_base`, and `forgerock_users_path` with your **ForgeRock / Ping Identity Platform** deployment.
- AM-only vs IDM-only paths differ; wrong paths will fail validation on configure.

---

## References

- [ForgeRock / Ping Identity Platform documentation](https://backstage.forgerock.com/) (OAuth and REST paths vary by product and version).
