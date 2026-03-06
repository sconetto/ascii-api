"""FastAPI application factory.

Wires together all middleware, exception handlers, and routers.
Sentry and observability hooks (logging, metrics, middleware) are added
here as stubs now and fully implemented in Phase 7.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import Settings
from app.exceptions import (
    AsciiAPIError,
    ascii_api_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from app.metrics import setup_metrics
from app.middleware import RequestLoggingMiddleware
from app.routers import health, images


def _init_sentry(settings: Settings) -> None:
    """Initialise Sentry SDK if a DSN is configured."""
    if not settings.sentry_dsn:
        return

    import sentry_sdk  # noqa: PLC0415

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        traces_sample_rate=settings.sentry_sample_rate,
        release=settings.version,
        send_default_pii=False,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan: startup and shutdown logic."""
    # Startup
    settings: Settings = app.state.settings
    _init_sentry(settings)
    yield
    # Shutdown (nothing to clean up yet)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = Settings()

    app = FastAPI(
        title="ascii-api",
        description="Convert images to ASCII art via a REST API.",
        version=settings.version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Store settings on app state so lifespan and middleware can access them
    app.state.settings = settings

    # ── Middleware (outermost first) ─────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(RequestLoggingMiddleware)

    # ── Exception handlers ───────────────────────────────────────────────────
    app.add_exception_handler(AsciiAPIError, ascii_api_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_error_handler)  # type: ignore[arg-type]

    # ── Routers ──────────────────────────────────────────────────────────────
    app.include_router(health.router)
    app.include_router(images.router)

    # ── Observability ────────────────────────────────────────────────────────
    setup_metrics(app)

    return app


app = create_app()
