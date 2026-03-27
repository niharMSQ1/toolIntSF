# Zoho People integration — bottlenecks and failure modes

This note complements **[0002 - zoho_integration.md](0002%20-%20zoho_integration.md)**. It describes **performance bottlenecks** and **common API mismatches** seen when running evidence collection against Zoho People (especially with debug logging enabled).

**All integrated tools:** **[0000 - integrations_index.md](0000%20-%20integrations_index.md)**.

---

## 1. Redundant employee form fetches (largest throughput cost)

Several evidence collectors each call the **same** Forms API: `GET .../api/forms/employee/getRecords` with pagination (`sIndex`, `limit`).

In code, each collector key independently runs `fetch_form_records_paginated(base, token, "employee")` for:

- Employee master list  
- Active / terminated employees  
- Reporting hierarchy  
- Employee email list  
- New hire records  
- Exit employees  

So one full collection run can **download the full employee roster multiple times** (roughly once per employee-based evidence type), multiplied by **page count** (e.g. 200 rows per page).

**Symptom:** Logs show the **same large employee JSON** repeated many times; wall time grows with roster size and number of employee-derived evidences.

**Direction for improvement:** Prefetch employee `getRecords` **once** per run and reuse rows for all collectors that only filter or project fields (see `collector.py` + `collection_runner.py`).

---

## 2. Sequential evidence loop

`run_evidence_collection` processes `evidence_masters` **one after another**. Total latency is the **sum** of all collectors, not the max.

**Symptom:** Long runs with many evidence types even when APIs are healthy.

**Direction for improvement:** Fix redundant fetches first; optional parallelism later if still needed.

---

## 3. Console and I/O when debugging HTTP

If `_get_json` (or similar) prints **full response bodies** on every request, each line can be hundreds of kilobytes. That:

- Slows the process (I/O bound)  
- Obscures real errors in noise  

**Symptom:** Terminal floods; server feels “stuck” while it prints.

**Direction for improvement:** Log status + URL + body length, or gate full bodies behind an environment flag (e.g. `ZOHO_DEBUG_HTTP`).

---

## 4. Date format: ISO vs organization format

Zoho often expects dates in the org’s format, commonly **`dd-MMM-yyyy`** (e.g. `11-Mar-2026`), while this integration builds ranges with **`YYYY-MM-DD`** from `default_date_range`.

**Symptoms (from Zoho responses):**

- Attendance: mismatch with organization date format; message may suggest `dd-MMM-yyyy` or passing `dateFormat`.  
- Leave tracker: HTTP 500 or error payload asking for `'dd-MMM-yyyy'` for `from` / `to`.

**Direction for improvement:** Format **outbound query parameters** for those endpoints to match Zoho’s docs / org settings; keep your own API in ISO if the product requires it.

---

## 5. Timesheet API: missing user

The timetracker `gettimesheet` call may return a business error such as **“No user parameter specified”** when the API expects a **user** (or employee) identifier and the request does not send one.

**Direction for improvement:** Pass the required user parameter per Zoho’s API (e.g. from integration config or from cached employee IDs), or document that your OAuth scope/org role only allows certain access patterns.

---

## 6. Exit clearance: form link name

Exit clearance uses `fetch_form_records_paginated(..., "exit")`. The **form link name** is **organization-specific**. If your tenant does not use the literal link `exit`, Zoho returns an error (e.g. form name invalid).

**Direction for improvement:** Make the form link name **configurable** in `tool_integrations.configuration_data`.

---

## 7. Training / LMS (courses) and subscription

The courses endpoint may return an error such as **module not included in subscription** (e.g. upgrade required). That is a **Zoho plan** limitation, not something the integration can bypass in code.

**Direction for improvement:** Treat as a known limitation: skip collector, or surface a clear message in evidence / collection status.

---

## 8. HTTP 200 with errors in JSON body

Zoho People APIs sometimes return **HTTP 200** with `response.status`, `errors`, or `message` indicating failure. Code that only uses `raise_for_status()` on the HTTP layer may still treat the call as “OK” and persist **error JSON** as if it were evidence.

**Direction for improvement:** After `json()`, detect Zoho-side failure in the envelope and fail the collector so `evidence_collection` records **failed** with a clear detail.

---

## Quick reference: where this lives in code

| Area | Location |
|------|----------|
| Collectors, date range, Zoho GETs | `app/integrations/categories/hrms/zoho_people/collector.py` |
| Per-run orchestration | `app/integrations/categories/hrms/zoho_people/collection_runner.py` |
| Evidence seed / API hints | `app/integrations/categories/hrms/zoho_people/seed.py` |
| OAuth (not People data APIs) | `app/integrations/categories/hrms/zoho_people/oauth.py` |

---

## Related doc

- **[0002 - zoho_integration.md](0002%20-%20zoho_integration.md)** — end-to-end Zoho flow (configure, OAuth, evidence).
