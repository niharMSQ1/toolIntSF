# Tool Integrations – Step-by-step flow guide

Follow this guide in order. Each step has: **scenario**, **exact endpoint**, **request**, **response**, **what to do with the response**, and **outcome**.

**Base URL:** `http://localhost:8005` (change if your server runs elsewhere)

**Prerequisites:**
- Server running (e.g. `python main.py` or uvicorn on port 8005).
- You have: `org_id`, `user_id`, `tool_id` for Zoho, `tool_id` for Jira (from your main platform/DB).
- Zoho and Atlassian OAuth apps created; `redirect_uri` in those apps must match the callback URLs below.
- For evaluation: a valid `control_id` from your controls table.

---

## Flow overview

| Order | Scenario | What you do |
|-------|----------|-------------|
| 1 | Sanity check | GET health |
| 2 | Connect Zoho (first time) | POST create Zoho integration → open auth URL in browser → callback runs automatically |
| 3 | (Optional) Re-collect Zoho evidence | POST refresh-and-collect with Zoho integration_id |
| 4 | Connect Jira (first time) | POST create Jira integration → open auth URL in browser → callback runs automatically |
| 5 | (Optional) Re-collect Jira or all evidence | POST refresh-and-collect for one integration, or by org |
| 6 | Run compliance check: offboarding ticket per leaver | POST evaluate offboarding-ticket-per-leaver |
| 7 | (Optional) Run compliance check: access removed in 24h | POST evaluate access-removed-within-24h |

---

## Step 1 – Health check (optional)

**Scenario:** Verify the Tool Integrations API is up before starting.

**Endpoint:** `GET http://localhost:8005/health`

**Request:**
- Method: `GET`
- Headers: none required
- Body: none

**Example response (200):**
```json
{
  "status": "ok"
}
```

**What to do with the response:** If you get `"status": "ok"`, the service is running. If not, start the server and retry.

**Outcome:** Confirmation that the API is reachable.

---

## Step 2 – Create Zoho People integration and complete OAuth

**Scenario:** Connect your organization to Zoho People so the platform can pull Employee Directory and Department Structure and sync employees (including exit dates). This is the **first-time Zoho connection** flow.

### Step 2a – Create integration and get auth URL

**Endpoint:** `POST http://localhost:8005/hrms/zoho/integrations`

**Request:**
- Method: `POST`
- Headers: `Content-Type: application/json`
- Body (JSON):
```json
{
  "org_id": "YOUR_ORGANIZATION_UUID",
  "user_id": "YOUR_USER_UUID",
  "tool_id": "YOUR_ZOHO_TOOL_UUID",
  "configuration_data": {
    "client_id": "YOUR_ZOHO_CLIENT_ID",
    "client_secret": "YOUR_ZOHO_CLIENT_SECRET",
    "redirect_uri": "https://your-domain.com/hrms/zoho/callback",
    "region": "com"
  }
}
```
Replace:
- `YOUR_ORGANIZATION_UUID` – your organization id from DB.
- `YOUR_USER_UUID` – user performing the connection.
- `YOUR_ZOHO_TOOL_UUID` – tool id for "Zoho People" from the `tools` table.
- `YOUR_ZOHO_CLIENT_ID`, `YOUR_ZOHO_CLIENT_SECRET` – from your Zoho API Console app.
- `redirect_uri` – must **exactly** match the redirect URI configured in Zoho (and must point to where this backend is reachable; e.g. `http://localhost:8005/hrms/zoho/callback` for local).
- `region` – Zoho region: `com`, `in`, `eu`, etc.

