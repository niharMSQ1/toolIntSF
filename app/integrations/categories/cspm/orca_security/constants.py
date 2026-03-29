"""Orca Security API — paths align with Cortex XSOAR Orca integration (public source)."""

ORCA_SECURITY_SOURCE = "orca_security"

# Default host (Cortex XSOAR Orca README: api_host default api.orcasecurity.io; base URL https://{host}/api).
DEFAULT_API_HOST = "api.orcasecurity.io"

# Demisto Orca.py — alert query automation path (POST JSON).
QUERY_ALERTS_PATH = "/automations/query/alerts"
