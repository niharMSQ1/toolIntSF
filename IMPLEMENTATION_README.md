# Tool Integrations – Implementation Summary, Code Flow & API Reference

This document describes what was implemented for the GRC Tool Integrations backend, how the code flows, and how to call all APIs (including a full Postman collection).

---

## 1. What Was Implemented

The implementation follows the plan **"What We Can Do With the Existing Code (Readme vs Codebase)"**. Delivered items:

| # | Work item | Status | Where |
|---|-----------|--------|-------|
| 1 | Populate `Employees.date_of_exit` from Zoho | Done | `HRMS_Integrations/Zoho_people/service.py` |
| 2 | Configurable offboarding detection for Jira + classified list | Done | `ITSM_Integrations/Jira_servicedesk/service.py` |
| 3 | Token refresh + scheduled/on-demand collection | Done | `integration_collection.py`, routes in `main.py` |
| 4 | Control evaluation module + ControlResults table | Done | `control_evaluation.py`, `models.py`, `migrations/001_create_control_results.sql` |
| 5 | Normalized ticket data in evidence (JSON) | Done | Jira evidence includes `classified_offboarding` and `classified_requests` |
| 6 | IdP placeholder + PENDING_IDP handling | Done | `IdP_Integrations/`, `evaluate/access-removed-within-24h` |

### 1.1 HRMS (Zoho People)

- **Exit date sync:** `_parse_zoho_date()` parses Zoho date formats; `_sync_employees_from_zoho` now reads common exit-date fields (e.g. `LastWorkingDate`, `Date of Exit`, `Termination Date`) and sets `Employees.date_of_exit`. Employee `status` is set to `inactive` when an exit date is present.
- **Provider tag:** Integration `configuration_data` includes `"provider": "zoho_people"` for routing refresh/collect.
- **Evidence collected from Zoho:** Employee Directory, Department Structure, Employee Termination Records (derived from directory), Employee Onboarding Records (derived), Employee Profile Verification (same as directory). Optionally: **Attendance Records** (if Zoho attendance API succeeds) and **Training Completion Records** (if `TRAINING_FORM_LINK_NAME` is set in `HRMS_Integrations/Zoho_people/config.py` and the form API succeeds). Attendance and Training are best-effort; on API error that evidence type is skipped for that run.
- **Evidence names skipped (not provided by Zoho):** Access Revocation Logs, User Access Permissions, System Audit Logs, User Activity Logs, Role-Based Access Control. These are not created as Evidence; they are skipped silently (optional debug log lists them).

### 1.2 ITSM (Jira Service Management)

- **Deprovision config:** `_get_deprovision_config()` reads from integration config: `deprovision_identifier` (field, values, keywords, optional_labels) and `correlation_field`. Defaults match readme Section 6.
- **Request normalization:** `_normalize_request_item()` maps Jira request payloads to a canonical shape (request_key, request_type, summary, created_at, requester_email, labels).
- **Offboarding classification:** `_classify_offboarding()` marks requests as offboarding by request type, summary keywords, or labels.
- **Evidence:** "Customer Requests" payload now has `classified_offboarding` and `classified_requests`. A third evidence type **"Offboarding Requests"** stores only the classified offboarding list and config used.
- **Provider tag:** `"provider": "jira_servicedesk"` in configuration_data.

### 1.3 Token Refresh & Evidence Collection

- **POST `/integrations/{integration_id}/refresh-and-collect`:** Refreshes access token if expired or expiring within 5 minutes, then runs the appropriate `collect_and_persist_evidence` (Zoho or Jira) and commits.
- **POST `/integrations/refresh-and-collect-by-org?organization_id=<uuid>`:** Runs refresh-and-collect for all active integrations in the org; returns success/failed counts.

### 1.4 Control Evaluation

- **Model:** `ControlResults` in `models.py` (organization_id, control_id, run_at, result, details JSON, evidence_ids).
- **SQL migration:** `migrations/001_create_control_results.sql` creates the table if not using Alembic.
- **Evaluator "Offboarding ticket per leaver":** Uses Employees (date_of_exit ≤ today) and latest Jira evidence (classified_offboarding); matches by requester_email; returns PASS/FAIL and persists to ControlResults.
- **Evaluator "Access removed within 24h":** Stub that returns **PENDING_IDP** until an IdP is integrated; result is persisted to ControlResults.
- **Endpoints:**  
  - **POST `/evaluate/offboarding-ticket-per-leaver`** (body: organization_id, control_id)  
  - **POST `/evaluate/access-removed-within-24h`** (body: organization_id, control_id)

### 1.5 IdP Placeholder

