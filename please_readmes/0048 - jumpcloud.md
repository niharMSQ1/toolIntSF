# JumpCloud — Directory API (IAM)

Code: [`app/integrations/categories/idp/jumpcloud/`](../app/integrations/categories/idp/jumpcloud/).

Uses **API key** authentication (`x-api-key`) against **JumpCloud** `https://api.jumpcloud.com`, default **`GET /api/v2/systemusers`**. No OAuth token exchange in configure. See **[0001 - initialising.md](0001%20-%20initialising.md)** for G1–G5.

---

## Registry

| Item | Value |
|------|--------|
| `evidence_masters.source` | `iam` (shared catalog; legacy `jumpcloud` possible) |
| Unified sync `provider_key` | `jumpcloud` |
| Inference | `jumpcloud_api_key` in `configuration_data` (see `sync_dispatch.py`) |

---

## Configuration (`configuration_data`)

| Field | Description |
|-------|-------------|
| `jumpcloud_api_key` | JumpCloud API key. **Required.** (Generic alias `api_key` is accepted in code for resolution but **inference** uses `jumpcloud_api_key` only.) |
| `jumpcloud_users_path` | Optional path override (default `/api/v2/systemusers`). |

The API key is masked in configure responses.

---

## HTTP routes

| Method | Path |
|--------|------|
| POST | `/api/v1/integrations/jumpcloud/configure` |
| POST | `/idp/jumpcloud/integrations` |
| GET | `/api/v1/integrations/jumpcloud/flow` |
| GET | `/api/v1/integrations/jumpcloud/status` |
| GET | `/api/v1/integrations/jumpcloud/users` |
| POST | `/api/v1/evidence/jumpcloud/collect` |

---

## Evidence catalog

Shared IAM **`EV-*`** codes in [`iam_evidence_catalog.py`](../app/integrations/categories/idp/iam_evidence_catalog.py). Seed: [`seed_service.py`](../app/integrations/categories/idp/jumpcloud/seed_service.py).

---

## Limitations

- **API key** scope must include reading system users; org-level keys are sensitive—store only in `configuration_data` and rely on masked responses.
- JumpCloud list endpoints may paginate; behavior is as implemented in [`api_client.py`](../app/integrations/categories/idp/jumpcloud/api_client.py).

---

## References

- [JumpCloud API](https://docs.jumpcloud.com/) (System users and authentication).
