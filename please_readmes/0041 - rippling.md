# Rippling — integration (HRMS)

Code: [`app/integrations/categories/hrms/rippling/`](../app/integrations/categories/hrms/rippling/).

---

## API findings

| Topic | Notes |
|-------|--------|
| **Auth** | **Bearer** token — use `rippling_api_key` or `access_token` per Rippling’s developer documentation for your app. |
| **Base** | Default **`rippling_api_base`**: `https://api.rippling.com` (override if your docs specify another host). |
| **Data** | Default **`rippling_employees_path`**: `/platform/api/v1/employees` — **must match** the Rippling API version you are approved for. |

---

## Configuration

```json
"configuration_data": {
  "rippling_api_base": "https://api.rippling.com",
  "rippling_employees_path": "/platform/api/v1/employees",
  "rippling_api_key": "..."
}
```

Aliases: `access_token`, `api_key`. Optional: `webhook_secret`.

---

## Routes

| Method | Path |
|--------|------|
| POST | `/api/v1/integrations/hrms/rippling/configure` |
| GET | `/api/v1/integrations/hrms/rippling/flow` |
| GET | `/api/v1/integrations/hrms/rippling/status` |
| GET | `/api/v1/integrations/hrms/rippling/employees` |
| POST | `/api/v1/webhooks/rippling/{org_id}/{tool_id}` |

---

## Unified mapping

**`HREmployee`** / **`HREvent`** via [`hrms/common_schema.py`](../app/integrations/categories/hrms/common_schema.py).
