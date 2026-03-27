"""Integration domain taxonomy (category = product area, e.g. HRMS, IDP)."""

from __future__ import annotations

from enum import Enum


class IntegrationCategory(str, Enum):
    """Top-level integration categories for a GRC platform."""

    HRMS = "hrms"
    IDP = "idp"
    DEVTOOLS = "devtools"
    ITSM = "itsm"
    CLOUD_INFRA = "cloud_infra"
