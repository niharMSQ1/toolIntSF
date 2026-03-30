"""Azure DevOps REST API — https://learn.microsoft.com/en-us/rest/api/azure/devops/"""

from __future__ import annotations

# Cloud default; Azure DevOps Server uses https://{server}/{collection} style base URL.
DEFAULT_AZURE_DEVOPS_BASE = "https://dev.azure.com"

# Pin api-version per https://learn.microsoft.com/en-us/azure/devops/integrate/how-to/call-rest-api
DEFAULT_API_VERSION = "7.1"
