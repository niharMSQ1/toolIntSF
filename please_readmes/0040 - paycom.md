# Paycom — integration (HRMS)

Code: [`app/integrations/categories/hrms/paycom/`](../app/integrations/categories/hrms/paycom/).

---

## API findings

| Topic | Notes |
|-------|--------|
| **Auth** | OAuth 2.0 client credentials; **token URL and REST base are assigned in Paycom’s developer / partner program**. |
| **Data** | Employee listing path is **not global** — set **`paycom_employees_path`** to the route documented for your integration (default `/employees`). |

---

## Configuration

```json
"configuration_data": {
  "paycom_token_url": "https://.../token",
  "paycom_api_base": "https://...",
  "paycom_employees_path": "/employees",
  "client_id": "...",
  "client_secret": "..."
}
```

Optional: `access_token`, `skip_token_exchange`, `webhook_secret`.

---

## Routes

| Method | Path |
|--------|------|
| POST | `/api/v1/integrations/hrms/paycom/configure` |
| GET | `/api/v1/integrations/hrms/paycom/flow` |
| GET | `/api/v1/integrations/hrms/paycom/status` |
| GET | `/api/v1/integrations/hrms/paycom/employees` |
| POST | `/api/v1/webhooks/paycom/{org_id}/{tool_id}` |

---

## Unified mapping

**`HREmployee`** / **`HREvent`** via [`hrms/common_schema.py`](../app/integrations/categories/hrms/common_schema.py).
