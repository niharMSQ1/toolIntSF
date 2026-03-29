"""Lacework API v2 — paths align with lacework/go-sdk (public source)."""

LACEWORK_SOURCE = "lacework"

# POST https://{account}.lacework.net/api/v2/access/tokens — body keyId + expiryTime; X-LW-UAKS: secret
ACCESS_TOKENS_PATH = "/api/v2/access/tokens"
USER_PROFILE_PATH = "/api/v2/UserProfile"
ORGANIZATION_INFO_PATH = "/api/v2/OrganizationInfo"
ALERTS_PATH = "/api/v2/Alerts"
