"""CrowdStrike Falcon API — paths align with OpenAPI (see Developer Center)."""

CROWDSTRIKE_FALCON_SOURCE = "crowdstrike_falcon"

# Regional API bases (SaaS). On-prem: use your tenant API host from Falcon installer docs.
DEFAULT_API_BASE_URL = "https://api.crowdstrike.com"

# OAuth2 — FalconPy: oauth2AccessToken → POST /oauth2/token (application/x-www-form-urlencoded)
OAUTH2_TOKEN_PATH = "/oauth2/token"

# Hosts — QueryDevices (GET)
DEVICES_QUERY_PATH = "/devices/queries/devices/v1"

# Detections — QueryDetects (GET)
DETECTS_QUERY_PATH = "/detects/queries/detects/v1"

# Spotlight — combinedQueryVulnerabilities (GET); ``filter`` is required (FQL).
SPOTLIGHT_COMBINED_VULNS_PATH = "/spotlight/combined/vulnerabilities/v1"
