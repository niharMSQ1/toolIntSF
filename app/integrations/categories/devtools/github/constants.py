"""GitHub REST API — https://docs.github.com/en/rest"""

from __future__ import annotations

# REST API base (documented).
GITHUB_API_BASE = "https://api.github.com"

# OAuth Apps — https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps
GITHUB_OAUTH_AUTHORIZE = "https://github.com/login/oauth/authorize"
GITHUB_OAUTH_ACCESS_TOKEN = "https://github.com/login/oauth/access_token"

# API versioning header — https://docs.github.com/en/rest/about-the-rest-api/api-versions
GITHUB_API_VERSION = "2022-11-28"

# Default OAuth scopes for repo + Actions read (adjust in GitHub OAuth app settings).
DEFAULT_GITHUB_OAUTH_SCOPES = "repo read:user read:org workflow"
