"""
Zoho People (HRMS) integration.

- ``oauth`` / ``credentials`` / ``regions``: OAuth against Zoho Accounts + People base URLs.
- ``collector``: evidence pull strategies per evidence_masters.code.
- ``seed`` / ``seed_service``: inventory rows for evidence_masters.
- ``token_refresh``: refresh_token → new access_token persisted on tool_integrations.
- ``collection_runner``: orchestrates collect → evidence → evidence_collections.
- ``routers``: FastAPI routes (also mounted via ``app.integrations.api``).

Provider metadata is registered in ``app.integrations.core.registry`` (see ``registry.py``).
"""

PROVIDER_KEY = "zoho_people"

__all__ = ["PROVIDER_KEY"]