**Example response (200):**
```json
{
  "authorization_url": "https://accounts.zoho.com/oauth/v2/auth?scope=...&client_id=...&redirect_uri=...&state=550e8400-e29b-41d4-a716-446655440000",
  "integration_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**What to do with the response:**
1. **Save `integration_id`** – you will need it for Step 3 (refresh-and-collect) and for API chaining.
2. **Open `authorization_url` in a browser** – the user signs in at Zoho and authorizes the app. Zoho then redirects the browser to your `redirect_uri` with query parameters `code` and `state`. The `state` value will be the same as `integration_id`.

**Outcome:** A ToolIntegration row exists (or was updated). The user must complete the browser step so the callback can run.

### Step 2b – OAuth callback (automatic – no API call by you)

**Scenario:** After the user authorizes in the browser, Zoho redirects to your callback. You do **not** call this URL yourself; the browser does.

**Endpoint (your backend):** `GET http://localhost:8005/hrms/zoho/callback`

**Request:** The browser is sent here by Zoho with:
- Query params: `code` (auth code from Zoho), `state` (same as `integration_id` from Step 2a).

Example redirect URL:
`http://localhost:8005/hrms/zoho/callback?code=1000.xxx...&state=550e8400-e29b-41d4-a716-446655440000`

**What the backend does:** Exchanges `code` for access and refresh tokens, fetches Employee Directory and Department Structure, syncs employees to the `employees` table (including `date_of_exit` when present), creates Evidence and EvidenceCollections, maps evidence to controls via ControlScenarios, then redirects the browser to your evidence listing page (e.g. `http://192.168.6.4/evidence/all-evidence`).

**Response to the browser:** HTTP 302 redirect to the evidence URL (no JSON).

**What you do:** Nothing. Ensure your Zoho app redirect URI is exactly the URL that reaches this backend (e.g. `http://localhost:8005/hrms/zoho/callback` or your public URL).

**Outcome:** Zoho is connected; tokens stored; employees synced; evidence created and linked to controls.

---

## Step 3 – (Optional) Re-run Zoho evidence collection without user re-login

**Scenario:** You already completed Step 2. You want to **refresh evidence** (e.g. daily job) without the user going through OAuth again. The backend will refresh the token if it is expired or expiring soon, then run the same evidence collection as the callback.

**Endpoint:** `POST http://localhost:8005/integrations/{integration_id}/refresh-and-collect`

Replace `{integration_id}` with the **Zoho** integration id you got from Step 2a (e.g. `550e8400-e29b-41d4-a716-446655440000`).

**Request:**
- Method: `POST`
- Headers: none required
- Body: none
- URL example: `POST http://localhost:8005/integrations/550e8400-e29b-41d4-a716-446655440000/refresh-and-collect`

**Example response (200):**
```json
{
  "status": "ok",
  "integration_id": "550e8400-e29b-41d4-a716-446655440000",
  "evidence_collected": true
}
```

**What to do with the response:** Treat as success; evidence and employees are updated. If you get 400 (e.g. token expired and no refresh token), the user must reconnect via Step 2.

**Outcome:** Latest Zoho Employee Directory and Department Structure evidence; employees table updated (including date_of_exit).

---

## Step 4 – Create Jira Service Management integration and complete OAuth

**Scenario:** Connect your organization to Jira Service Management to pull Service Desks, Customer Requests, and classified offboarding requests for compliance checks.

### Step 4a – Create integration and get auth URL

**Endpoint:** `POST http://localhost:8005/itsm/jira/integrations`

**Request:**
- Method: `POST`
- Headers: `Content-Type: application/json`
- Body (JSON):
```json
{
  "org_id": "YOUR_ORGANIZATION_UUID",
  "user_id": "YOUR_USER_UUID",
  "tool_id": "YOUR_JIRA_TOOL_UUID",
  "configuration_data": {
    "client_id": "YOUR_ATLASSIAN_CLIENT_ID",
    "client_secret": "YOUR_ATLASSIAN_CLIENT_SECRET",
    "redirect_uri": "https://your-domain.com/itsm/jira/callback"
  }
}
```
Replace with your org_id, user_id, Jira tool id, and Atlassian OAuth app credentials. `redirect_uri` must match the one configured in your Atlassian app.

