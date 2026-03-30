<<<<<<< HEAD
"""HTTP routers for BambooHR (HRMS)."""

from app.integrations.categories.hrms.bamboohr.routers import configure, employees, evidence, oauth

__all__ = ["configure", "employees", "evidence", "oauth"]
=======
from app.integrations.categories.hrms.bamboohr.routers.configure import router as configure_router
from app.integrations.categories.hrms.bamboohr.routers.data import router as data_router
from app.integrations.categories.hrms.bamboohr.routers.webhook import router as webhook_router

__all__ = ["configure_router", "data_router", "webhook_router"]
>>>>>>> master
