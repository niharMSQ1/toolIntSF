"""Microsoft Entra / Microsoft Graph defaults."""

from __future__ import annotations

# Delegated Graph scopes: admin consent typically required for User.Read.All / Group.Read.All.
DEFAULT_GRAPH_SCOPES = (
    "offline_access "
    "openid profile "
    "https://graph.microsoft.com/User.Read.All "
    "https://graph.microsoft.com/Group.Read.All"
)

# GCC High Graph host uses graph.microsoft.us — scope resource URLs still use graph.microsoft.com in many tenants;
# Microsoft documents using the same scope strings with the .us token/resource. Keep identical scopes as Graph accepts.
DEFAULT_GRAPH_SCOPES_GCC_HIGH = DEFAULT_GRAPH_SCOPES

# Safety cap for @odata.nextLink pagination.
MAX_GRAPH_PAGES = 200
