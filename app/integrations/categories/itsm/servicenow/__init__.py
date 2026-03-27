"""
ServiceNow ITSM integration.

- ``client``: ServiceNow Table API wrapper with mock fallback.
- ``seed`` / ``seed_service``: schema-driven evidence_masters inventory.
- ``collector``: generic source fetch + schema mapping per evidence code.
- ``collection_runner``: shared G4/G5 persistence flow.
- ``routers``: configure endpoint and explicit collect endpoint.
"""

PROVIDER_KEY = "servicenow"

__all__ = ["PROVIDER_KEY"]
