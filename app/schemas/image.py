"""Image conversion request and response schemas."""

from pydantic import BaseModel, Field


class ImageConvertResponse(BaseModel):
    """Response model for successful image-to-ASCII conversion."""

    ascii_art: str = Field(description="The ASCII art representation of the image")
    width: int = Field(description="Output width in characters")
    height: int = Field(description="Output height in characters")
    height_factor: float = Field(
        description="Height factor used for aspect ratio correction"
    )
    original_format: str = Field(description="Original image format (jpeg, png, webp)")
