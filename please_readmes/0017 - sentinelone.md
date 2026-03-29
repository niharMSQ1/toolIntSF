# SentinelOne — integration

## 1. API documentation review (verified sources)

SentinelOne publishes the **Management Console Web API** (commonly referenced as **v2.1**). Exact PDF/HTML docs are tenant-scoped in the product; integrators and open wrappers document the same URI shapes.

Authoritative patterns used here:

| Topic | Reference |
|-------|-----------|
| URI prefix | `https://{your-console-host}/web/api/v2.1` — see community/API mirrors and [SentinelOne PowerShell wrapper](https://celerium.github.io/SentinelOne-PowerShellWrapper/) (e.g. **Get-SentinelOneAgents** → `/agents`). |
| Authentication | API token: **`Authorization: ApiToken <token>`** — tokens are created in the SentinelOne console (user profile / API token); see vendor and partner hardening guides (e.g. [NinjaOne — SentinelOne API tokens](https://www.ninjaone.com/docs/integrations/antivirus/sentinelone/understanding-sentinelone-api-tokens/)). |
| Pagination | List endpoints support `limit` (typical max **1000**), `cursor`, `skip` (see integrator docs such as [BlinkOps — Get Threats](https://docs.blinkops.com/docs/integrations/sentinelone/actions/get-threats)). |
| Response shape | List responses commonly expose a top-level **`data`** array plus **`pagination`** (integrator docs). |

### Implemented endpoints (this repo)

| Use case | HTTP | Route | Notes |
|----------|------|-------|-------|
| Agents | GET | `/agents` | Inventory; validate uses `?limit=1`. |
| Threats | GET | `/threats` | Threat list; `limit` capped at 1000 in API client. |
| Installed applications | GET | `/installed-applications` | Application Risk inventory (vendor **Application Risk** / Complete SKU may apply; HTTP **403** if not entitled). |

---

## 2. Integration implementation (this codebase)

| Module | Role |
|--------|------|
| `credentials.py` | `api_token`, `api_base_url` (console origin **or** full `.../web/api/v2.1`), `verify_tls`. |
| `api_client.py` | `ApiToken` header, GET with retries on 429/5xx. |
| `normalization.py` | Maps `data[]` to internal `items[]`. |
| `collector.py` | Per evidence code: agents, threats, installed applications. |
| `collection_runner.py` | Standard persistence (`upsert_evidence_full_replace`, `insert_evidence_collection`). |
| `seed_service.py` | Seeds EV-781..783 with `source=sentinelone`. |

Routes:

- `POST /api/v1/integrations/endpoint/sentinelone/configure`
- `GET .../flow`, `GET .../status`
- `POST /api/v1/evidence/sentinelone/collect`
- `POST /api/v1/integrations/sync` with `provider_key`: `sentinelone`

`configuration_data`: `api_token`, `api_base_url` (see below), optional `provider_key`: `sentinelone`, optional `verify_tls`.

**`api_base_url`:** Either the **console origin** (e.g. `https://usea1.sentinelone.net`) — the app appends `/web/api/v2.1` — or the **full API root** including `/web/api/v2.1`.

---

## 3. Data mapping (internal envelope)

Each collect stores:

- `normalized`: `{ vendor: sentinelone, artifact_type, item_count, items[], pagination }`
- `raw`: vendor JSON (truncated if extremely large)

`artifact_type` values: `agents`, `threats`, `installed_applications`.

---

## 4. Postman

Folder **SentinelOne** in `postman/ToolIntegrations.postman_collection.json`.

Variables: `s1_api_base_url`, `s1_api_token`.

---

## 5. Evidence masters

| Code | Strategy |
|------|----------|
| EV-781 | Agents |
| EV-782 | Threats |
| EV-783 | Installed applications |

Seed with `seed_sentinelone_evidence_masters(session, tool_id)`.
