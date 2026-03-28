"""Snyk integration source tag for evidence_masters."""

SNYK_SOURCE = "snyk"

# REST API version (see https://docs.snyk.io/snyk-api/rest-api/getting-started-with-the-rest-api)
SNYK_REST_API_VERSION = "2024-10-15"

# Safety cap per collect (pagination stops here)
MAX_ISSUES_PER_SCOPE = 8000
MAX_PROJECTS_PER_ORG = 2000
