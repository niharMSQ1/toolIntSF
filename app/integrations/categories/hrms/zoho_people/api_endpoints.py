"""
Zoho People HTTP paths used by this integration (HR / Employee Management).

Official documentation (read before changing collectors):

- Overview: https://www.zoho.com/people/api/
- **Forms** (employee, department, custom exit form, etc.): https://www.zoho.com/people/api/forms/
  - List/get records: ``GET {people_base}/api/forms/{{formLinkName}}/getRecords`` with ``sIndex``, ``limit``.
- **Attendance**: https://www.zoho.com/people/api/attendance-api/
  - User report: ``GET {people_base}/people/api/attendance/getUserReport`` — query ``sdate``, ``edate``, ``startIndex`` (dd-MMM-yyyy dates).
- **Time tracker**: https://www.zoho.com/people/api/timetracker/
  - Timesheet: ``GET {people_base}/people/api/timetracker/gettimesheet`` — ``fromDate``, ``toDate``, ``user``, ``sIndex``, ``limit``.
- **Leave**: https://www.zoho.com/people/api/leavetracker/
  - Leave records (v2): ``GET {people_base}/api/v2/leavetracker/leaves/records`` — ``from``, ``to``, ``startIndex``, ``limit``.
- **LMS / courses** (optional module): ``GET {people_base}/api/v1/courses`` — may return subscription errors if LMS not purchased.

``people_base`` is region-specific (e.g. ``https://people.zoho.in`` for India); see ``regions.people_base_url``.
"""

from __future__ import annotations


DOCS_HOME = "https://www.zoho.com/people/api/"
FORMS_DOCS = "https://www.zoho.com/people/api/forms/"

# Default form link names (org can rename; employee/department are standard).
FORM_EMPLOYEE = "employee"
FORM_DEPARTMENT = "department"


def path_forms_get_records(form_link: str) -> str:
    """Relative path: GET /api/forms/{formLink}/getRecords"""
    return f"/api/forms/{form_link}/getRecords"


PATH_ATTENDANCE_USER_REPORT = "/people/api/attendance/getUserReport"
PATH_TIMETRACKER_GET_TIMESHEET = "/people/api/timetracker/gettimesheet"
PATH_LEAVETRACKER_RECORDS_V2 = "/api/v2/leavetracker/leaves/records"
PATH_COURSES_V1 = "/api/v1/courses"
# Policy acknowledgements (files module) — optional future use
PATH_FILES_ACK_V3 = "/people/api/v3/files/acknowledgement/details"
