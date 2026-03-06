"""Middleware for request processing.

Includes request logging middleware that adds correlation IDs and logs
request details for debugging and tracing.
"""

import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.logging import get_logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        log = get_logger("ascii-api").bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None,
        )

        log.info("request_started")

        try:
            response = await call_next(request)
            log.info(
                "request_completed",
                status_code=response.status_code,
            )
            return response
        except Exception as e:
            log.exception("request_failed", error=str(e))
            raise
