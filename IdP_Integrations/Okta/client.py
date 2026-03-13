"""
Okta Admin API client for GRC evidence collection.
Uses API token (SSWS) auth. Implements MVP endpoints: users, factors, groups,
group users, apps, app users, app groups, logs, policies, user roles.
"""
from typing import Any, Dict, List, Optional

import httpx

from .config import (
    OKTA_APPS_PATH,
    OKTA_APP_GROUPS_PATH,
    OKTA_APP_USERS_PATH,
    OKTA_DEFAULT_LIMIT,
    OKTA_GROUPS_PATH,
    OKTA_GROUP_USERS_PATH,
    OKTA_LOGS_PATH,
    OKTA_POLICIES_PATH,
    OKTA_USER_FACTORS_PATH,
    OKTA_USER_ROLES_PATH,
    OKTA_USERS_PATH,
)


def _normalize_domain(org_domain: str) -> str:
    """Ensure domain has no scheme and no trailing slash."""
    d = (org_domain or "").strip().lower()
    for prefix in ("https://", "http://"):
        if d.startswith(prefix):
            d = d[len(prefix) :]
    return d.rstrip("/").split("/")[0] or ""


class OktaClient:
    """
    Client for Okta Admin API (token-based).
    Base URL: https://{org_domain}/api/v1
    """

    def __init__(self, org_domain: str, api_token: str) -> None:
        self.org_domain = _normalize_domain(org_domain)
        if not self.org_domain:
            raise ValueError("org_domain is required")
        self.api_token = (api_token or "").strip()
        if not self.api_token:
            raise ValueError("api_token is required")
        self.base_url = f"https://{self.org_domain}/api/v1"

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"SSWS {self.api_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(url, headers=self._headers(), params=params)
            resp.raise_for_status()
            return resp.json()

    async def _get_list(
        self,
        path: str,
        limit: int = OKTA_DEFAULT_LIMIT,
        since: Optional[str] = None,
    ) -> List[Any]:
        """Fetch a list endpoint with pagination via Link header."""
        url = f"{self.base_url}{path}"
        params: Dict[str, Any] = {"limit": limit}
        if since:
            params["since"] = since
        collected: List[Any] = []
        async with httpx.AsyncClient(timeout=60.0) as client:
            while url:
                resp = await client.get(url, headers=self._headers(), params=params)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, list):
                    collected.extend(data)
                else:
                    collected.append(data)
                # Next page: Okta returns Link header with rel="next"
                link = resp.headers.get("link")
                url = ""
                params = {}
                if link:
                    for part in link.split(","):
                        if 'rel="next"' in part:
                            u = part.split(";", 1)[0].strip(" <>")
                            if u.startswith("http"):
                                url = u
                            break
        return collected

    # -------------------------------------------------------------------------
    # MVP endpoints
    # -------------------------------------------------------------------------

    async def list_users(self, limit: int = OKTA_DEFAULT_LIMIT) -> List[Dict[str, Any]]:
        """GET /api/v1/users"""
        return await self._get_list(OKTA_USERS_PATH, limit=limit)

    async def list_user_factors(self, user_id: str) -> List[Dict[str, Any]]:
        """GET /api/v1/users/{userId}/factors"""
        path = OKTA_USER_FACTORS_PATH.format(userId=user_id)
        data = await self._get(path)
        return data if isinstance(data, list) else [data]

    async def list_groups(self, limit: int = OKTA_DEFAULT_LIMIT) -> List[Dict[str, Any]]:
        """GET /api/v1/groups"""
        return await self._get_list(OKTA_GROUPS_PATH, limit=limit)

    async def list_group_users(
        self, group_id: str, limit: int = OKTA_DEFAULT_LIMIT
    ) -> List[Dict[str, Any]]:
        """GET /api/v1/groups/{groupId}/users"""
        path = OKTA_GROUP_USERS_PATH.format(groupId=group_id)
        return await self._get_list(path, limit=limit)

    async def list_apps(self, limit: int = OKTA_DEFAULT_LIMIT) -> List[Dict[str, Any]]:
        """GET /api/v1/apps"""
        return await self._get_list(OKTA_APPS_PATH, limit=limit)

    async def list_app_users(
        self, app_id: str, limit: int = OKTA_DEFAULT_LIMIT
    ) -> List[Dict[str, Any]]:
        """GET /api/v1/apps/{appId}/users"""
        path = OKTA_APP_USERS_PATH.format(appId=app_id)
        return await self._get_list(path, limit=limit)

    async def list_app_groups(
        self, app_id: str, limit: int = OKTA_DEFAULT_LIMIT
    ) -> List[Dict[str, Any]]:
        """GET /api/v1/apps/{appId}/groups"""
        path = OKTA_APP_GROUPS_PATH.format(appId=app_id)
        return await self._get_list(path, limit=limit)

    async def list_logs(
        self, limit: int = 200, since: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """GET /api/v1/logs (supports since= for incremental)"""
        path = OKTA_LOGS_PATH
        return await self._get_list(path, limit=limit, since=since)

    async def list_policies(
        self, limit: int = OKTA_DEFAULT_LIMIT
    ) -> List[Dict[str, Any]]:
        """GET /api/v1/policies"""
        return await self._get_list(OKTA_POLICIES_PATH, limit=limit)

    async def list_user_roles(self, user_id: str) -> List[Dict[str, Any]]:
        """GET /api/v1/users/{userId}/roles"""
        path = OKTA_USER_ROLES_PATH.format(userId=user_id)
        data = await self._get(path)
        return data if isinstance(data, list) else [data]
