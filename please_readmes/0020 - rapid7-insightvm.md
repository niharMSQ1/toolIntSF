# Rapid7 InsightVM — integration

## 1. API documentation review

Primary references:

- [RESTful API overview](https://docs.rapid7.com/insightvm/restful-api/) — Security Console API v3 at `https://host:3780/api/3/...`
- [API index (Rapid7 Help)](https://help.rapid7.com/insightvm/en-us/api/index.html) — resource list including `/sites`, `/vulnerabilities`, `/scans`
- [insightvm-api-examples (GitHub)](https://github.com/rapid7/insightvm-api-examples) — Basic authentication, global administrator for full access

### Authentication

HTTP **Basic** with a local InsightVM user (typically global administrator for full API use per Rapid7 examples).

### Pagination

List endpoints support `page`, `size`, and `sort` query parameters (see official API docs for defaults and max `size`).

---

## 2. Implementation (this codebase)

Package: `app/integrations/categories/vulnerability_management/rapid7_insightvm/`.

| Evidence | HTTP | Route |
|----------|------|-------|
| EV-811 | GET | `/api/3/sites` |
| EV-812 | GET | `/api/3/vulnerabilities` |
| EV-813 | GET | `/api/3/scans` |

Responses use a `resources` array and `page` metadata (per InsightVM JSON examples).

Routes:

- `POST /api/v1/integrations/vulnerability/rapid7-insightvm/configure`
- `POST /api/v1/evidence/rapid7-insightvm/collect`
- `POST /api/v1/integrations/sync` — `provider_key`: `rapid7_insightvm`

`configuration_data`: `username`, `password`, `api_base_url` (console origin such as `https://hostname:3780`; `/api/3` is appended if missing).

Seed: `seed_rapid7_insightvm_evidence_masters(session, tool_id)` — **`source`** = **`rapid7_insightvm`**.

---

## 3. Postman

Folder **Rapid7 InsightVM** — `r7_api_base_url`, `r7_username`, `r7_password`.