**Example response (200):**
```json
{
  "authorization_url": "https://auth.atlassian.com/authorize?client_id=...&redirect_uri=...&state=660e8400-e29b-41d4-a716-446655440001",
  "integration_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

**What to do with the response:**
1. **Save `integration_id`** – needed for Step 5 (refresh-and-collect).
2. **Open `authorization_url` in a browser** – user authorizes at Atlassian; then the browser is redirected to your `redirect_uri` with `code` and `state` (state = integration_id).

**Outcome:** ToolIntegration row for Jira exists; user must complete browser auth so the callback runs.

### Step 4b – Jira OAuth callback (automatic)

**Scenario:** After Atlassian redirects the browser to your callback, the backend completes the flow.

**Endpoint (your backend):** `GET http://localhost:8005/itsm/jira/callback`

**Request:** Browser is sent here with query params `code` and `state` (state = integration_id).

**What the backend does:** Exchanges code for tokens, gets cloud_id, fetches Service Desks and Customer Requests, classifies offboarding requests (using config or defaults), creates Evidence for "Service Desks", "Customer Requests", and "Offboarding Requests", maps to controls, then redirects to the evidence listing URL.

**Response to the browser:** HTTP 302 redirect (no JSON).

**Outcome:** Jira connected; evidence created including `classified_offboarding` and `classified_requests` for evaluation.

---

## Step 5 – (Optional) Re-run evidence collection for one integration or entire org

**Scenario A – Re-collect for one integration (Jira or Zoho):** Same as Step 3 but use the **Jira** integration_id for Jira.

**Endpoint:** `POST http://localhost:8005/integrations/{integration_id}/refresh-and-collect`

**Request:** POST, no body. Use the integration_id (Zoho or Jira) you saved from Step 2a or 4a.

**Example response (200):**
```json
{
  "status": "ok",
  "integration_id": "660e8400-e29b-41d4-a716-446655440001",
  "evidence_collected": true
}
```

**What to do:** Use this to refresh evidence on a schedule or on demand for a single integration.

**Outcome:** Latest evidence for that integration.

---

**Scenario B – Re-collect for all active integrations in an organization:** Run refresh-and-collect for every active Zoho and Jira integration in the org.

**Endpoint:** `POST http://localhost:8005/integrations/refresh-and-collect-by-org?organization_id=YOUR_ORGANIZATION_UUID`

**Request:**
- Method: `POST`
- Query param: `organization_id` = your org UUID
- Body: none

**Example response (200):**
```json
{
  "status": "ok",
  "organization_id": "YOUR_ORGANIZATION_UUID",
  "total": 2,
  "success": 2,
  "failed": 0,
  "first_error": null
}
```
If some fail, `first_error` will contain `integration_id` and `detail` for the first failure.

**What to do with the response:** Check `success` and `failed`; if `failed` > 0, use `first_error` to debug (e.g. reconnect that integration via Step 2 or 4).

**Outcome:** All active integrations for that org have evidence re-collected.

---

## Step 6 – Run control: Offboarding ticket per leaver

**Scenario:** **Compliance check** – "Every employee who has left (date_of_exit set and in the past) must have at least one offboarding ticket in Jira (matched by requester email)." Use this after you have both Zoho (employees with date_of_exit) and Jira (offboarding requests) evidence.

**Endpoint:** `POST http://localhost:8005/evaluate/offboarding-ticket-per-leaver`

**Request:**
- Method: `POST`
- Headers: `Content-Type: application/json`
- Body (JSON):
```json
{
  "organization_id": "YOUR_ORGANIZATION_UUID",
  "control_id": "YOUR_CONTROL_UUID"
}
```
Use the control_id that represents "Offboarding ticket exists for every leaver" in your controls table.

**Example response (200):**
```json
{
  "control_result_id": "770e8400-e29b-41d4-a716-446655440002",
  "organization_id": "YOUR_ORGANIZATION_UUID",
  "control_id": "YOUR_CONTROL_UUID",
  "result": "PASS",
  "run_at": "2026-03-12T10:30:00.000000",
  "details": {
    "message": "Every leaver has at least one offboarding ticket",
    "leaver_count": 3,
    "offboarding_ticket_count": 5
  }
}
```
On FAIL, `result` will be `"FAIL"` and `details` will include `leavers_without_ticket` (list of emails).

