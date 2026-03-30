# Qualys VM (API 2.0) — integration

## 1. API documentation review

Primary references:

- [Authentication](https://docs.qualys.com/en/vm/api/users/get_started/authentication.htm) — HTTPS, Basic auth or session (this integration uses **Basic** with API user + password).
- [Host List](https://docs.qualys.com/en/vm/api/assets/host_lists/host_list.htm) — `GET/POST /api/2.0/fo/asset/host/?action=list`
- [Host VM Detection](https://docs.qualys.com/en/vm/qweb-all-api/mergedProjects/qapi-assets/host_lists/host_detection.htm) — detection API under `/api/2.0/fo/asset/host/vm/detection/`
- [Scan List](https://docs.qualys.com/en/vm/api/scans/vm_scans/scan_list_params.htm) — `/api/2.0/fo/scan/?action=list`

Responses are **XML**; this integration parses `HOST` / `SCAN` elements with `xml.etree.ElementTree`.

### API gateway

Use the API server URL for your Qualys platform (e.g. `https://qualysapi.qualys.com`). See Qualys documentation for [API server URL](https://docs.qualys.com/en/vm/api/users/get_started/url_api_server.htm).

---

## 2. Implementation (this codebase)

Package: `app/integrations/categories/vulnerability_management/qualys/`.

| Evidence | API |
|----------|-----|
| EV-801 | Host list |
| EV-802 | VM detection list |
| EV-803 | VM scan list |

Routes:

- `POST /api/v1/integrations/vulnerability/qualys/configure`
- `POST /api/v1/evidence/qualys/collect`
- `POST /api/v1/integrations/sync` — `provider_key`: `qualys`

`configuration_data`: `username`, `password`, `api_base_url`, optional `provider_key`: `qualys`, optional `verify_tls`.

Seed: `seed_qualys_evidence_masters(session, tool_id)` — **`source`** = **`qualys`**.

---

## 3. Postman

Folder **Qualys VM** — `qualys_api_base_url`, `qualys_username`, `qualys_password`.
