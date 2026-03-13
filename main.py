import warnings

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SAWarning

from HRMS_Integrations import zoho_people_router
from ITSM_Integrations import jira_servicedesk_router
from IdP_Integrations import okta_router
from integration_collection import router as integration_collection_router
from control_evaluation import router as control_evaluation_router


# Suppress known SQLAlchemy SAWarning coming from generated models.py
warnings.filterwarnings(
    "ignore",
    category=SAWarning,
    message="Implicitly combining column trustcenter_users.created_at.*",
)
warnings.filterwarnings(
    "ignore",
    category=SAWarning,
    message="Implicitly combining column trustcenter_users.updated_at.*",
)

app = FastAPI(title="Tool Integrations Backend - GRC Platform")

# CORS: allow all origins/methods/headers for now
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(zoho_people_router)
app.include_router(jira_servicedesk_router)
app.include_router(okta_router)
app.include_router(integration_collection_router)
app.include_router(control_evaluation_router)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    # Allows running and debugging via "Python: Current File" or launch.json
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=True)

