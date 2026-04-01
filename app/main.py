from __future__ import annotations

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.integrations.api import mount_integration_routes
from app.middleware.http_log import HttpRequestResponseLogMiddleware

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


class _OptionsPreflightMiddleware(BaseHTTPMiddleware):
    """
    Starlette CORSMiddleware skips when `Origin` is missing, so OPTIONS can fall through and
    hit POST-only routes → 405. Browsers send OPTIONS before POST (CORS preflight); answer here.
    """

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        if request.method == "OPTIONS":
            print(
                "[options-middleware] preflight — returning 200, path=",
                request.url.path,
                "origin=",
                request.headers.get("origin") or "-",
                flush=True,
            )
            return Response(
                status_code=200,
                content=b"",
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Max-Age": "600",
                },
            )
        return await call_next(request)


# Add last so this runs first (outermost): handles OPTIONS before routing.
app.add_middleware(_OptionsPreflightMiddleware)

# Outermost: log every request/response (method, path, safe headers, status).
app.add_middleware(HttpRequestResponseLogMiddleware)

mount_integration_routes(app)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
