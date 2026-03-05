"""
Zoho People API client: OAuth token exchange and REST calls for evidence data.
Uses client_id, client_secret, and refresh_token (obtained once via OAuth authorization code flow).
"""

from typing import Any
from urllib.parse import urlencode

import requests

# Zoho Accounts base URLs by region (for token endpoint)
ACCOUNTS_BASE = {
    "com": "https://accounts.zoho.com",
    "eu": "https://accounts.zoho.eu",
    "in": "https://accounts.zoho.in",
    "au": "https://accounts.zoho.com.au",
}
# Zoho People API base (resource server)
PEOPLE_BASE = {
    "com": "https://people.zoho.com",
    "eu": "https://people.zoho.eu",
    "in": "https://people.zoho.in",
    "au": "https://people.zoho.com.au",
}

SCOPE_FORMS_READ = "ZOHOPEOPLE.forms.READ"
MAX_RECORDS_PER_PAGE = 200


class ZohoPeopleClientError(Exception):
    """Raised when Zoho API or token request fails."""
    pass


def build_authorize_url(
    *,
    client_id: str,
    redirect_uri: str,
    region: str = "com",
    scope: str | None = None,
    state: str | None = None,
) -> str:
    """
    Build Zoho OAuth authorize URL for the Authorization Code flow.
    User should open this URL, consent, and you then receive ?code=...&state=...
    Pass state=integration_id so the callback knows which integration to update.
    """
    region = region if region in ACCOUNTS_BASE else "com"
    base = ACCOUNTS_BASE[region]
    scope = scope or "ZOHOPEOPLE.forms.READ"
    params = {
        "scope": scope,
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "access_type": "offline",
        "prompt": "consent",
    }
    if state:
        params["state"] = state
    return f"{base}/oauth/v2/auth?{urlencode(params)}"


