"""Log and optionally print employee master summary during Zoho People integration runs."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_PREVIEW_ENV = "ZOHO_PRINT_EMPLOYEE_MASTER"


def emit_employee_master_preview(
    employee_payload: dict[str, Any] | None,
    *,
    emit_print: bool | None = None,
) -> None:
    """
    After prefetching the employee form, emit count + a full slim field list for every row.

    Set env ``ZOHO_PRINT_EMPLOYEE_MASTER=0`` to disable ``print()`` (logging still runs).
    """
    import os

    if emit_print is None:
        emit_print = os.environ.get(_PREVIEW_ENV, "1").strip() not in ("0", "false", "no")

    rows = (employee_payload or {}).get("rows") or []
    total = int((employee_payload or {}).get("total_rows", len(rows)))
    headline = (
        "[zoho_people | HR/Employee Management] Employee master: "
        f"{total} record(s) from GET .../api/forms/employee/getRecords"
    )
    logger.info(headline)
    if emit_print:
        print(headline)

    if not rows:
        return

    sample: list[dict[str, Any]] = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        sample.append(
            {
                "EmployeeID": r.get("EmployeeID"),
                "Zoho_ID": r.get("Zoho_ID"),
                "FirstName": r.get("FirstName"),
                "LastName": r.get("LastName"),
                "EmailID": r.get("EmailID") or r.get("Email"),
            }
        )
    logger.info("Employee master sample (all %s rows): %s", len(sample), sample)
    if emit_print:
        print(f"Employee master sample (all {len(sample)} rows):", sample)