- **Package:** `IdP_Integrations/` with `__init__.py` and `README.md` describing planned Okta/Entra/Google integrations and implementation pattern.

---

## 2. Flow of the Code

### 2.1 Application entry and routing

```
main.py
  ├── FastAPI app (title: "Tool Integrations Backend - GRC Platform")
  ├── GET /health
  ├── zoho_people_router    (prefix /hrms/zoho)
  ├── jira_servicedesk_router (prefix /itsm/jira)
  ├── integration_collection_router (prefix /integrations)
  └── control_evaluation_router (prefix /evaluate)
```

### 2.2 OAuth and evidence collection (Zoho)

```
1. Client calls POST /hrms/zoho/integrations
   Body: { org_id, user_id, tool_id, configuration_data: { client_id, client_secret, redirect_uri, region } }
   → Creates/updates ToolIntegrations row, sets provider = "zoho_people"
   → Returns { authorization_url, integration_id }

2. User opens authorization_url in browser, signs in at Zoho, is redirected to redirect_uri with ?code=...&state=<integration_id>

3. Client (or browser) hits GET /hrms/zoho/callback?code=...&state=...
   → Loads integration by state (integration_id)
   → ZohoPeopleClient.exchange_code_for_tokens(code) → access_token, refresh_token, expires_in
   → Stores tokens + access_token_expires_at in configuration_data, sets is_active = True
   → ZohoPeopleClient.fetch_employee_directory(access_token), fetch_department_structure(access_token)
   → service.collect_and_persist_evidence():
        - _sync_employees_from_zoho(): upserts Employees (email, name, department, designation, employee_status, date_of_exit, etc.)
        - Creates Evidence + EvidenceCollections for "Employee Directory", "Department Structure"
        - _map_evidence_to_controls(): finds ControlScenarios by tool_id + evidence_name, creates EvidenceMappeds to controls
   → Commit; redirect to evidence listing URL
```

### 2.3 OAuth and evidence collection (Jira)

```
1. Client calls POST /itsm/jira/integrations
   Body: { org_id, user_id, tool_id, configuration_data: { client_id, client_secret, redirect_uri } }
   → Creates/updates ToolIntegrations, sets provider = "jira_servicedesk"
   → Returns { authorization_url, integration_id }

2. User authorizes at Atlassian; redirect to redirect_uri with ?code=...&state=<integration_id>

3. GET /itsm/jira/callback?code=...&state=...
   → Exchange code for tokens; get_accessible_resources(access_token) → cloud_id
   → Store access_token, refresh_token, cloud_id, provider in configuration_data, is_active = True
   → service.collect_and_persist_evidence():
        - fetch_servicedesks(cloud_id, access_token), fetch_customer_requests(cloud_id, access_token)
        - _get_deprovision_config(config), _classify_offboarding(requests_data, config)
        - Build requests_payload with classified_offboarding + classified_requests
        - Create Evidence + EvidenceCollections for "Service Desks", "Customer Requests", "Offboarding Requests"
        - _map_evidence_to_controls() for each evidence name
   → Commit; redirect
```

### 2.4 On-demand refresh and collection

```
POST /integrations/{integration_id}/refresh-and-collect
  → Load ToolIntegrations by integration_id
  → If access_token_expires_at is missing or within 5 min: refresh via ZohoPeopleClient or JiraServicedeskClient.refresh_access_token()
  → Update configuration_data with new tokens
  → Call zoho_collect() or jira_collect() (same as callback flow), commit
  → Return { status, integration_id, evidence_collected: true }

POST /integrations/refresh-and-collect-by-org?organization_id=<uuid>
  → Select all ToolIntegrations where organization_id and is_active
  → For each, call refresh_and_collect(integration_id, db); aggregate success/failed, first_error
  → Return { status, organization_id, total, success, failed, first_error }
```

### 2.5 Control evaluation

```
POST /evaluate/offboarding-ticket-per-leaver
  Body: { organization_id, control_id }
  → run_and_persist_offboarding_ticket_control():
       - _get_leavers(db, organization_id): Employees with date_of_exit <= today
       - _get_latest_offboarding_requests(db, organization_id): latest EvidenceCollections (Offboarding Requests / Customer Requests) with classified_offboarding or classified_requests
       - Match leaver emails to requester_email in offboarding list → PASS if all matched, else FAIL with leavers_without_ticket
       - Insert ControlResults (result, details, evidence_ids), commit
  → Return { control_result_id, organization_id, control_id, result, run_at, details }

POST /evaluate/access-removed-within-24h
  Body: { organization_id, control_id }
  → run_and_persist_access_removed_24h(): always writes result = "PENDING_IDP", details = { message: "IdP integration required..." }
  → Return same shape as above
```