def exchange_auth_code_for_tokens(
    *,
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
    region: str = "com",
) -> dict[str, Any]:
    """
    Exchange authorization code for access_token + refresh_token.
    """
    region = region if region in ACCOUNTS_BASE else "com"
    token_url = f"{ACCOUNTS_BASE[region]}/oauth/v2/token"
    resp = requests.post(
        token_url,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "access_token" not in data:
        err_msg = data.get("error", "") or data.get("error_description", str(data))
        raise ZohoPeopleClientError(f"Zoho token response missing access_token: {err_msg}")
    return data


class ZohoPeopleClient:
    """
    Client for Zoho People API. Requires a refresh_token from a one-time OAuth
    authorization code flow (user consents in browser; you exchange code for access + refresh token).
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        region: str = "com",
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.region = region if region in ACCOUNTS_BASE else "com"
        self._access_token: str | None = None

    def _token_url(self) -> str:
        return f"{ACCOUNTS_BASE[self.region]}/oauth/v2/token"

    def _people_url(self, path: str) -> str:
        base = PEOPLE_BASE[self.region]
        path = path.lstrip("/")
        return f"{base}/people/api/forms/{path}"

    def get_access_token(self) -> str:
        """Exchange refresh_token for a new access_token. Cached for reuse in same session."""
        if self._access_token:
            return self._access_token
        resp = requests.post(
            self._token_url(),
            data={
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if "access_token" not in data:
            raise ZohoPeopleClientError("Zoho token response missing access_token")
        self._access_token = data["access_token"]
        return self._access_token

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Zoho-oauthtoken {self.get_access_token()}"}

    def _get_records(self, form_name: str, s_index: int = 1, limit: int = MAX_RECORDS_PER_PAGE) -> dict[str, Any]:
        url = self._people_url(f"{form_name}/getRecords")
        params = {"sIndex": s_index, "limit": limit}
        r = requests.get(url, params=params, headers=self._headers(), timeout=30)
        r.raise_for_status()
        data = r.json()
        res = data.get("response") or {}
        if res.get("status") != 0 and res.get("status") is not None:
            raise ZohoPeopleClientError(res.get("message", "API error") or str(data))
        return data

    def fetch_employee_records(self) -> list[dict[str, Any]]:
        """
        Fetch all employee form records (paginated). Returns a list of raw record dicts
        suitable for the Zoho normalizer (we map Zoho field names to normalizer expectations).
        """
        out: list[dict[str, Any]] = []
        s_index = 1
        while True:
            data = self._get_records("employee", s_index=s_index, limit=MAX_RECORDS_PER_PAGE)
            result = (data.get("response") or {}).get("result") or []
            if not result:
                break
            for item in result:
                if isinstance(item, dict):
                    for key, rows in item.items():
                        if isinstance(rows, list):
                            for row in rows:
                                if isinstance(row, dict):
                                    out.append(self._normalize_employee_row(row, key))
                else:
                    break
            if len(result) < MAX_RECORDS_PER_PAGE:
                break
            s_index += MAX_RECORDS_PER_PAGE
        return out

    @staticmethod
    def _normalize_employee_row(row: dict[str, Any], zoho_id: str) -> dict[str, Any]:
        """Map Zoho People form fields to names our normalizer expects."""
        first = row.get("FirstName") or row.get("First_Name") or ""
        last = row.get("LastName") or row.get("Last_Name") or ""
        name = (first + " " + last).strip() or row.get("FullName") or row.get("DisplayName")
        return {
            "id": str(row.get("Zoho_ID") or zoho_id),
            "employee_id": row.get("EmployeeID"),
            "EmployeeID": row.get("EmployeeID"),
            "email": row.get("EmailID") or row.get("Email"),
            "EmailID": row.get("EmailID"),
            "name": name,
            "full_name": name,
            "FirstName": first,
            "LastName": last,
            "department_id": row.get("Department.ID") or row.get("DepartmentID"),
            "DepartmentID": row.get("Department.ID") or row.get("DepartmentID"),
            "department_name": row.get("Department") or row.get("DepartmentName"),
            "DepartmentName": row.get("Department") or row.get("DepartmentName"),
            # designation / title
            "designation": row.get("Designation"),
            "Designation": row.get("Designation"),
            "manager_id": row.get("Reporting_To.ID") or row.get("ManagerID"),
            "ManagerID": row.get("Reporting_To.ID") or row.get("ManagerID"),
            "status": row.get("Employeestatus") or row.get("EmployeeStatus") or row.get("Status") or "active",
            "Status": row.get("Employeestatus") or row.get("EmployeeStatus"),
            "hire_date": row.get("Date_of_Join") or row.get("JoiningDate") or row.get("DateOfJoin"),
            "joiningDate": row.get("Date_of_Join") or row.get("JoiningDate"),
            "dateOfJoin": row.get("Date_of_Join") or row.get("JoiningDate"),
            "termination_date": row.get("Relieving_Date") or row.get("Last_Working_Date"),
            "relievingDate": row.get("Relieving_Date") or row.get("Last_Working_Date"),
            "lastWorkingDate": row.get("Relieving_Date") or row.get("Last_Working_Date"),
            "employment_type": row.get("Employment_Type") or row.get("EmploymentType"),
            "EmploymentType": row.get("Employment_Type") or row.get("EmploymentType"),
        }

    def fetch_department_records(self) -> list[dict[str, Any]]:
        """
        Try to fetch department/organization form if it exists. Many Zoho People setups
        use a custom form for departments. Common form link names: 'Department', 'Departments'.
        If the API doesn't have a department form, returns empty list (we can derive from employees).
        """
        out: list[dict[str, Any]] = []
        for form_name in ("Department", "Departments", "department", "departments"):
            try:
                data = self._get_records(form_name, s_index=1, limit=MAX_RECORDS_PER_PAGE)
                result = (data.get("response") or {}).get("result") or []
                for item in result:
                    if isinstance(item, dict):
                        for key, rows in item.items():
                            if isinstance(rows, list):
                                for row in rows:
                                    if isinstance(row, dict):
                                        out.append({
                                            "id": str(row.get("Zoho_ID") or row.get("ID") or key),
                                            "department_id": row.get("ID"),
                                            "name": row.get("Department") or row.get("Name") or row.get("DepartmentName"),
                                            "department_name": row.get("Department") or row.get("Name"),
                                            "parent_id": row.get("Parent_ID") or row.get("ParentDepartmentID") or row.get("ParentDepartment.ID"),
                                            "head_count": row.get("Head_Count") or row.get("HeadCount") or row.get("Employee_Count") or 0,
                                        })
                if out:
                    break
            except (ZohoPeopleClientError, requests.RequestException):
                continue
        return out
