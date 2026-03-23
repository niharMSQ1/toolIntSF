from __future__ import annotations

from fastapi import FastAPI

from app.integrations.api import mount_integration_routes

app = FastAPI(
    title="Stakflo GRC tool integration",
    version="0.1.0",
)

mount_integration_routes(app)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
