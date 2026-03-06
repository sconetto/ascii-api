"""Unit tests for the validators service."""

import io

import pytest

from app.exceptions import FileTooLargeError, UnsupportedFileTypeError
from app.services.validators import (
    ALLOWED_MIME_TYPES,
    enforce_size_limit,
    sanitize_filename,
    validate_file_type,
)


class TestValidateFileType:
    """Tests for validate_file_type function."""

    def test_valid_png_with_correct_content_type(
        self, sample_image_bytes: bytes
    ) -> None:
        """Test validating a valid PNG with correct content type."""
        # Should not raise
        validate_file_type("image/png", sample_image_bytes)

    def test_valid_jpeg_with_correct_content_type(
        self, sample_jpeg_bytes: bytes
    ) -> None:
        """Test validating a valid JPEG with correct content type."""
        validate_file_type("image/jpeg", sample_jpeg_bytes)

    def test_valid_webp_with_correct_content_type(
        self, sample_webp_bytes: bytes
    ) -> None:
        """Test validating a valid WebP with correct content type."""
        validate_file_type("image/webp", sample_webp_bytes)

    def test_valid_image_with_wrong_content_type(
        self, sample_image_bytes: bytes
    ) -> None:
        """Test validating a valid image with wrong content type."""
        with pytest.raises(UnsupportedFileTypeError):
            validate_file_type("image/gif", sample_image_bytes)

    def test_valid_image_with_no_content_type(self, sample_image_bytes: bytes) -> None:
        """Test validating a valid image with no content type."""
        # Should not raise - content type is optional
        validate_file_type(None, sample_image_bytes)

    def test_image_with_no_detected_format(self) -> None:
        """Test that image with no detected format raises error."""
        # Create a minimal valid PNG in memory
        from PIL import Image

        img = Image.new("RGB", (10, 10), color="red")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        # Corrupt the format detection by passing bad data
        with pytest.raises(UnsupportedFileTypeError):
            validate_file_type("image/png", b"not an image")

    def test_valid_image_unsupported_by_pillow(self) -> None:
        """Test that valid image format not supported by Pillow raises error."""
        # BMP format is valid but not in our allowed list
        from PIL import Image

        img = Image.new("RGB", (10, 10), color="blue")
        buf = io.BytesIO()
        img.save(buf, format="BMP")
        buf.seek(0)
        with pytest.raises(UnsupportedFileTypeError):
            validate_file_type("image/bmp", buf.read())

    def test_invalid_data_with_any_content_type(
        self, invalid_image_bytes: bytes
    ) -> None:
        """Test validating invalid data raises UnsupportedFileTypeError."""
        with pytest.raises(UnsupportedFileTypeError):
            validate_file_type("image/png", invalid_image_bytes)

    def test_unsupported_content_type_with_valid_data(
        self, sample_image_bytes: bytes
    ) -> None:
        """Test unsupported content type is rejected even with valid data."""
        with pytest.raises(UnsupportedFileTypeError):
            validate_file_type("image/gif", sample_image_bytes)

    def test_unsupported_content_type_with_text_file(self) -> None:
        """Test text file is rejected."""
        with pytest.raises(UnsupportedFileTypeError):
            validate_file_type("text/plain", b"This is text")

    def test_allowed_mime_types_contains_expected(self) -> None:
        """Verify ALLOWED_MIME_TYPES contains expected values."""
        assert "image/jpeg" in ALLOWED_MIME_TYPES
        assert "image/png" in ALLOWED_MIME_TYPES
        assert "image/webp" in ALLOWED_MIME_TYPES
        assert len(ALLOWED_MIME_TYPES) == 3


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_generates_uuid_filename(self) -> None:
        """Test that generated filename is a UUID with .bin extension."""
        filename = sanitize_filename()
        # UUID format: 8-4-4-4-12 hex digits + .bin
        assert filename.endswith(".bin")
        assert len(filename) == 36 + 4  # UUID (36) + .bin (4)

    def test_ignores_original_filename(self) -> None:
        """Test that original filename is ignored."""
        filename1 = sanitize_filename("malicious../../etc/passwd")
        filename2 = sanitize_filename("normal.jpg")
        # Should be different (random), not using the input
        assert filename1 != filename2
        # Neither should contain the input
        assert "malicious" not in filename1
        assert "normal" not in filename2

    def test_generates_unique_filenames(self) -> None:
        """Test that multiple calls generate unique filenames."""
        filenames = {sanitize_filename() for _ in range(100)}
        # All should be unique
        assert len(filenames) == 100


class TestEnforceSizeLimit:
    """Tests for enforce_size_limit function."""

    def test_file_within_size_limit(self) -> None:
        """Test that files within the size limit pass through."""
        data = b"small content"
        stream = (chunk for chunk in [data])
        result = b"".join(enforce_size_limit(stream, max_size=100))
        assert result == data

    def test_file_exactly_at_limit(self) -> None:
        """Test that file exactly at the limit passes through."""
        data = b"x" * 10
        stream = (chunk for chunk in [data])
        result = b"".join(enforce_size_limit(stream, max_size=10))
        assert result == data

    def test_file_exceeds_limit(self) -> None:
        """Test that files exceeding the limit raise FileTooLargeError."""
        data = b"x" * 15
        stream = (chunk for chunk in [data])
        with pytest.raises(FileTooLargeError):
            b"".join(enforce_size_limit(stream, max_size=10))

    def test_multiple_chunks_within_limit(self) -> None:
        """Test streaming with multiple chunks all within limit."""
        chunks = [b"chunk1", b"chunk2", b"chunk3"]
        stream = (chunk for chunk in chunks)
        result = b"".join(enforce_size_limit(stream, max_size=100))
        assert result == b"chunk1chunk2chunk3"

    def test_multiple_chunks_exceeds_limit(self) -> None:
        """Test streaming with multiple chunks exceeding limit."""
        chunks = [b"aaa", b"bbb", b"ccc"]  # total 9 bytes
        stream = (chunk for chunk in chunks)
        with pytest.raises(FileTooLargeError):
            b"".join(enforce_size_limit(stream, max_size=7))  # fails on 3rd chunk

    def test_empty_file(self) -> None:
        """Test that empty files pass through."""
        stream = (chunk for chunk in [b""])
        result = b"".join(enforce_size_limit(stream, max_size=10))
        assert result == b""
