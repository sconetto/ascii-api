"""Health check endpoints.

Provides three probes following the Kubernetes convention:
  GET /health        - Basic check (alias for liveness)
  GET /health/live   - Liveness probe: is the process alive?
  GET /health/ready  - Readiness probe: is the process ready to serve traffic?
"""

from fastapi import APIRouter

from app.dependencies import SettingsDep
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Basic health check",
    description="Returns 200 when the service is running. Alias for /health/live.",
)
async def health(settings: SettingsDep) -> HealthResponse:
    """Basic liveness check."""
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        version=settings.version,
    )


@router.get(
    "/health/live",
    response_model=HealthResponse,
    summary="Liveness probe",
    description="Kubernetes liveness probe. Returns 200 when the process is alive.",
)
async def liveness(settings: SettingsDep) -> HealthResponse:
    """Kubernetes liveness probe."""
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        version=settings.version,
    )


@router.get(
    "/health/ready",
    response_model=HealthResponse,
    summary="Readiness probe",
    description=(
        "Kubernetes readiness probe. "
        "Returns 200 when the service is ready to serve traffic."
    ),
)
async def readiness(settings: SettingsDep) -> HealthResponse:
    """Kubernetes readiness probe."""
    return HealthResponse(
        status="ready",
        service=settings.service_name,
        version=settings.version,
    )
