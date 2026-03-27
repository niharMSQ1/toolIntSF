"""
Zoho People HTTP paths used by this integration (HR / Employee Management).

Official documentation (verify paths and parameters before changing collectors):

- Overview: https://www.zoho.com/people/api/
- **Bulk form records** (employee, department, custom forms): https://www.zoho.com/people/api/bulk-records.html
  - ``GET {people_base}/api/forms/{{formLinkName}}/getRecords`` — ``sIndex``, ``limit`` (max 200 per call).
- **Attendance — user report**: https://www.zoho.com/people/api/userreport.html
  - ``GET {people_base}/people/api/attendance/getUserReport`` — ``sdate``, ``edate``; multi-employee: ``startIndex`` (0, 100, …).
- **Time tracker — timesheet**: https://www.zoho.com/people/api/timesheet.html (module index)
  - ``GET {people_base}/people/api/timetracker/gettimesheet`` — ``fromDate``, ``toDate``, ``user``, ``sIndex``, ``limit``.
- **Leave — fetch records v2**: https://www.zoho.com/people/api/get-records-v2.html
  - ``GET {people_base}/api/v2/leavetracker/leaves/records`` — ``from``, ``to``, ``startIndex``, ``limit``.
- **LMS — fetch all courses**: https://www.zoho.com/people/api/LMS/allcourses.html
  - ``GET {people_base}/api/v1/courses`` — optional module; may error if LMS not purchased.

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
