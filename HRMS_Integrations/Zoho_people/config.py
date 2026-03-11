# Combined OAuth scope used when building the auth URL.
# - ZohoPeople.forms.READ         → required for Forms (employee directory) APIs
# - ZOHOPEOPLE.orgstructure.READ  → required for OrgStructure (entities/departments) APIs
ZOHO_DEFAULT_SCOPE = "ZohoPeople.forms.READ,ZOHOPEOPLE.orgstructure.READ"

# API endpoints for Zoho People. Adjust if your app uses different versions/paths.
# Employee Directory (Forms API - employees list)
# Docs example: https://people.zoho.com/api/forms/employee/getRecords
EMPLOYEE_DIRECTORY_ENDPOINT = "/api/forms/employee/getRecords"

# Department (Forms API - department getRecords)
# GET https://people.zoho.com/people/api/forms/department/getRecords?sIndex=1&limit=200
DEPARTMENT_STRUCTURE_ENDPOINT = "/people/api/forms/department/getRecords"

