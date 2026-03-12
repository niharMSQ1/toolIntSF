from typing import Any, Dict, List, Optional

import httpx

from .config import (
    ATLASSIAN_ACCESSIBLE_RESOURCES_URL,
    ATLASSIAN_AUTHORIZE_URL,
    ATLASSIAN_TOKEN_URL,
    REQUEST_PATH,
    SERVICEDESK_PATH,
)


class JiraServicedeskClient:
    """
    Client for Atlassian OAuth 2.0 (3LO) and Jira Service Management REST API.
    - Build auth URL, exchange code for tokens, get accessible resources (cloud ID).
    - Fetch service desks and customer requests using cloud ID + access token.
    """

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri.rstrip("/")

    # --------------------------------------------------------------------- #
    # OAuth
    # --------------------------------------------------------------------- #

    def build_authorization_url(self, scope: str, state: str) -> str:
        """Build Atlassian authorization URL for redirect."""
        params = {
            "client_id": self.client_id,
            "scope": scope,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "state": state,
            "prompt": "consent",
        }
        query = "&".join(f"{k}={httpx.QueryParams({k: v})[k]}" for k, v in params.items())
        return f"{ATLASSIAN_AUTHORIZE_URL}?{query}"

    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access_token and refresh_token."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                ATLASSIAN_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.redirect_uri,
                    "code": code,
                },
                headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            return resp.json()

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh_token."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                ATLASSIAN_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                },
                headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            return resp.json()

    async def get_accessible_resources(self, access_token: str) -> List[Dict[str, Any]]:
        """
        Get list of sites (cloud IDs) the user has access to.
        Each item has 'id' (cloud_id), 'url', 'name', etc.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                ATLASSIAN_ACCESSIBLE_RESOURCES_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
            resp.raise_for_status()
            return resp.json()

    # --------------------------------------------------------------------- #
    # JSM API (base URL uses cloud_id)
    # --------------------------------------------------------------------- #

    def _jsm_base_url(self, cloud_id: str) -> str:
        return f"https://api.atlassian.com/ex/jira/{cloud_id}"

    async def _get(
        self,
        access_token: str,
        cloud_id: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self._jsm_base_url(cloud_id)}{path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
                params=params,
            )
            resp.raise_for_status()
            return resp.json()

    async def fetch_servicedesks(self, cloud_id: str, access_token: str) -> Dict[str, Any]:
        """Fetch all service desks (paginated; default start/limit)."""
        return await self._get(
            access_token,
            cloud_id,
            SERVICEDESK_PATH,
            params={"start": 0, "limit": 50},
        )

    async def fetch_customer_requests(self, cloud_id: str, access_token: str) -> Dict[str, Any]:
        """Fetch customer requests for the current user (paginated)."""
        return await self._get(
            access_token,
            cloud_id,
            REQUEST_PATH,
            params={"start": 0, "limit": 50},
        )
