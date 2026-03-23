"""HTTP routers for Zoho People (HRMS)."""

from app.integrations.categories.hrms.zoho_people.routers import configure, evidence, oauth

__all__ = ["configure", "evidence", "oauth"]