**What to do with the response:** Store or display `control_result_id`, `result`, and `details`. The row is already persisted in `control_results` table. Use `result` for dashboards and audit.

**Outcome:** A control result row (PASS or FAIL) with details; audit trail for "offboarding ticket per leaver".

---

## Step 7 – (Optional) Run control: Access removed within 24h

**Scenario:** **Compliance check** – "Access must be removed within 24 hours of termination." Currently this control **does not** have IdP data, so the backend always returns **PENDING_IDP** and persists that. Use this to record that the control was evaluated and is waiting on Identity Provider integration.

**Endpoint:** `POST http://localhost:8005/evaluate/access-removed-within-24h`

**Request:**
- Method: `POST`
- Headers: `Content-Type: application/json`
- Body (JSON):
```json
{
  "organization_id": "YOUR_ORGANIZATION_UUID",
  "control_id": "YOUR_CONTROL_UUID"
}
```

**Example response (200):**
```json
{
  "control_result_id": "880e8400-e29b-41d4-a716-446655440003",
  "organization_id": "YOUR_ORGANIZATION_UUID",
  "control_id": "YOUR_CONTROL_UUID",
  "result": "PENDING_IDP",
  "run_at": "2026-03-12T10:35:00.000000",
  "details": {
    "message": "IdP integration required to evaluate account disabled status and timing.",
    "evidence_sources_required": ["HRMS", "ITSM", "Identity Provider"]
  }
}
```

**What to do with the response:** Treat as "evaluation run, result is PENDING_IDP until IdP is connected." Store the result for audit.

**Outcome:** A control result row with result PENDING_IDP; when you add an IdP integration, this evaluator can be extended to return PASS/FAIL.

---

## Quick reference – order of operations

| Step | Scenario | Method | Endpoint | You provide | Outcome |
|------|----------|--------|----------|-------------|---------|
| 1 | Health check | GET | `/health` | — | Confirm API is up |
| 2a | Connect Zoho | POST | `/hrms/zoho/integrations` | org_id, user_id, tool_id, configuration_data | authorization_url, integration_id |
| 2b | (Browser) Zoho callback | GET | `/hrms/zoho/callback` | code, state (from Zoho redirect) | Tokens + evidence + employees synced |
| 3 | Re-collect Zoho | POST | `/integrations/{integration_id}/refresh-and-collect` | integration_id (from 2a) | Fresh Zoho evidence |
| 4a | Connect Jira | POST | `/itsm/jira/integrations` | org_id, user_id, tool_id, configuration_data | authorization_url, integration_id |
| 4b | (Browser) Jira callback | GET | `/itsm/jira/callback` | code, state (from Atlassian redirect) | Tokens + evidence + offboarding classified |
| 5 | Re-collect one or all | POST | `/integrations/{id}/refresh-and-collect` or `/integrations/refresh-and-collect-by-org?organization_id=` | integration_id or organization_id | Fresh evidence |
| 6 | Evaluate offboarding ticket per leaver | POST | `/evaluate/offboarding-ticket-per-leaver` | organization_id, control_id | control_result_id, result (PASS/FAIL), details |
| 7 | Evaluate access removed 24h | POST | `/evaluate/access-removed-within-24h` | organization_id, control_id | control_result_id, result (PENDING_IDP), details |

---

## Callback URLs to configure in Zoho / Atlassian

- **Zoho:** Redirect URI must be exactly: `http://localhost:8005/hrms/zoho/callback` (or your public base URL + `/hrms/zoho/callback`).
- **Atlassian (Jira):** Redirect URI must be exactly: `http://localhost:8005/itsm/jira/callback` (or your public base URL + `/itsm/jira/callback`).

You do **not** call these URLs yourself; the browser is redirected to them by Zoho/Atlassian after the user authorizes.

---

## Postman

Import **`Tool_Integrations_Postman_Collection.json`** and set the variables (`base_url`, `org_id`, `user_id`, `tool_id_zoho`, `tool_id_jira`, `integration_id`, `control_id`). Execute requests in the same order as above.
