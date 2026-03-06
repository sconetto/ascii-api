"""Pytest configuration and fixtures for ascii-api tests."""

import io

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Return a TestClient for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def settings() -> Settings:
    """Return a Settings instance with test defaults."""
    return Settings(
        max_file_size=10_485_760,
        max_pixels=25_000_000,
        default_width=100,
        max_width=200,
        height_factor=0.5,
        rate_limit=10,
        auth_enabled=False,
        api_key=None,
        log_level="INFO",
        log_json_format=False,
        service_name="ascii-api",
        version="0.1.0",
    )


@pytest.fixture
def settings_auth_enabled() -> Settings:
    """Return a Settings instance with authentication enabled."""
    return Settings(
        max_file_size=10_485_760,
        max_pixels=25_000_000,
        default_width=100,
        max_width=200,
        height_factor=0.5,
        rate_limit=10,
        auth_enabled=True,
        api_key="test-api-key",
        log_level="INFO",
        log_json_format=False,
        service_name="ascii-api",
        version="0.1.0",
    )


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Return valid PNG image bytes (a small white 10x10 image)."""
    from PIL import Image

    img = Image.new("RGB", (10, 10), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


@pytest.fixture
def sample_jpeg_bytes() -> bytes:
    """Return valid JPEG image bytes (a small white 10x10 image)."""
    from PIL import Image

    img = Image.new("RGB", (10, 10), color="white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.read()


@pytest.fixture
def sample_webp_bytes() -> bytes:
    """Return valid WebP image bytes (a small white 10x10 image)."""
    from PIL import Image

    img = Image.new("RGB", (10, 10), color="white")
    buf = io.BytesIO()
    img.save(buf, format="WEBP")
    buf.seek(0)
    return buf.read()


@pytest.fixture
def invalid_image_bytes() -> bytes:
    """Return invalid image bytes (plain text)."""
    return b"This is not an image!"
