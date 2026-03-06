"""Health check response schemas."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response model for all health check endpoints."""

    status: str
    service: str
    version: str
