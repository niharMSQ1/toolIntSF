# Microsoft Defender for Endpoint — integration

This is **Defender for Endpoint** (MDE / former Microsoft Defender ATP) REST APIs — **not** [Microsoft Defender for Cloud](0010%20-%20defender-cloud.md) (ARM subscription assessments).

## 1. API documentation review (verified sources)

Primary references:

- [Hello World for Microsoft Defender for Endpoint API](https://learn.microsoft.com/en-us/defender-endpoint/api/api-hello-world) — token acquisition with resource `https://api.securitycenter.microsoft.com`, example `GET https://api.security.microsoft.com/api/alerts`.
- [List machines API](https://learn.microsoft.com/en-us/defender-endpoint/api/get-machines) — `GET /api/machines` (OData).
- [List alerts API](https://learn.microsoft.com/en-us/defender-endpoint/api/get-alerts) — `GET /api/alerts` (OData).
- [List vulnerabilities by machine and software](https://learn.microsoft.com/en-us/defender-endpoint/api/get-all-vulnerabilities-by-machines) — `GET /api/vulnerabilities/machinesVulnerabilities` (OData).

### Authentication

| Item | Detail |
|------|--------|
| Mechanism | OAuth2 **client credentials** for a Microsoft Entra **app registration** (application permissions on **WindowsDefenderATP** / Defender APIs). |
| Token audience | Microsoft documents using **`https://api.securitycenter.microsoft.com`** as the token resource so the JWT audience matches what Defender APIs expect (see Hello World troubleshooting for 403). |
| Token request | `POST https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token` with `scope=https://api.securitycenter.microsoft.com/.default`, or legacy `POST .../oauth2/token` with form field `resource=https://api.securitycenter.microsoft.com/`. This integration tries **v2.0 first**, then **v1**. |
| API calls | `Authorization: Bearer {access_token}` against **`api_base_url`** (see below). |

### API host (`api_base_url`)

| Host | Notes |
|------|--------|
| `https://api.security.microsoft.com` | Default global host in Microsoft examples. |
| `https://us.api.security.microsoft.com`, `eu.api.security.microsoft.com`, … | Regional hosts for latency (see Hello World). |

### Application permissions (examples)

Configure in Entra **App registration → API permissions → WindowsDefenderATP** (search by name). Grant **admin consent**. Typical needs for this integration’s three collectors:

- **Machines:** application permission **`Machine.ReadWrite.All`** per [list machines](https://learn.microsoft.com/en-us/defender-endpoint/api/get-machines) (Microsoft’s table); use the least privilege your org allows if Microsoft adds narrower read-only app roles later.
- **Alerts:** e.g. `Alert.Read.All` or `Alert.ReadWrite.All` per [list alerts](https://learn.microsoft.com/en-us/defender-endpoint/api/get-alerts).
- **Vulnerabilities:** `Vulnerability.Read.All` per [vulnerabilities API](https://learn.microsoft.com/en-us/defender-endpoint/api/get-all-vulnerabilities-by-machines).

### Implemented endpoints (this repo)

| Use case | HTTP | Route |
|----------|------|-------|
| Machines | GET | `/api/machines?$top={n}` |
| Alerts | GET | `/api/alerts?$top={n}` |
| Vulnerabilities | GET | `/api/vulnerabilities/machinesVulnerabilities?$top={n}` |

**Note:** [List machines](https://learn.microsoft.com/en-us/defender-endpoint/api/get-machines) documents **404** when there are no recent machines; the client maps that to an empty `value` list.

---

## 2. Integration implementation (this codebase)

| Module | Role |
|--------|------|
| `credentials.py` | `tenant_id`, `client_id`, `client_secret`, `api_base_url`, `verify_tls`. |
| `api_client.py` | Token (v2 then v1), GET wrappers, retries on 429/5xx. |
| `normalization.py` | OData `value[]` → internal `items[]`. |
| `collector.py` | Per evidence code: machines, alerts, vulnerabilities. |
| `collection_runner.py` | Same persistence pattern as other tools. |
| `seed_service.py` | Seeds `evidence_masters` for EV-771..773 with `source=defender_for_endpoint`. |

Routes:

- `POST /api/v1/integrations/endpoint/defender-for-endpoint/configure`
- `GET .../flow`, `GET .../status`
- `POST /api/v1/evidence/defender-for-endpoint/collect`
- `POST /api/v1/integrations/sync` with `provider_key`: `defender_for_endpoint`

`configuration_data` fields: `tenant_id`, `client_id`, `client_secret`, `api_base_url` (optional; defaults to `https://api.security.microsoft.com`), optional `provider_key`: `defender_for_endpoint`, optional `verify_tls`.

---

## 3. Data mapping (internal envelope)

Each collect stores:

- `normalized`: `{ vendor: defender_for_endpoint, artifact_type, item_count, items[], pagination }`
- `raw`: vendor OData JSON (truncated if extremely large)

`artifact_type` values: `machines`, `alerts`, `vulnerabilities`.

---

## 4. Postman

Folder **Microsoft Defender for Endpoint** in `postman/ToolIntegrations.postman_collection.json`.

Variables: `dfe_tenant_id`, `dfe_client_id`, `dfe_client_secret`, `dfe_api_base_url`.

---

## 5. Evidence masters

| Code | Strategy |
|------|----------|
| EV-771 | Machines list |
| EV-772 | Alerts list |
| EV-773 | Vulnerabilities by machine/software |

Seed with `seed_defender_for_endpoint_evidence_masters(session, tool_id)`.
