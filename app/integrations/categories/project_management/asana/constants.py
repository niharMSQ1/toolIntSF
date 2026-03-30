"""Asana REST API constants (official docs)."""

from __future__ import annotations

# Base URL and version — https://developers.asana.com/reference/rest-api-reference
ASANA_API_BASE = "https://app.asana.com/api/1.0"

# OAuth 2.0 — https://developers.asana.com/docs/oauth
ASANA_OAUTH_AUTHORIZE = "https://app.asana.com/-/oauth_authorize"
ASANA_OAUTH_TOKEN = "https://app.asana.com/-/oauth_token"

# Default OAuth scopes (read-focused; register matching scopes in the Developer Console).
DEFAULT_ASANA_SCOPES = "tasks:read projects:read users:read workspaces:read stories:read"
