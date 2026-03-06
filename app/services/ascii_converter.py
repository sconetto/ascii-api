"""Image to ASCII art conversion service.

This module provides the core conversion logic: load an image from bytes,
resize with aspect ratio correction, convert to grayscale, and map pixel
brightness to ASCII characters.
"""

from io import BytesIO

from PIL import Image

from app.exceptions import DecompressionBombError, InvalidImageError

ASCII_CHARS = " `.-^',:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#%@$"


def load_image(data: bytes) -> Image.Image:
    """Load a PIL Image from raw bytes.

    Applies decompression bomb protection based on MAX_IMAGE_PIXELS setting.

    Args:
        data: Raw image bytes (JPEG, PNG, or WebP).

    Returns:
        A PIL Image object.

    Raises:
        InvalidImageError: If the data cannot be opened as an image.
        DecompressionBombError: If the image exceeds the pixel limit.
    """
    try:
        image = Image.open(BytesIO(data))
        image.load()
    except Exception as e:
        raise InvalidImageError(f"Could not load image: {e}") from e

    if hasattr(Image, "DecompressionBombError"):
        max_pixels = Image.MAX_IMAGE_PIXELS
        if max_pixels and image.size[0] * image.size[1] > max_pixels:
            raise DecompressionBombError()

    return image


def resize_image(image: Image.Image, width: int, height_factor: float) -> Image.Image:
    """Resize image with aspect ratio correction.

    Terminal characters are taller than they are wide (~2:1 ratio), so we
    scale height by height_factor to compensate.

    Args:
        image: Source PIL Image.
        width: Target width in characters.
        height_factor: Multiplier to correct aspect ratio (0.3-0.7).

    Returns:
        Resized PIL Image.
    """
    original_width, original_height = image.size
    new_height = int(width * (original_height / original_width) * height_factor)
    return image.resize((width, new_height), Image.Resampling.LANCZOS)


def convert_to_grayscale(image: Image.Image) -> Image.Image:
    """Convert image to 8-bit grayscale.

    Args:
        image: Source PIL Image (any mode).

    Returns:
        Grayscale PIL Image (mode "L").
    """
    if image.mode != "L":
        return image.convert("L")
    return image


def map_pixels_to_ascii(image: Image.Image) -> str:
    """Map each pixel's brightness to an ASCII character.

    Uses the ordered ASCII_CHARS string where characters range from
    darkest (" ", space) to brightest ("$").

    Args:
        image: Grayscale PIL Image (mode "L").

    Returns:
        ASCII art string with newlines between rows.
    """
    width = image.width
    pixels = list(image.get_flattened_data())  # type: ignore[arg-type]

    ascii_rows = []
    chars_len = len(ASCII_CHARS) - 1
    for i in range(0, len(pixels), width):
        row = pixels[i : i + width]
        ascii_row = "".join(ASCII_CHARS[(pixel * chars_len) // 255] for pixel in row)
        ascii_rows.append(ascii_row)

    return "\n".join(ascii_rows)


def convert(
    data: bytes,
    width: int = 100,
    height_factor: float = 0.5,
) -> tuple[str, int, int]:
    """Convert image bytes to ASCII art.

    This is the main orchestrator that chains:
        1. Load image from bytes
        2. Resize with aspect ratio correction
        3. Convert to grayscale
        4. Map pixels to ASCII characters

    Args:
        data: Raw image bytes.
        width: Output width in characters (default: 100).
        height_factor: Aspect ratio correction factor (default: 0.5).

    Returns:
        A tuple of (ascii_art_string, output_width, output_height).

    Raises:
        InvalidImageError: If the data cannot be opened as an image.
        DecompressionBombError: If the image exceeds the pixel limit.
    """
    image = load_image(data)
    image = resize_image(image, width, height_factor)
    image = convert_to_grayscale(image)
    ascii_art = map_pixels_to_ascii(image)

    return ascii_art, width, image.height
