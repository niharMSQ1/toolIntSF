# BambooHR — integration (HRMS)

Code: [`app/integrations/categories/hrms/bamboohr/`](../app/integrations/categories/hrms/bamboohr/).

---

## API findings (official)

| Topic | Documented |
|-------|------------|
| **Auth** | **API key** with HTTP Basic: `base64("{api_key}:x")` ([API getting started](https://documentation.bamboohr.com/docs/getting-started)). |
| **Data** | **Employee directory** — `GET https://{subdomain}.bamboohr.com/api/v1/employees/directory` |

---

## Configuration

```json
"configuration_data": {
  "bamboohr_subdomain": "yourcompany",
  "bamboohr_api_key": "..."
}
```

Aliases: `subdomain`, `api_key`. Optional: `webhook_secret`.

---

## Routes

| Method | Path |
|--------|------|
| POST | `/api/v1/integrations/hrms/bamboohr/configure` |
| GET | `/api/v1/integrations/hrms/bamboohr/flow` |
| GET | `/api/v1/integrations/hrms/bamboohr/status` |
| GET | `/api/v1/integrations/hrms/bamboohr/employees` |
| POST | `/api/v1/webhooks/bamboohr/{org_id}/{tool_id}` |

---

## Unified mapping

**`HREmployee`** / **`HREvent`** via [`hrms/common_schema.py`](../app/integrations/categories/hrms/common_schema.py).
