# SAP SuccessFactors — integration (HRMS)

Code: [`app/integrations/categories/hrms/sap_successfactors/`](../app/integrations/categories/hrms/sap_successfactors/).

---

## API findings (official)

| Topic | Documented |
|-------|------------|
| **Auth** | OAuth 2.0 client credentials against your tenant **token URL** (data-center specific). |
| **Data** | OData v2 **User** entity (and others) via `sf_odata_base_url` (e.g. `https://<host>/odata/v2`). |

Use SAP’s admin / API hub for exact hostnames, scopes, and entity permissions.

---

## Configuration

```json
"configuration_data": {
  "sf_token_url": "https://<host>/oauth/token",
  "sf_odata_base_url": "https://<host>/odata/v2",
  "client_id": "...",
  "client_secret": "..."
}
```

Optional: `access_token` with `skip_token_exchange: true`. Optional: `webhook_secret` for inbound custom webhooks.

---

## Routes

| Method | Path |
|--------|------|
| POST | `/api/v1/integrations/hrms/sap-successfactors/configure` |
| GET | `/api/v1/integrations/hrms/sap-successfactors/flow` |
| GET | `/api/v1/integrations/hrms/sap-successfactors/status` |
| GET | `/api/v1/integrations/hrms/sap-successfactors/employees` |
| POST | `/api/v1/webhooks/sap-successfactors/{org_id}/{tool_id}` |

---

## Unified mapping

Responses normalize to **`HREmployee`** / **`HREvent`** in [`hrms/common_schema.py`](../app/integrations/categories/hrms/common_schema.py).
