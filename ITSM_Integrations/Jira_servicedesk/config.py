# Atlassian OAuth 2.0 (3LO)
ATLASSIAN_AUTHORIZE_URL = "https://auth.atlassian.com/authorize"
ATLASSIAN_TOKEN_URL = "https://auth.atlassian.com/oauth/token"

# After token exchange: get cloud ID for the user's site(s)
ATLASSIAN_ACCESSIBLE_RESOURCES_URL = "https://api.atlassian.com/oauth/token/accessible-resources"

# Scopes for read-only Jira Service Management (servicedesks, requests)
JIRA_DEFAULT_SCOPE = "read:jira-work read:servicedesk-request read:servicedesk:jira-service-management"

# JSM REST API paths (base is https://api.atlassian.com/ex/jira/{cloudId}/rest/servicedeskapi)
SERVICEDESK_PATH = "/rest/servicedeskapi/servicedesk"
REQUEST_PATH = "/rest/servicedeskapi/request"
