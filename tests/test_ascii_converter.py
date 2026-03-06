"""Unit tests for the ascii_converter service."""

import pytest
from PIL import Image

from app.exceptions import InvalidImageError
from app.services.ascii_converter import (
    ASCII_CHARS,
    convert,
    convert_to_grayscale,
    load_image,
    map_pixels_to_ascii,
    resize_image,
)


class TestLoadImage:
    """Tests for load_image function."""

    def test_load_valid_png(self, sample_image_bytes: bytes) -> None:
        """Test loading a valid PNG image."""
        img = load_image(sample_image_bytes)
        assert isinstance(img, Image.Image)
        assert img.size == (10, 10)

    def test_load_valid_jpeg(self, sample_jpeg_bytes: bytes) -> None:
        """Test loading a valid JPEG image."""
        img = load_image(sample_jpeg_bytes)
        assert isinstance(img, Image.Image)

    def test_load_valid_webp(self, sample_webp_bytes: bytes) -> None:
        """Test loading a valid WebP image."""
        img = load_image(sample_webp_bytes)
        assert isinstance(img, Image.Image)

    def test_load_invalid_data(self, invalid_image_bytes: bytes) -> None:
        """Test loading invalid data raises InvalidImageError."""
        with pytest.raises(InvalidImageError):
            load_image(invalid_image_bytes)

    def test_load_empty_data(self) -> None:
        """Test loading empty data raises InvalidImageError."""
        with pytest.raises(InvalidImageError):
            load_image(b"")


class TestResizeImage:
    """Tests for resize_image function."""

    def test_resize_with_defaults(self, sample_image_bytes: bytes) -> None:
        """Test resizing with default height factor."""
        img = load_image(sample_image_bytes)
        resized = resize_image(img, width=50, height_factor=0.5)
        assert resized.width == 50
        # 10x10 image resized to width=50: 50 * (10/10) * 0.5 = 25
        assert resized.height == 25

    def test_resize_with_custom_height_factor(self, sample_image_bytes: bytes) -> None:
        """Test resizing with custom height factor."""
        img = load_image(sample_image_bytes)
        resized = resize_image(img, width=50, height_factor=0.7)
        assert resized.width == 50
        # 10x10 image resized to width=50: 50 * (10/10) * 0.7 = 35
        assert resized.height == 35

    def test_resize_wide_image(self, sample_image_bytes: bytes) -> None:
        """Test resizing a wide image."""
        # Create a wide image (100x50)
        wide_img = Image.new("RGB", (100, 50), color="white")
        resized = resize_image(wide_img, width=50, height_factor=0.5)
        assert resized.width == 50
        # 50/100 * 50 * 0.5 = 12.5 -> 12


class TestConvertToGrayscale:
    """Tests for convert_to_grayscale function."""

    def test_convert_rgb_to_grayscale(self, sample_image_bytes: bytes) -> None:
        """Test converting RGB image to grayscale."""
        img = load_image(sample_image_bytes)
        gray = convert_to_grayscale(img)
        assert gray.mode == "L"

    def test_grayscale_stays_grayscale(self, sample_image_bytes: bytes) -> None:
        """Test grayscale image stays grayscale."""
        img = load_image(sample_image_bytes)
        gray = convert_to_grayscale(img)
        # Convert again
        gray2 = convert_to_grayscale(gray)
        assert gray2.mode == "L"


class TestMapPixelsToAscii:
    """Tests for map_pixels_to_ascii function."""

    def test_map_white_image(self, sample_image_bytes: bytes) -> None:
        """Test mapping a white image (all bright pixels)."""
        img = load_image(sample_image_bytes)
        img = resize_image(img, width=10, height_factor=0.5)
        img = convert_to_grayscale(img)
        ascii_art = map_pixels_to_ascii(img)
        # White image should use brightest characters
        lines = ascii_art.split("\n")
        assert len(lines) > 0
        # First character should be one of the brightest ($)
        assert lines[0][0] == "$"

    def test_map_black_image(self) -> None:
        """Test mapping a black image (all dark pixels)."""
        img = Image.new("L", (10, 5), color=0)  # Black
        ascii_art = map_pixels_to_ascii(img)
        lines = ascii_art.split("\n")
        # Black image should use darkest character (space)
        assert lines[0][0] == " "

    def test_ascii_art_has_correct_width(self, sample_image_bytes: bytes) -> None:
        """Test ASCII art has correct width."""
        img = load_image(sample_image_bytes)
        img = resize_image(img, width=10, height_factor=0.5)
        img = convert_to_grayscale(img)
        ascii_art = map_pixels_to_ascii(img)
        lines = ascii_art.split("\n")
        # Filter out empty lines (trailing newlines)
        lines = [line for line in lines if line]
        assert all(len(line) == 10 for line in lines)


class TestConvert:
    """Tests for the main convert function."""

    def test_convert_png(self, sample_image_bytes: bytes) -> None:
        """Test converting a PNG image."""
        ascii_art, width, height = convert(
            sample_image_bytes, width=20, height_factor=0.5
        )
        assert isinstance(ascii_art, str)
        assert width == 20
        assert height > 0

    def test_convert_jpeg(self, sample_jpeg_bytes: bytes) -> None:
        """Test converting a JPEG image."""
        ascii_art, width, height = convert(
            sample_jpeg_bytes, width=20, height_factor=0.5
        )
        assert isinstance(ascii_art, str)
        assert width == 20
        assert height > 0

    def test_convert_with_default_params(self, sample_image_bytes: bytes) -> None:
        """Test converting with default parameters."""
        ascii_art, width, height = convert(sample_image_bytes)
        assert width == 100  # default
        assert height > 0

    def test_convert_invalid_data(self, invalid_image_bytes: bytes) -> None:
        """Test converting invalid data raises InvalidImageError."""
        with pytest.raises(InvalidImageError):
            convert(invalid_image_bytes)

    def test_ascii_chars_ordered_dark_to_bright(self) -> None:
        """Verify ASCII_CHARS is ordered from dark to bright."""
        assert ASCII_CHARS[0] == " "  # Darkest
        assert ASCII_CHARS[-1] == "$"  # Brightest
