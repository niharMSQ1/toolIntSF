from __future__ import annotations

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.integrations.api import mount_integration_routes

app = FastAPI(
    title="Stakflo GRC tool integration",
    version="0.1.0",
)

# Allow any browser origin. Wildcard requires allow_credentials=False (Bearer tokens in headers are fine).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

mount_integration_routes(app)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
