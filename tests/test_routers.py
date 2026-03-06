"""Tests for routers (health and images endpoints)."""

import io

from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_endpoint_returns_ok(self, client: TestClient) -> None:
        """Test /health returns 200 with status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "ascii-api"
        assert data["version"] == "0.1.0"

    def test_health_live_endpoint(self, client: TestClient) -> None:
        """Test /health/live returns 200."""
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_health_ready_endpoint(self, client: TestClient) -> None:
        """Test /health/ready returns 200 with status ready."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"


class TestImageConvertEndpoint:
    """Tests for POST /api/v1/images/convert endpoint."""

    def test_convert_valid_png(
        self, client: TestClient, sample_image_bytes: bytes
    ) -> None:
        """Test converting a valid PNG image."""
        files = {"file": ("test.png", io.BytesIO(sample_image_bytes), "image/png")}
        data = {"width": 50, "height_factor": 0.5}
        response = client.post("/api/v1/images/convert", files=files, data=data)
        assert response.status_code == 200
        json_data = response.json()
        assert "ascii_art" in json_data
        assert json_data["width"] == 50
        assert json_data["height_factor"] == 0.5
        assert json_data["original_format"] == "png"

    def test_convert_valid_jpeg(
        self, client: TestClient, sample_jpeg_bytes: bytes
    ) -> None:
        """Test converting a valid JPEG image."""
        files = {"file": ("test.jpg", io.BytesIO(sample_jpeg_bytes), "image/jpeg")}
        data = {"width": 50, "height_factor": 0.5}
        response = client.post("/api/v1/images/convert", files=files, data=data)
        assert response.status_code == 200
        assert response.json()["original_format"] == "jpeg"

    def test_convert_with_default_params(
        self, client: TestClient, sample_image_bytes: bytes
    ) -> None:
        """Test converting with default width and height_factor."""
        files = {"file": ("test.png", io.BytesIO(sample_image_bytes), "image/png")}
        response = client.post("/api/v1/images/convert", files=files)
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["width"] == 100  # default
        assert json_data["height_factor"] == 0.5  # default

    def test_convert_with_custom_width(
        self, client: TestClient, sample_image_bytes: bytes
    ) -> None:
        """Test converting with custom width."""
        files = {"file": ("test.png", io.BytesIO(sample_image_bytes), "image/png")}
        data = {"width": 75}
        response = client.post("/api/v1/images/convert", files=files, data=data)
        assert response.status_code == 200
        assert response.json()["width"] == 75

    def test_convert_invalid_file_type(self, client: TestClient) -> None:
        """Test converting an invalid file type returns 415."""
        files = {"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")}
        response = client.post("/api/v1/images/convert", files=files)
        assert response.status_code == 415

    def test_convert_invalid_image_data(
        self, client: TestClient, invalid_image_bytes: bytes
    ) -> None:
        """Test converting invalid image data returns 415 (unsupported type)."""
        files = {"file": ("test.png", io.BytesIO(invalid_image_bytes), "image/png")}
        response = client.post("/api/v1/images/convert", files=files)
        assert response.status_code == 415

    def test_convert_width_below_minimum(
        self, client: TestClient, sample_image_bytes: bytes
    ) -> None:
        """Test width below minimum returns 422."""
        files = {"file": ("test.png", io.BytesIO(sample_image_bytes), "image/png")}
        data = {"width": 10}  # min is 50
        response = client.post("/api/v1/images/convert", files=files, data=data)
        assert response.status_code == 422

    def test_convert_width_above_maximum(
        self, client: TestClient, sample_image_bytes: bytes
    ) -> None:
        """Test width above maximum returns 422."""
        files = {"file": ("test.png", io.BytesIO(sample_image_bytes), "image/png")}
        data = {"width": 300}  # max is 200
        response = client.post("/api/v1/images/convert", files=files, data=data)
        assert response.status_code == 422

    def test_convert_height_factor_below_minimum(
        self, client: TestClient, sample_image_bytes: bytes
    ) -> None:
        """Test height_factor below minimum returns 422."""
        files = {"file": ("test.png", io.BytesIO(sample_image_bytes), "image/png")}
        data = {"height_factor": 0.1}  # min is 0.3
        response = client.post("/api/v1/images/convert", files=files, data=data)
        assert response.status_code == 422

    def test_convert_height_factor_above_maximum(
        self, client: TestClient, sample_image_bytes: bytes
    ) -> None:
        """Test height_factor above maximum returns 422."""
        files = {"file": ("test.png", io.BytesIO(sample_image_bytes), "image/png")}
        data = {"height_factor": 1.0}  # max is 0.7
        response = client.post("/api/v1/images/convert", files=files, data=data)
        assert response.status_code == 422

    def test_convert_missing_file(self, client: TestClient) -> None:
        """Test missing file returns 422."""
        response = client.post("/api/v1/images/convert", data={})
        assert response.status_code == 422

    def test_ascii_art_contains_newlines(
        self, client: TestClient, sample_image_bytes: bytes
    ) -> None:
        """Test ASCII art output contains newlines between rows."""
        files = {"file": ("test.png", io.BytesIO(sample_image_bytes), "image/png")}
        data = {"width": 50}
        response = client.post("/api/v1/images/convert", files=files, data=data)
        assert response.status_code == 200
        ascii_art = response.json()["ascii_art"]
        assert "\n" in ascii_art
