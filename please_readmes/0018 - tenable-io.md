# Tenable.io (Tenable Vulnerability Management) — integration

## 1. API documentation review

Primary references:

- [Authorization (X-ApiKeys)](https://developer.tenable.com/docs/authorization) — `X-ApiKeys: accessKey=...; secretKey=...;`
- [List assets](https://developer.tenable.com/reference/assets-list-assets) — `GET https://cloud.tenable.com/assets`
- [List vulnerabilities (workbench)](https://developer.tenable.com/reference/workbenches-vulnerabilities) — `GET /workbenches/vulnerabilities`
- [List scans](https://developer.tenable.com/reference/scans-list) — `GET /scans`

### Authentication

| Item | Detail |
|------|--------|
| Header | `X-ApiKeys: accessKey=ACCESS_KEY; secretKey=SECRET_KEY;` |
| Keys | Generated in Tenable Vulnerability Management / cloud console (user profile → API Keys). |

### Implemented endpoints (this repo)

| Evidence | HTTP | Route |
|----------|------|-------|
| EV-791 | GET | `/assets` |
| EV-792 | GET | `/workbenches/vulnerabilities` |
| EV-793 | GET | `/scans` |

---

## 2. Implementation (this codebase)

Package: `app/integrations/categories/vulnerability_management/tenable_io/`.

Routes:

- `POST /api/v1/integrations/vulnerability/tenable-io/configure`
- `GET .../flow`, `GET .../status`
- `POST /api/v1/evidence/tenable-io/collect`
- `POST /api/v1/integrations/sync` with `provider_key`: `tenable_io`

`configuration_data`: `access_key`, `secret_key`, optional `api_base_url` (default `https://cloud.tenable.com`), optional `provider_key`: `tenable_io`, optional `verify_tls`.

Seed: `seed_tenable_io_evidence_masters(session, tool_id)` — **`evidence_masters.source`** = **`tenable_io`**.

---

## 3. Postman

Folder **Tenable.io** — variables `tio_api_base_url`, `tio_access_key`, `tio_secret_key`.
