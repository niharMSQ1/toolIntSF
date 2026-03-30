# Smartsheet — integration

Code: [`app/integrations/categories/project_management/smartsheet/`](../app/integrations/categories/project_management/smartsheet/).

---

## API findings (official)

| Topic | Documented |
|-------|------------|
| **Base** | `https://api.smartsheet.com/2.0/` ([Smartsheet API](https://smartsheet.redoc.ly/)) |
| **Auth** | **Bearer** access token in `Authorization` ([Overview](https://smartsheet.redoc.ly/tag/Authorization)) |
| **Sheets / rows** | `GET /users/me`, `GET /sheets`, `GET /sheets/{sheetId}/rows` |

---

## Authentication setup

Create an access token in Smartsheet (personal or OAuth per their docs). **Configure** with:

```json
"configuration_data": { "api_token": "<access_token>" }
```

Aliases: `smartsheet_access_token`, `access_token`.

---

## Routes

`POST .../configure`, `GET .../flow`, `GET .../status`, `GET .../me`, `GET .../sheets`, `GET .../sheets/{sheet_id}/rows`

---

## Unified mapping

- **UnifiedUser** ← `/users/me`
- **UnifiedProject** ← sheet summary
- **UnifiedTask** ← row (primary cell text as name when available)

---

## Limitations

- Row → task mapping is **best-effort** from cell data; adjust for your sheet layout.
