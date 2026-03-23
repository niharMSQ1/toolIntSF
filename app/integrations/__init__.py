"""
GRC tool integrations package.

Structure
---------
- ``core``: shared constants, protocols, provider registry, generic DB persistence.
- ``categories``: product areas (``hrms``, ``idp``, ``devtools``, ``itsm``).
- ``categories.hrms.zoho_people``: Zoho People OAuth, collectors, and HTTP routes.

Use ``app.integrations.api.mount_integration_routes`` in FastAPI ``main``.
"""

from app.integrations.api import mount_integration_routes

__all__ = ["mount_integration_routes"]
