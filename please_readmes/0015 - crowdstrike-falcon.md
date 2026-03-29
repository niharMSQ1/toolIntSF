# CrowdStrike Falcon — integration

## 1. API documentation review (verified sources)

Primary references:

- [CrowdStrike Developer Center — OpenAPI](https://developer.crowdstrike.com/docs/openapi) — regional Swagger links; **requires Falcon console login** for full spec.
- [FalconPy — OAuth2 service collection](https://www.falconpy.io/Service-Collections/OAuth2.html) — operation IDs and routes: `POST /oauth2/token`, `POST /oauth2/revoke`.
- [FalconPy — Spotlight Vulnerabilities](https://www.falconpy.io/Service-Collections/Spotlight-Vulnerabilities.html) — `GET /spotlight/combined/vulnerabilities/v1` (filter required, pagination `after`, limits).

### Authentication

| Item | Detail |
|------|--------|
| Mechanism | OAuth2 **client credentials** using API **client ID** and **client secret** created in the Falcon console. |
| Token request | `POST {api_base_url}/oauth2/token` |
| Content-Type | `application/x-www-form-urlencoded` |
| Body fields | At minimum `client_id` and `client_secret`. FalconPy examples also use `grant_type` / MSSP `member_cid` where applicable. This integration tries `grant_type=client_credentials` first, then retries without `grant_type` if the first call fails (some public examples show only id/secret). |
| API calls | `Authorization: Bearer {access_token}` |
| Token lifetime | Response includes `expires_in` (commonly ~30 minutes per FalconPy docs). |

### Base URLs (SaaS regions)

From [Developer Center OpenAPI](https://developer.crowdstrike.com/docs/openapi) (table excerpt):

| Region | API host |
|--------|----------|
| US-1 | `https://api.crowdstrike.com` |
| US-2 | `https://api.us-2.crowdstrike.com` |
| EU-1 | `https://api.eu-1.crowdstrike.com` |
| US-GOV-1 | `https://api.laggar.gcw.crowdstrike.com` |
| US-GOV-2 | `https://api.us-gov-2.crowdstrike.mil` |

On-prem: use the API hostname documented in **your** Falcon on-premises deployment (see CrowdStrike on-prem admin documentation).

### Implemented endpoints (this repo)

| Use case | HTTP | Route | Notes |
|----------|------|-------|--------|
| Token | POST | `/oauth2/token` | See above. |
| Host inventory (IDs) | GET | `/devices/queries/devices/v1` | QueryDevices — returns `resources` (device IDs). Pagination via `offset` per API. |
| Detections (IDs) | GET | `/detects/queries/detects/v1` | QueryDetects — returns detection IDs in `resources`. |
| Vulnerabilities (Spotlight) | GET | `/spotlight/combined/vulnerabilities/v1` | **Required** FQL `filter` parameter. Default in app: `status:'open'`. Override with `spotlight_filter` / `spotlight_fql` in `configuration_data`. |

### Pagination, rate limits, errors

- **Pagination:** Host/detect query APIs support `limit` (and `offset` where documented). Spotlight uses `limit` and cursor-style `after` for large result sets (see Spotlight docs).
- **Rate limits:** CrowdStrike may return HTTP **429**; the API client retries GETs up to 3 times with backoff for 429/5xx.
- **Schemas:** Full JSON schemas are in the regional Swagger; this integration stores vendor `resources` plus a **normalized** envelope (see below).

---

## 2. Integration implementation (this codebase)

| Module | Role |
|--------|------|
| `credentials.py` | Resolves `api_base_url`, `client_id`, `client_secret`, optional `member_cid`, `verify_tls`, Spotlight FQL default. |
| `api_client.py` | OAuth token, GET wrappers, retries on GET. |
| `normalization.py` | Maps Falcon JSON to internal `artifact_type` + `items[]` with stable keys. |
| `collector.py` | Per evidence code: hosts, detects, Spotlight; attaches `normalized` + `raw`. |
| `collection_runner.py` | Same persistence pattern as other tools (`upsert_evidence_full_replace`, `insert_evidence_collection`). |
| `seed_service.py` | Seeds `evidence_masters` for EV-761..763 with `source=crowdstrike_falcon`. |

Routes:

- `POST /api/v1/integrations/endpoint/crowdstrike-falcon/configure`
- `GET .../flow`, `GET .../status`
- `POST /api/v1/evidence/crowdstrike-falcon/collect`
- `POST /api/v1/integrations/sync` with `provider_key`: `crowdstrike_falcon`

`configuration_data` fields: `client_id`, `client_secret`, `api_base_url`, optional `member_cid`, `verify_tls`, optional `spotlight_filter` (FQL).

---

## 3. Data mapping (internal envelope)

Each collect stores:

- `normalized`: `{ vendor, artifact_type, item_count, items[{ id, title, kind, severity?, timestamp?, metadata? }], pagination }`
- `raw`: vendor response (truncated if extremely large)

`artifact_type` values: `host_inventory`, `detections`, `vulnerabilities`.

---

## 4. Postman

Folder **CrowdStrike Falcon** in `postman/ToolIntegrations.postman_collection.json` — configure, flow, status, collect, sync, and direct `POST .../oauth2/token`.

Variables: `cs_falcon_api_base_url`, `cs_falcon_client_id`, `cs_falcon_client_secret`, `cs_falcon_member_cid`.

---

## 5. Sample requests / responses

**Token (simplified):**

```http
POST /oauth2/token HTTP/1.1
Host: api.crowdstrike.com
Content-Type: application/x-www-form-urlencoded

client_id=...&client_secret=...&grant_type=client_credentials
```

```json
{
  "access_token": "...",
  "expires_in": 1799,
  "token_type": "bearer"
}
```

**Host query (abbreviated):**

```json
{
  "resources": ["device-id-1", "device-id-2"],
  "meta": { "query_time": 1.23, "pagination": { "total": 2 } }
}
```

(Exact `meta` shape — see Swagger for your cloud.)

---

## 6. Limitations

- **Query vs entity APIs:** This phase collects **ID lists** for hosts/detects (query APIs). Enriching to full device or detection **entities** requires additional `GET` calls with those IDs (future enhancement).
- **Spotlight FQL:** Wrong filters return API errors; test filters in Falcon UI or Swagger.
- **MSSP:** `member_cid` is passed on the token request when set; behavior follows CrowdStrike MSSP documentation.
- **Evidence codes:** EV-761–EV-763 reserved for CrowdStrike; seed before collect.

---

## Related

- [0000 - integrations_index.md](0000%20-%20integrations_index.md)
- [Postman collection](../postman/ToolIntegrations.postman_collection.json)
