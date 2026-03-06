# ascii-api

[![Python 3.14](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/release/python-3140/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://github.com/sconetto/ascii-api/actions/workflows/unit-test.yml/badge.svg)](https://github.com/sconetto/ascii-api/actions/workflows/unit-test.yml)
[![Coverage](https://codecov.io/gh/sconetto/ascii-api/branch/main/graph/badge.svg)](https://codecov.io/gh/sconetto/ascii-api)

A FastAPI REST API service for converting images to ASCII art.

## Features

- **Image to ASCII conversion** - Convert JPEG, PNG, and WebP images to ASCII art
- **Configurable output** - Adjust output width (50-200 characters) and height factor (0.3-0.7)
- **Optional authentication** - Enable API key authentication via environment variables
- **Rate limiting** - 10 requests per minute per IP (configurable)
- **Security** - File size limits, magic number validation, decompression bomb protection
- **Observability** - Structured logging (JSON for Grafana Loki), Prometheus metrics, Sentry integration
- **Docker-ready** - Multi-stage build, non-root user, Kubernetes health checks

## Quick Start

### Using Docker Compose

```bash
# Start the service
docker compose up -d

# Check health
curl http://localhost:8000/health

# Convert an image
curl -X POST http://localhost:8000/api/v1/images/convert \
  -F "file=@my-image.jpg" \
  -F "width=100" \
  -F "height_factor=0.5"
```

### Using Python Directly

```bash
# Install dependencies
uv sync

# Run the server
uv run uvicorn app.main:app --reload

# Convert an image (in another terminal)
curl -X POST http://localhost:8000/api/v1/images/convert \
  -F "file=@my-image.jpg"
```

## API Reference

### Convert Image to ASCII

```bash
POST /api/v1/images/convert
```

**Parameters:**

| Parameter       | Type    | Required | Default | Range     | Description                       |
|-----------------|---------|----------|---------|-----------|-----------------------------------|
| `file`          | file    | Yes      | -       | -         | Image file (JPEG, PNG, or WebP)   |
| `width`         | int     | No       | 100     | 50-200    | Output width in characters        |
| `height_factor` | float   | No       | 0.5     | 0.3-0.7   | Aspect ratio correction factor    |

**Response:**

```json
{
  "ascii_art": "$$$@@@BBBB...",
  "width": 100,
  "height": 45,
  "height_factor": 0.5,
  "original_format": "jpeg"
}
```

**Error Responses:**

- `400` - Invalid image file
- `413` - File too large
- `415` - Unsupported file type
- `422` - Validation error
- `429` - Rate limit exceeded

### Health Checks

| Endpoint            | Description                    |
|---------------------|--------------------------------|
| `GET /health`       | Basic liveness check           |
| `GET /health/ready` | Readiness probe (Kubernetes)   |
| `GET /health/live`  | Liveness probe (Kubernetes)    |

### Metrics

```bash
GET /metrics
```

Prometheus metrics including:

- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request duration
- `images_converted_total` - Total images converted

## Configuration

All configuration is done via environment variables. See `.env.example` for all options.

### Key Variables

| Variable          | Default      | Description                          |
|-------------------|--------------|--------------------------------------|
| `MAX_FILE_SIZE`   | 10485760     | Max upload size in bytes (10MB)      |
| `DEFAULT_WIDTH`   | 100          | Default ASCII output width           |
| `HEIGHT_FACTOR`   | 0.5          | Default height factor (0.3-0.7)      |
| `AUTH_ENABLED`    | false        | Enable API key authentication        |
| `API_KEY`         | -            | API key (required if auth enabled)   |
| `LOG_JSON_FORMAT` | false        | Output JSON for Loki (vs console)    |
| `SENTRY_DSN`      | -            | Sentry DSN for error tracking        |

### Enabling Authentication

```bash
# Set environment variables
AUTH_ENABLED=true
API_KEY=your-secret-api-key

# Then use in requests
curl -X POST http://localhost:8000/api/v1/images/convert \
  -H "Authorization: Bearer your-secret-api-key" \
  -F "file=@my-image.jpg"
```

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run linter
uv run ruff check --fix
uv run ruff format

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=term-missing --cov-report=html
```

## Docker

### Production Build

```bash
# Build the image
docker build -t ascii-api .

# Run the container
docker run -p 8000:8000 ascii-api
```

### Development (Docker Compose)

For local development with hot reload:

```bash
# Start the service with volume mounts and auto-reload
docker compose -f dev-docker-compose.yml up -d

# View logs
docker compose -f dev-docker-compose.yml logs -f

# Stop the service
docker compose -f dev-docker-compose.yml down
```

The development compose file:

- Mounts the `app/` directory for live code reloading
- Exposes port 8000
- Runs with `LOG_LEVEL=DEBUG` for verbose logging

### Production

The Docker image runs as a non-root user (`appuser`) for security.

## License

MIT License - see [LICENSE](LICENSE) file for details.
