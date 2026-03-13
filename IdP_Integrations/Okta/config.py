# Okta Admin API (GRC evidence collection)
# Base URL: https://{org_domain}/api/v1 (e.g. https://dev-12345.okta.com or https://company.okta.com)
# Authentication: API Token in header Authorization: SSWS {api_token}

# API paths (relative to base /api/v1)
OKTA_USERS_PATH = "/users"
OKTA_USER_FACTORS_PATH = "/users/{userId}/factors"
OKTA_GROUPS_PATH = "/groups"
OKTA_GROUP_USERS_PATH = "/groups/{groupId}/users"
OKTA_APPS_PATH = "/apps"
OKTA_APP_USERS_PATH = "/apps/{appId}/users"
OKTA_APP_GROUPS_PATH = "/apps/{appId}/groups"
OKTA_LOGS_PATH = "/logs"
OKTA_POLICIES_PATH = "/policies"
OKTA_USER_ROLES_PATH = "/users/{userId}/roles"

# Default pagination (Okta max is 10000 per request; use 200 for safer memory)
OKTA_DEFAULT_LIMIT = 200
