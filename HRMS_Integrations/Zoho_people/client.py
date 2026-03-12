from typing import Any, Dict, Optional

import httpx

from .config import (
    ATTENDANCE_ENDPOINT,
    DEPARTMENT_STRUCTURE_ENDPOINT,
    EMPLOYEE_DIRECTORY_ENDPOINT,
)


class ZohoPeopleClient:
    """
    Minimal Zoho People client focused on:
    - OAuth token exchange (auth_code -> access/refresh)
    - Fetching Employee Directory
    - Fetching Department Structure
    """

    def __init__(self, region: str, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self.region = region
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri.rstrip("/")

        # Region decides base domain (e.g. .com, .in, .eu)
        self.base_auth_url = f"https://accounts.zoho.{self.region}"
        self.base_people_url = f"https://people.zoho.{self.region}"

    # --------------------------------------------------------------------- #
    # OAuth URLs and token exchange
    # --------------------------------------------------------------------- #

    def build_authorization_url(self, scope: str, state: str) -> str:
        """
        Build Zoho authorization URL for redirect.
        Scope is controlled by the tool configuration; state can be org/user context.
        """
        params = {
            "scope": scope,
            "client_id": self.client_id,
            "response_type": "code",
            "access_type": "offline",
            "redirect_uri": self.redirect_uri,
            "prompt": "consent",
            "state": state,
        }
        query = "&".join(f"{k}={httpx.QueryParams({k: v})[k]}" for k, v in params.items())
        return f"{self.base_auth_url}/oauth/v2/auth?{query}"

    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access + refresh tokens.
        """
        url = f"{self.base_auth_url}/oauth/v2/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, data=data)
            resp.raise_for_status()
            payload = resp.json()

        # Typical payload includes: access_token, refresh_token, expires_in, api_domain, token_type
        return payload

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh_token.
        """
        url = f"{self.base_auth_url}/oauth/v2/token"
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, data=data)
            resp.raise_for_status()
            payload = resp.json()

        return payload

    # --------------------------------------------------------------------- #
    # Evidence collection APIs
    # --------------------------------------------------------------------- #

    async def _get(self, access_token: str, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
        url = f"{self.base_people_url}{path}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            return resp.json()

    async def fetch_employee_directory(self, access_token: str) -> Dict[str, Any]:
        """
        Fetch Employee Directory data.
        Endpoint/params can be tuned as per Zoho People API spec.
        """
        return await self._get(access_token, EMPLOYEE_DIRECTORY_ENDPOINT)

    async def fetch_department_structure(self, access_token: str) -> Dict[str, Any]:
        """
        Fetch Department Structure data (Forms API: department getRecords).
        """
        params = {"sIndex": 1, "limit": 200}
        return await self._get(access_token, DEPARTMENT_STRUCTURE_ENDPOINT, params=params)

    async def fetch_attendance(
        self,
        access_token: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Fetch attendance data (e.g. User Report). Optional; only called when ATTENDANCE_ENDPOINT is used.
        Params may include date range (e.g. fromDate, toDate) per Zoho People API.
        """
        return await self._get(access_token, ATTENDANCE_ENDPOINT, params=params or {})

    async def fetch_form_records(
        self,
        access_token: str,
        form_link_name: str,
        sIndex: int = 1,
        limit: int = 200,
    ) -> Dict[str, Any]:
        """
        Fetch records from any Zoho People form (e.g. training). Path: /people/api/forms/{form_link_name}/getRecords.
        """
        path = f"/people/api/forms/{form_link_name}/getRecords"
        params = {"sIndex": sIndex, "limit": limit}
        return await self._get(access_token, path, params=params)

