from typing import Optional

# Combined OAuth scope used when building the auth URL.
# - ZohoPeople.forms.READ         → required for Forms (employee directory) APIs
# - ZOHOPEOPLE.orgstructure.READ  → required for OrgStructure (entities/departments) APIs
ZOHO_DEFAULT_SCOPE = "ZohoPeople.forms.READ,ZOHOPEOPLE.orgstructure.READ"

# API endpoints for Zoho People. All use Forms API pattern:
# https://people.zoho.{region}/people/api/forms/{formLinkName}/getRecords
EMPLOYEE_DIRECTORY_ENDPOINT = "/people/api/forms/employee/getRecords"
DEPARTMENT_STRUCTURE_ENDPOINT = "/people/api/forms/department/getRecords"

# Optional: Attendance Records. If set, fetch_attendance() will be called.
# Zoho People User Report: https://people.zoho.{region}/people/api/attendance/getUserReport
ATTENDANCE_ENDPOINT = "/people/api/attendance/getUserReport"  # optional; pass date params

# Optional: Training Completion Records. Form link name for training/completion form.
# If None, training evidence is skipped.
TRAINING_FORM_LINK_NAME: Optional[str] = None

