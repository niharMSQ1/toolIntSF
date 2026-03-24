from __future__ import annotations

import os
import re
from datetime import date, datetime, timedelta
from typing import Any

import httpx

from app.integrations.categories.hrms.zoho_people.credentials import resolve_access_token, resolve_region
from app.integrations.categories.hrms.zoho_people.regions import people_base_url
from app.integrations.categories.hrms.zoho_people.seed import CODE_TO_COLLECTOR

# Collector keys that only need the employee form — safe to share one prefetch per run.
EMPLOYEE_COLLECTOR_KEYS: frozenset[str] = frozenset(
    {
        "employee_master",
        "active_employees",
        "terminated_employees",
        "reporting_hierarchy",
        "employee_email_list",
        "new_hire_records",
        "exit_employees",
    }
)


def needs_employee_prefetch(masters: list[dict[str, Any]]) -> bool:
    """True if any selected evidence master will read the employee form."""
    for m in masters:
        key = CODE_TO_COLLECTOR.get(m.get("code") or "")
        if key in EMPLOYEE_COLLECTOR_KEYS:
            return True
    return False


def _people_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Zoho-oauthtoken {access_token}"}


def _log_http_line(r: httpx.Response, url: str) -> None:
    if os.environ.get("ZOHO_DEBUG_HTTP"):
        print(r.status_code, url, r.text)
    else:
        print(r.status_code, url, f"len={len(r.content)}")


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


def validate_zoho_json_payload(data: Any) -> None:
    """Raise if Zoho returned a business error in JSON (including HTTP 200 bodies)."""
    if not isinstance(data, dict):
        return
    err = data.get("error")
    if err:
        msg = err if isinstance(err, str) else str(err)
        raise ValueError(f"Zoho People API error: {msg}")
    resp = data.get("response")
    if isinstance(resp, dict):
        st = resp.get("status")
        if st is not None and st != 0:
            msg = resp.get("message")
            errs = resp.get("errors")
            if isinstance(errs, dict):
                msg = msg or str(errs.get("message") or errs)
            elif isinstance(errs, list) and errs:
                first = errs[0]
                if isinstance(first, dict):
                    msg = msg or str(first.get("message") or first)
                else:
                    msg = msg or str(errs)
            raise ValueError(f"Zoho People API error: {msg or resp}")


def _is_courses_subscription_skip(data: dict[str, Any]) -> bool:
    """LMS not on plan (e.g. code 7411) — collector should skip, not fail."""
    resp = data.get("response")
    if not isinstance(resp, dict):
        return False
    errs = resp.get("errors")
    if isinstance(errs, dict) and errs.get("code") == 7411:
        return True
    if isinstance(errs, dict) and "not included in your subscription" in str(errs.get("message", "")).lower():
        return True
    return False


def _get_json(client: httpx.Client, url: str, headers: dict[str, str], params: dict[str, Any] | None = None) -> Any:
    r = client.get(url, headers=headers, params=params, timeout=120.0)
    _log_http_line(r, url)
    r.raise_for_status()
    data = r.json()
    validate_zoho_json_payload(data)
    return data


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


def to_zoho_date(d: date) -> str:
    """Zoho often expects dd-MMM-yyyy (e.g. 11-Mar-2026)."""
    return d.strftime("%d-%b-%Y")


def zoho_date_range(date_from: str | None, date_to: str | None) -> tuple[str, str]:
    """Date strings for Zoho query params (not ISO)."""
    if date_to:
        end = datetime.strptime(date_to, "%Y-%m-%d").date()
    else:
        end = date.today()
    if date_from:
        start = datetime.strptime(date_from, "%Y-%m-%d").date()
    else:
        start = end - timedelta(days=90)
    return to_zoho_date(start), to_zoho_date(end)


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


def _exit_form_link(cfg: dict[str, Any]) -> str:
    v = cfg.get("exit_form_link")
    if v and str(v).strip():
        return str(v).strip()
    return "exit"


def _resolve_timesheet_user(cfg: dict[str, Any], employee_rows: list[dict[str, Any]] | None) -> str | None:
    u = cfg.get("timesheet_user_id") or cfg.get("timesheet_erecno")
    if u is not None and str(u).strip():
        return str(u).strip()
    if employee_rows:
        r0 = employee_rows[0]
        zid = r0.get("Zoho_ID")
        if zid is not None and str(zid).strip():
            return str(zid)
    return None


def _get_employee_form_data(
    employee_cache: dict[str, Any] | None,
    base: str,
    token: str,
) -> dict[str, Any]:
    if employee_cache is not None:
        return {
            "raw_last_page": employee_cache.get("raw_last_page", {}),
            "rows": list(employee_cache["rows"]),
            "total_rows": employee_cache.get("total_rows", len(employee_cache["rows"])),
        }
    return fetch_form_records_paginated(base, token, "employee")


