from __future__ import annotations

import logging
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.middleware.http")


def _auth_header_summary(request: Request) -> str:
    raw = request.headers.get("authorization")
    if not raw:
        return "none"
    lower = raw.lower()
    if lower.startswith("bearer "):
        return "Bearer <redacted>"
    return "<redacted>"


class HttpRequestResponseLogMiddleware(BaseHTTPMiddleware):
    """
    Logs each incoming request (method, path, safe headers) and the response status after the stack.
    Does not log request bodies or full tokens.
    """

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        client = request.client.host if request.client else "?"
        qs_raw = str(request.query_params)
        qs = qs_raw if qs_raw else "-"
        print(
            "[http] incoming",
            f"method={request.method}",
            f"path={request.url.path}",
            f"query={qs}",
            f"client={client}",
            f"origin={request.headers.get('origin') or '-'}",
            f"content_type={request.headers.get('content-type') or '-'}",
            f"authorization={_auth_header_summary(request)}",
            flush=True,
        )
        logger.info(
            "incoming method=%s path=%s query=%s client=%s origin=%s content_type=%s authorization=%s",
            request.method,
            request.url.path,
            qs,
            client,
            request.headers.get("origin") or "-",
            request.headers.get("content-type") or "-",
            _auth_header_summary(request),
        )

        response = await call_next(request)

        print(
            "[http] response",
            f"method={request.method}",
            f"path={request.url.path}",
            f"status={response.status_code}",
            flush=True,
        )
        logger.info(
            "response method=%s path=%s status=%s",
            request.method,
            request.url.path,
            response.status_code,
        )
        return response
