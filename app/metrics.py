"""Prometheus metrics for monitoring application behavior.

Provides metrics for HTTP requests, request duration, and image conversion counts.
These metrics are exposed via the /metrics endpoint for Prometheus scraping.
"""

from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    make_asgi_app,  # pyright: ignore[reportUnknownVariableType]
)

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

images_converted_total = Counter(
    "images_converted_total",
    "Total images converted to ASCII",
)

images_in_memory_cache = Gauge(
    "images_in_memory_cache",
    "Number of images in memory cache",
)


def track_request_metrics(request: Request, response: Response) -> None:
    http_requests_total.labels(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
    ).inc()


def track_request_duration(request: Request, response: Response) -> None:
    duration = request.state.duration
    http_request_duration_seconds.labels(
        method=request.method,
        path=request.url.path,
    ).observe(duration)


def setup_metrics(app: FastAPI) -> None:
    @app.middleware("http")  # type: ignore[misc]
    async def metrics_middleware(  # type: ignore[unused-ignore]
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start = perf_counter()
        response = await call_next(request)
        request.state.duration = perf_counter() - start

        track_request_metrics(request, response)
        track_request_duration(request, response)

        return response

    # Create and mount the Prometheus metrics ASGI app
    metrics_app = make_asgi_app()  # type: ignore[no-untyped-call]
    app.mount("/metrics", metrics_app)  # type: ignore[arg-type]