def collect_for_master(
    master: dict[str, Any],
    cfg: dict[str, Any],
    *,
    date_from: str | None,
    date_to: str | None,
    employee_cache: dict[str, Any] | None = None,
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
    z0, z1 = zoho_date_range(date_from, date_to)

    if key == "employee_master":
        data = _get_employee_form_data(employee_cache, base, token)
        return {"source": "zoho_people", "collector_key": key, "form": "employee", **data}

    if key == "active_employees":
        data = _get_employee_form_data(employee_cache, base, token)
        rows = [r for r in data["rows"] if _is_active_status(_status_value(r))]
        return {
            "source": "zoho_people",
            "collector_key": key,
            "form": "employee",
            "total_rows": len(rows),
            "rows": rows,
        }

    if key == "terminated_employees":
        data = _get_employee_form_data(employee_cache, base, token)
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
        data = _get_employee_form_data(employee_cache, base, token)
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
        data = _get_employee_form_data(employee_cache, base, token)
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
                    "sdate": z0,
                    "edate": z1,
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
        rows_for_user = employee_cache["rows"] if employee_cache else None
        user_param = _resolve_timesheet_user(cfg, rows_for_user)
        if not user_param:
            raise ValueError(
                "Timesheet API requires a user identifier: set timesheet_user_id or timesheet_erecno in "
                "tool_integrations.configuration_data, or prefetch employees so Zoho_ID can be used."
            )
        headers = _people_headers(token)
        url = f"{base.rstrip('/')}/people/api/timetracker/gettimesheet"
        with httpx.Client() as client:
            params = {
                "fromDate": z0,
                "toDate": z1,
                "sIndex": 0,
                "limit": 200,
                "user": user_param,
            }
            raw = _get_json(client, url, headers, params)
        note = None
        if not (cfg.get("timesheet_user_id") or cfg.get("timesheet_erecno")):
            note = "timesheet user from first employee row (Zoho_ID); set timesheet_user_id to pin a specific user."
        out: dict[str, Any] = {
            "source": "zoho_people",
            "collector_key": key,
            "date_from": d0,
            "date_to": d1,
            "payload": raw,
        }
        if note:
            out["note"] = note
        return out

    if key == "leave_records":
        headers = _people_headers(token)
        url = f"{base.rstrip('/')}/api/v2/leavetracker/leaves/records"
        rows: list[dict[str, Any]] = []
        start_index = 0
        with httpx.Client() as client:
            while True:
                params = {
                    "from": z0,
                    "to": z1,
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
            r = client.get(url, headers=headers, params={"startIndex": 0}, timeout=120.0)
            _log_http_line(r, url)
            r.raise_for_status()
            raw = r.json()
        if isinstance(raw, dict) and _is_courses_subscription_skip(raw):
            return {
                "source": "zoho_people",
                "collector_key": key,
                "skipped": True,
                "reason": "LMS/courses module not included in this Zoho subscription (or similar).",
                "payload": raw,
            }
        validate_zoho_json_payload(raw)
        return {"source": "zoho_people", "collector_key": key, "payload": raw}

    if key == "policy_acknowledgement":
        return {
            "source": "zoho_people",
            "collector_key": key,
            "skipped": True,
            "reason": "Requires policy file_id list from Zoho Files; configure file_ids in integration or extend.",
        }

    if key == "new_hire_records":
        data = _get_employee_form_data(employee_cache, base, token)
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
        data = _get_employee_form_data(employee_cache, base, token)
        rows = [r for r in data["rows"] if _is_terminated_status(_status_value(r))]
        return {
            "source": "zoho_people",
            "collector_key": key,
            "rows": rows,
            "total_rows": len(rows),
        }

    if key == "exit_clearance":
        form_link = _exit_form_link(cfg)
        try:
            data = fetch_form_records_paginated(base, token, form_link)
            return {"source": "zoho_people", "collector_key": key, "form": form_link, **data}
        except Exception:
            return {
                "source": "zoho_people",
                "collector_key": key,
                "error_hint": f"Form link name may be wrong; set exit_form_link in configuration_data (tried {form_link!r}).",
                "rows": [],
                "total_rows": 0,
            }

    raise ValueError(f"Unknown collector_key: {key}")


_ZOHO_STORE_DROP_KEYS: frozenset[str] = frozenset(
    {
        "source",
        "collector_key",
        "form",
        "note",
        "error_hint",
        "skipped",
        "reason",
        "date_from",
        "date_to",
        "total_rows",
    }
)


def zoho_evidence_for_tool_storage(content: dict[str, Any]) -> Any:
    """Remove integration metadata; persist only Zoho-shaped response data."""
    out = {k: v for k, v in content.items() if k not in _ZOHO_STORE_DROP_KEYS}
    if len(out) == 1 and "payload" in out:
        return out["payload"]
    return out
