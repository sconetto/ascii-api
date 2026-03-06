"""Image conversion endpoints.

Provides the POST /api/v1/images/convert endpoint which accepts an image file
and returns its ASCII art representation.
"""

from fastapi import APIRouter, File, Form, Request, UploadFile

from app.auth import AuthDep
from app.dependencies import SettingsDep
from app.exceptions import (
    DecompressionBombError,
    FileTooLargeError,
    InvalidImageError,
)
from app.schemas.image import ImageConvertResponse
from app.services.ascii_converter import convert as ascii_convert
from app.services.rate_limiter import get_rate_limiter
from app.services.validators import validate_file_type

router = APIRouter(prefix="/api/v1/images", tags=["images"])


@router.post(
    "/convert",
    response_model=ImageConvertResponse,
    summary="Convert image to ASCII art",
    description="Upload an image (JPEG, PNG, or WebP) to convert it to ASCII art.",
)
async def convert_image(
    request: Request,
    settings: SettingsDep,
    auth: AuthDep,
    file: UploadFile = File(..., description="Image file to convert"),  # noqa: B008
    width: int = Form(
        default=100, ge=50, le=200, description="Output width in characters"
    ),
    height_factor: float = Form(
        default=0.5, ge=0.3, le=0.7, description="Aspect ratio correction factor"
    ),
) -> ImageConvertResponse:
    """Convert an uploaded image to ASCII art.

    The endpoint validates the file type using magic numbers, enforces the
    maximum file size, and applies the ASCII conversion pipeline.

    Rate limiting is applied per IP address (default: 10 requests/minute).

    Authentication is optional and can be enabled via AUTH_ENABLED and API_KEY
    environment variables.
    """
    # Apply rate limiting
    rate_limiter = get_rate_limiter(settings)
    rate_limiter.check(request)

    # Validate content type from header
    content_type = file.content_type

    # Read file content (with size limit enforcement)
    max_size = settings.max_file_size
    chunks: list[bytes] = []
    total_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > max_size:
            raise FileTooLargeError()
        chunks.append(chunk)

    file_data = b"".join(chunks)

    # Validate file type using magic numbers (Pillow)
    validate_file_type(content_type, file_data)

    # Convert to ASCII art
    try:
        ascii_art, out_width, out_height = ascii_convert(
            file_data, width=width, height_factor=height_factor
        )
    except DecompressionBombError:
        raise
    except InvalidImageError:
        raise

    # Detect original format from the uploaded file
    original_format = content_type.split("/")[-1] if content_type else "unknown"
    if original_format == "jpeg":
        original_format = "jpeg"

    return ImageConvertResponse(
        ascii_art=ascii_art,
        width=out_width,
        height=out_height,
        height_factor=height_factor,
        original_format=original_format,
    )
