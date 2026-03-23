from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx

from app.integrations.categories.hrms.zoho_people.credentials import resolve_access_token, resolve_region
from app.integrations.categories.hrms.zoho_people.regions import people_base_url
from app.integrations.categories.hrms.zoho_people.seed import CODE_TO_COLLECTOR


def _people_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Zoho-oauthtoken {access_token}"}


def _flatten_form_get_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize Zoho People forms getRecords JSON into a list of row dicts."""
    root = payload.get("response") or payload
    result = root.get("result")
    if not result:
        return []
    rows: list[dict[str, Any]] = []
    if isinstance(result, list):
        for block in result:
            if not isinstance(block, dict):
                continue
            for _rid, recs in block.items():
                if isinstance(recs, list):
                    for r in recs:
                        if isinstance(r, dict):
                            rows.append(r)
    return rows


def _get_json(client: httpx.Client, url: str, headers: dict[str, str], params: dict[str, Any] | None = None) -> Any:
    r = client.get(url, headers=headers, params=params, timeout=120.0)
    r.raise_for_status()
    return r.json()


def fetch_form_records_paginated(
    base: str,
    token: str,
    form_link: str,
    *,
    limit: int = 200,
) -> dict[str, Any]:
    """Fetch all pages from /api/forms/{form}/getRecords (best effort)."""
    headers = _people_headers(token)
    s_index = 1
    combined_rows: list[dict[str, Any]] = []
    last_raw: dict[str, Any] = {}
    with httpx.Client() as client:
        while True:
            url = f"{base.rstrip('/')}/api/forms/{form_link}/getRecords"
            params: dict[str, Any] = {"sIndex": s_index, "limit": limit}
            raw = _get_json(client, url, headers, params)
            last_raw = raw
            rows = _flatten_form_get_records(raw)
            if not rows:
                break
            combined_rows.extend(rows)
            if len(rows) < limit:
                break
            s_index += limit
            if s_index > 20000:  # safety
                break
    return {"raw_last_page": last_raw, "rows": combined_rows, "total_rows": len(combined_rows)}


def _status_value(row: dict[str, Any]) -> str:
    for k in ("Employeestatus", "Employee status", "employeestatus"):
        if k in row and row[k]:
            return str(row[k]).strip().lower()
    for key in row:
        if "status" in key.lower() and "employee" in key.lower():
            return str(row[key]).strip().lower()
    return ""


def _is_active_status(val: str) -> bool:
    if "inactive" in val or "terminat" in val or "exit" in val:
        return False
    return "active" in val or val in ("confirmed", "probation", "full time")


def _is_terminated_status(val: str) -> bool:
    return any(x in val for x in ("terminat", "exit", "reliev", "inactive"))


def default_date_range(
    date_from: str | None, date_to: str | None
) -> tuple[str, str]:
    if date_to:
        end = datetime.strptime(date_to, "%Y-%m-%d").date()
    else:
        end = date.today()
    if date_from:
        start = datetime.strptime(date_from, "%Y-%m-%d").date()
    else:
        start = end - timedelta(days=90)
    return start.isoformat(), end.isoformat()


def collect_for_master(
    master: dict[str, Any],
    cfg: dict[str, Any],
    *,
    date_from: str | None,
    date_to: str | None,
) -> dict[str, Any]:
    """
    Returns a dict suitable for evidence.content (full replace).
    On failure raises Exception.
    """
    token = resolve_access_token(cfg)
    if not token:
        raise ValueError("Missing access_token; complete OAuth first.")
    base = cfg.get("people_base_url") or people_base_url(resolve_region(cfg))
    code = master["code"]
    key = CODE_TO_COLLECTOR.get(code)
    if not key:
        raise ValueError(f"No collector registered for evidence_masters.code={code!r}")
    d0, d1 = default_date_range(date_from, date_to)

    if key == "employee_master":
        data = fetch_form_records_paginated(base, token, "employee")
        return {"source": "zoho_people", "collector_key": key, "form": "employee", **data}

    if key == "active_employees":
        data = fetch_form_records_paginated(base, token, "employee")
        rows = [r for r in data["rows"] if _is_active_status(_status_value(r))]
        return {
            "source": "zoho_people",
            "collector_key": key,
            "form": "employee",
            "total_rows": len(rows),
            "rows": rows,
        }

    if key == "terminated_employees":
        data = fetch_form_records_paginated(base, token, "employee")
        rows = [r for r in data["rows"] if _is_terminated_status(_status_value(r))]
        return {
            "source": "zoho_people",
            "collector_key": key,
            "form": "employee",
            "total_rows": len(rows),
            "rows": rows,
        }

    if key == "department_structure":
        data = fetch_form_records_paginated(base, token, "department")
        return {"source": "zoho_people", "collector_key": key, "form": "department", **data}

    if key == "reporting_hierarchy":
        data = fetch_form_records_paginated(base, token, "employee")
        slim = []
        for r in data["rows"]:
            entry = {k: r[k] for k in r if re.search(r"report|manager|lead|supervisor", k, re.I)}
            entry["_full_record_id"] = r.get("EmployeeID") or r.get("Zoho_ID")
            slim.append(entry)
        return {
            "source": "zoho_people",
            "collector_key": key,
            "note": "Fields matching report/manager/lead/supervisor; extend if your org uses other field names.",
            "rows": slim,
            "total_rows": len(slim),
        }

    if key == "employee_email_list":
        data = fetch_form_records_paginated(base, token, "employee")
        slim = []
        for r in data["rows"]:
            slim.append(
                {
                    "EmployeeID": r.get("EmployeeID"),
                    "EmailID": r.get("EmailID") or r.get("Email"),
                    "FirstName": r.get("FirstName"),
                    "LastName": r.get("LastName"),
                }
            )
        return {"source": "zoho_people", "collector_key": key, "rows": slim, "total_rows": len(slim)}

    if key == "attendance_logs":
        headers = _people_headers(token)
        url = f"{base.rstrip('/')}/people/api/attendance/getUserReport"
        out: list[dict[str, Any]] = []
        start_index = 0
        with httpx.Client() as client:
            while True:
                params = {
                    "sdate": d0,
                    "edate": d1,
                    "startIndex": start_index,
                }
                raw = _get_json(client, url, headers, params)
                res = raw.get("result")
                if not res:
                    break
                if isinstance(res, list):
                    out.extend(res)
                if len(res) < 100:
                    break
                start_index += 100
                if start_index > 5000:
                    break
        return {"source": "zoho_people", "collector_key": key, "date_from": d0, "date_to": d1, "result": out}

    if key == "timesheet_records":
        headers = _people_headers(token)
        url = f"{base.rstrip('/')}/people/api/timetracker/gettimesheet"
        with httpx.Client() as client:
            params = {
                "fromDate": d0,
                "toDate": d1,
                "sIndex": 0,
                "limit": 200,
            }
            raw = _get_json(client, url, headers, params)
        return {"source": "zoho_people", "collector_key": key, "date_from": d0, "date_to": d1, "payload": raw}

    if key == "leave_records":
        headers = _people_headers(token)
        url = f"{base.rstrip('/')}/api/v2/leavetracker/leaves/records"
        rows: list[dict[str, Any]] = []
        start_index = 0
        with httpx.Client() as client:
            while True:
                params = {
                    "from": d0,
                    "to": d1,
                    "startIndex": start_index,
                    "limit": 200,
                }
                raw = _get_json(client, url, headers, params)
                if not isinstance(raw, dict):
                    break
                chunk = raw.get("records") or raw.get("result") or []
                if isinstance(chunk, dict):
                    chunk = chunk.get("records") or []
                if not chunk:
                    break
                if isinstance(chunk, list):
                    rows.extend(chunk)
                if len(chunk) < 200:
                    break
                start_index += 200
        return {"source": "zoho_people", "collector_key": key, "date_from": d0, "date_to": d1, "records": rows}

    if key == "training_completion":
        headers = _people_headers(token)
        url = f"{base.rstrip('/')}/api/v1/courses"
        with httpx.Client() as client:
            raw = _get_json(client, url, headers, {"startIndex": 0})
        return {"source": "zoho_people", "collector_key": key, "payload": raw}

    if key == "policy_acknowledgement":
        return {
            "source": "zoho_people",
            "collector_key": key,
            "skipped": True,
            "reason": "Requires policy file_id list from Zoho Files; configure file_ids in integration or extend.",
        }

    if key == "new_hire_records":
        data = fetch_form_records_paginated(base, token, "employee")
        rows = []
        for r in data["rows"]:
            added = str(r.get("AddedTime") or "")
            if added:
                rows.append(r)
        return {
            "source": "zoho_people",
            "collector_key": key,
            "note": "Filtered rows with AddedTime set; tighten with Dateofjoining if available.",
            "rows": rows,
            "total_rows": len(rows),
        }

    if key == "exit_employees":
        data = fetch_form_records_paginated(base, token, "employee")
        rows = [r for r in data["rows"] if _is_terminated_status(_status_value(r))]
        return {
            "source": "zoho_people",
            "collector_key": key,
            "rows": rows,
            "total_rows": len(rows),
        }

    if key == "exit_clearance":
        try:
            data = fetch_form_records_paginated(base, token, "exit")
            return {"source": "zoho_people", "collector_key": key, "form": "exit", **data}
        except Exception:
            return {
                "source": "zoho_people",
                "collector_key": key,
                "error_hint": "Form link name may not be 'exit'; set custom form name in future config.",
                "rows": [],
                "total_rows": 0,
            }

    raise ValueError(f"Unknown collector_key: {key}")
