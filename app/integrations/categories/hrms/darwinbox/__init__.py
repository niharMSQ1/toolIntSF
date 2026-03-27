"""
Darwinbox-style mock HRMS integration.

- ``client``: mock HRMS API payloads grouped by business source.
- ``seed`` / ``seed_service``: schema-driven evidence_masters inventory.
- ``collector``: generic source fetch + schema mapping per evidence code.
- ``collection_runner``: shared G4/G5 persistence flow.
- ``routers``: configure endpoint and optional explicit collect endpoint.
"""

PROVIDER_KEY = "darwinbox"

__all__ = ["PROVIDER_KEY"]