### 2.6 Data flow (high level)

```
External (Zoho / Jira)
       ↓
OAuth (create integration → auth URL → callback with code)
       ↓
Tokens stored in ToolIntegrations.configuration_data
       ↓
collect_and_persist_evidence()
  → Raw API payloads → Evidence + EvidenceCollections (tool_evidence)
  → Employees sync (Zoho) / classified_offboarding (Jira) for normalization
  → ControlScenarios + EvidenceMappeds (evidence → controls)
       ↓
Refresh-and-collect endpoint can re-run collection without user re-auth
       ↓
Control evaluation reads Employees + EvidenceCollections (classified data)
       ↓
ControlResults table (PASS / FAIL / PENDING_IDP)
```

---

## 3. API Summary (Postman-ready)

Base URL (default): **`http://localhost:8005`**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/hrms/zoho/integrations` | Create/update Zoho integration; returns auth URL |
| GET | `/hrms/zoho/callback` | Zoho OAuth callback (code, state) |
| POST | `/itsm/jira/integrations` | Create/update Jira integration; returns auth URL |
| GET | `/itsm/jira/callback` | Jira OAuth callback (code, state) |
| POST | `/integrations/{integration_id}/refresh-and-collect` | Refresh token (if needed) and run evidence collection for one integration |
| POST | `/integrations/refresh-and-collect-by-org?organization_id=<uuid>` | Refresh and collect for all active integrations in org |
| POST | `/evaluate/offboarding-ticket-per-leaver` | Run "offboarding ticket per leaver" control; persist result |
| POST | `/evaluate/access-removed-within-24h` | Run "access removed within 24h" control; returns PENDING_IDP until IdP added |

---

## 4. Postman Collection

A complete Postman Collection v2.1 file is provided: **`Tool_Integrations_Postman_Collection.json`**.

Import it in Postman: **File → Import → Upload** and select that file.

- **Base URL** is set to `http://localhost:8005` in the collection variable `base_url`. Change it if your server runs elsewhere.
- All requests use `{{base_url}}` for the host.
- Request bodies for POST APIs are pre-filled with example/placeholder UUIDs; replace with your `org_id`, `user_id`, `tool_id`, `integration_id`, `organization_id`, and `control_id` as needed.
- The **Zoho** and **Jira** callback URLs are intended to be opened in a browser (or after redirect); in Postman you can use a GET request with query params `code` and `state` after you have them from the OAuth redirect.

---

## 5. Prerequisites and setup

1. **Database:** Run `migrations/001_create_control_results.sql` if the `control_results` table does not exist.
2. **Tools and ControlScenarios:** The main platform should have `Tools` rows (e.g. for "Zoho People", "Jira Service Management") and `ControlScenarios` rows linking evidence names (e.g. "Employee Directory", "Department Structure", "Service Desks", "Customer Requests", "Offboarding Requests") to control IDs so that EvidenceMappeds are created.
3. **Zoho/Jira apps:** Register OAuth apps in Zoho and Atlassian; use the correct client_id, client_secret, and redirect_uri (must match the URL that serves `/hrms/zoho/callback` and `/itsm/jira/callback`).
4. **Jira offboarding config (optional):** When storing integration config, you can set `configuration_data.deprovision_identifier` to match your JSM request types (e.g. `{ "field": "requestType", "values": ["Offboarding", "Employee Exit"] }`).

---

## 6. File reference

| Path | Purpose |
|------|---------|
| `main.py` | App entry; mounts all routers; GET /health |
| `HRMS_Integrations/Zoho_people/routes.py` | Zoho create integration + callback |
| `HRMS_Integrations/Zoho_people/service.py` | Zoho evidence collection; employee sync; date_of_exit parsing |
| `HRMS_Integrations/Zoho_people/client.py` | Zoho OAuth + Employee Directory / Department APIs |
| `ITSM_Integrations/Jira_servicedesk/routes.py` | Jira create integration + callback |
| `ITSM_Integrations/Jira_servicedesk/service.py` | Jira evidence collection; offboarding classification |
| `ITSM_Integrations/Jira_servicedesk/client.py` | Jira OAuth + Service Desks / Customer Requests APIs |
| `integration_collection.py` | Refresh-and-collect endpoints |
| `control_evaluation.py` | Offboarding-ticket and access-removed-24h evaluators + endpoints |
| `models.py` | ControlResults model; Employees, Evidence, EvidenceCollections, etc. |
| `migrations/001_create_control_results.sql` | Create control_results table |
| `IdP_Integrations/` | Placeholder for future IdP integrations |

---

*End of implementation README.*
