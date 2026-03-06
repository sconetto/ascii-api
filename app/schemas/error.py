"""Error response schemas."""

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response model for all API errors."""

    detail: str = Field(description="Human-readable error message")
    type: str | None = Field(default=None, description="Error type/class name")
