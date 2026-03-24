"""HTTP routers for Microsoft Entra (commercial + GCC High)."""

from app.integrations.categories.idp.microsoft_entra.routers import configure, evidence, oauth

__all__ = ["configure", "evidence", "oauth"]
