"""
Zoho People integration — **HR / Employee Management** evidence (category: HRMS).

Maps to GRC domain **HR / Employee Management** in ``mappings.txt`` (EV-* HR codes on the
tool’s ``domain_id``). Uses Zoho People public APIs documented at
https://www.zoho.com/people/api/ — see ``api_endpoints.py`` for paths used here.

- ``oauth`` / ``credentials`` / ``regions``: OAuth against Zoho Accounts + People base URLs.
- ``collector``: evidence pull strategies per ``evidence_masters.code``.
- ``employee_preview``: logs/prints employee master summary after prefetch when forms API runs.
- ``seed`` / ``seed_service``: inventory rows for ``evidence_masters`` (manual seed; not on configure).
- ``token_refresh``: refresh_token → new access_token persisted on ``tool_integrations``.
- ``collection_runner``: orchestrates collect → evidence → ``evidence_collections``.
- ``routers``: FastAPI routes (also mounted via ``app.integrations.api``).

Provider metadata: ``app.integrations.core.registry`` (``zoho_people``).
"""

PROVIDER_KEY = "zoho_people"

__all__ = ["PROVIDER_KEY"]
