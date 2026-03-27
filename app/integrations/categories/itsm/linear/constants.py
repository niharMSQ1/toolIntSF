"""Linear provider identifiers and API constants."""

LINEAR_SOURCE = "linear"

LINEAR_GRAPHQL_URL = "https://api.linear.app/graphql"
LINEAR_OAUTH_AUTHORIZE_URL = "https://linear.app/oauth/authorize"
LINEAR_OAUTH_TOKEN_URL = "https://api.linear.app/oauth/token"

# Read + write scope so the integration can fetch teams/issues and create/update issues.
DEFAULT_LINEAR_SCOPES = "read,write,issues:create"
