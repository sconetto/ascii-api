"""Custom exceptions and FastAPI exception handlers.

All application-specific errors are defined here with their corresponding
HTTP status codes. Exception handlers are registered on the FastAPI app
in app/main.py.
"""

from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.error import ErrorResponse

# ── Custom exception classes ─────────────────────────────────────────────────


class AsciiAPIError(Exception):
    """Base class for all ascii-api application errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "An unexpected error occurred."

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)


class FileTooLargeError(AsciiAPIError):
    """Raised when the uploaded file exceeds the size limit."""

    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    detail = "File size exceeds the maximum allowed limit."


class UnsupportedFileTypeError(AsciiAPIError):
    """Raised when the uploaded file type is not supported."""

    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    detail = "Unsupported file type. Allowed types: JPEG, PNG, WebP."


class InvalidImageError(AsciiAPIError):
    """Raised when the uploaded file cannot be opened as a valid image."""

    status_code = status.HTTP_400_BAD_REQUEST
    detail = "The uploaded file is not a valid image."


class DecompressionBombError(AsciiAPIError):
    """Raised when the image exceeds the maximum pixel limit."""

    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Image dimensions exceed the maximum allowed pixel count."


class AuthenticationError(AsciiAPIError):
    """Raised when authentication fails or is missing."""

    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Authentication required. Provide a valid API key."


class RateLimitError(AsciiAPIError):
    """Raised when the rate limit is exceeded."""

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    detail = "Rate limit exceeded. Please slow down your requests."


# ── Exception handlers ───────────────────────────────────────────────────────


async def ascii_api_error_handler(
    _request: Request, exc: AsciiAPIError
) -> JSONResponse:
    """Handle all AsciiAPIError subclasses with a consistent JSON response."""
    headers: dict[str, str] = {}
    if isinstance(exc, AuthenticationError):
        headers["WWW-Authenticate"] = "Bearer"

    error = ErrorResponse(detail=exc.detail, type=type(exc).__name__)
    return JSONResponse(
        status_code=exc.status_code,
        content=error.model_dump(),
        headers=headers or None,
    )


async def validation_error_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic request validation errors with a clean JSON response."""
    errors: list[dict[str, Any]] = [
        {
            "field": ".".join(str(loc) for loc in err["loc"]),
            "message": err["msg"],
            "type": err["type"],
        }
        for err in exc.errors()
    ]
    error = ErrorResponse(detail="Request validation failed.")
    content = error.model_dump()
    content["errors"] = errors
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=content,
    )


async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unexpected errors.

    In production, details are hidden to avoid leaking internal information.
    Sentry (if configured) will capture the full traceback separately.
    """
    error = ErrorResponse(
        detail="An internal server error occurred.", type="InternalServerError"
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error.model_dump(),
    )
