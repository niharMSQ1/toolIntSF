"""Microsoft Defender for Endpoint REST API — constants."""

DEFENDER_FOR_ENDPOINT_SOURCE = "defender_for_endpoint"

# Default global API host (regional hosts: us.api.security.microsoft.com, eu.api.security.microsoft.com, …)
DEFAULT_API_BASE_URL = "https://api.security.microsoft.com"

# Token audience for Defender APIs (Hello World / app registration docs).
TOKEN_RESOURCE = "https://api.securitycenter.microsoft.com/"

MACHINES_PATH = "/api/machines"
ALERTS_PATH = "/api/alerts"
VULNS_MACHINES_PATH = "/api/vulnerabilities/machinesVulnerabilities"
