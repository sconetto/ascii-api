"""File validation utilities for secure image uploads.

Provides functions to validate file type using Pillow, enforce size limits
via streaming, and generate safe filenames.
"""

import io
import uuid
from collections.abc import Generator

from PIL import Image

from app.exceptions import UnsupportedFileTypeError

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
CHUNK_SIZE = 1024 * 1024  # 1MB chunks for streaming


def validate_file_type(content_type: str | None, data: bytes) -> None:
    """Validate file type using Content-Type header and magic numbers.

    Args:
        content_type: Client-provided Content-Type header.
        data: First bytes of the file for magic number detection.

    Raises:
        UnsupportedFileTypeError: If the file type is not allowed.
    """
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        raise UnsupportedFileTypeError()

    try:
        img = Image.open(io.BytesIO(data))
        img.load()  # Force loading to verify it's a valid image
        if img.format is None:
            raise UnsupportedFileTypeError()
        detected = img.format.lower()
    except UnsupportedFileTypeError:
        raise
    except Exception:
        raise UnsupportedFileTypeError() from None

    if detected not in ("jpeg", "png", "webp"):
        raise UnsupportedFileTypeError()


def enforce_size_limit(
    file_stream: Generator[bytes], max_size: int
) -> Generator[bytes]:
    """Stream a file while enforcing a maximum size limit.

    Args:
        file_stream: Generator yielding file chunks.
        max_size: Maximum allowed size in bytes.

    Yields:
        File chunks up to the maximum size.

    Raises:
        FileTooLargeError: If the file exceeds the size limit.
    """
    from app.exceptions import FileTooLargeError

    total = 0
    for chunk in file_stream:
        total += len(chunk)
        if total > max_size:
            raise FileTooLargeError()
        yield chunk


def sanitize_filename(original_filename: str | None = None) -> str:
    """Generate a safe filename using UUID.

    Never uses the user-provided filename to prevent path traversal attacks.
    The original filename is ignored; a random UUID is used instead.

    Args:
        original_filename: Ignored (kept for API compatibility).

    Returns:
        A safe filename with .bin extension (actual type determined elsewhere).
    """
    return f"{uuid.uuid4()}.bin"
