"""
GRC tool integrations package.

Structure
---------
- ``core``: shared constants, protocols, provider registry, generic DB persistence.
- ``categories``: product areas (``hrms``, ``idp``, ``devtools``, ``itsm``).
- ``categories.hrms.zoho_people``: Zoho People OAuth, collectors, and HTTP routes.
- ``categories.idp.microsoft_entra``: Microsoft Entra (commercial + GCC High) OAuth, Graph collectors, routes.
- ``core.sync_dispatch`` / ``routers.integration_sync``: unified ``POST /api/v1/integrations/sync`` for all providers.

Use ``app.integrations.api.mount_integration_routes`` in FastAPI ``main``.
"""

from app.integrations.api import mount_integration_routes

__all__ = ["mount_integration_routes"]
