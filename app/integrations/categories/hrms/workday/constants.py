"""Workday REST API and OAuth 2.0 endpoints.

Official references:
- REST API overview: https://developer.workday.com/en-us/docs/rest-api
- OAuth 2.0 token endpoint pattern: ``https://{{hostname}}/ccx/oauth2/{{tenant}}/token``
  (client credentials and refresh flows are documented for API clients for integrations).
"""

from __future__ import annotations

DEFAULT_API_VERSION = "v1"
