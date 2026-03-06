# ascii-api Work Plan

## Project Overview

**Project Name**: ascii-api  
**Type**: FastAPI REST API Service  
**Core Functionality**: Accept image uploads and convert them to ASCII art representation  
**Target Users**: Developers and end-users who need ASCII art conversion

---

## Technical Stack

| Component               | Technology        | Version |
| ----------------------- | ----------------- | ------- |
| Framework               | FastAPI           | latest  |
| Server                  | Uvicorn           | latest  |
| Image Processing        | Pillow (PIL)      | latest  |
| Linter/Formatter        | ruff              | latest  |
| Logging                 | structlog         | latest  |
| Metrics                 | prometheus-client | latest  |
| Error Tracking          | Sentry            | latest  |
| Log Aggregation         | Grafana Loki      | latest  |
| File Uploads            | python-multipart  | latest  |
| Async I/O               | aiofiles          | latest  |
| Magic Number Validation | python-magic      | latest  |
| Rate Limiting           | fastapi-limiter   | latest  |
| Authentication          | python-jose (JWT) | latest  |
| Deployment              | Docker            | latest  |

---

## Core Design Decisions

| Decision         | Value                                   |
| ---------------- | --------------------------------------- |
| Image Support    | Static only (no GIF animation)          |
| Processing Model | Synchronous                             |
| Authentication   | Basic JWT/API Key (disabled by default) |
| Deployment       | Docker-compliant                        |

---

## Project Structure

```bash
ascii-api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app + middleware
│   ├── config.py               # Settings (Pydantic BaseSettings)
│   ├── dependencies.py         # Shared dependencies
│   ├── auth.py                 # JWT/API Key authentication
│   ├── logging.py              # structlog configuration
│   ├── middleware.py           # Request logging + correlation ID
│   ├── metrics.py              # Prometheus metrics
│   ├── exceptions.py           # Custom exceptions + handlers
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── images.py           # Image upload/processing endpoints
│   │   └── health.py           # Health check endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ascii_converter.py  # Core ASCII conversion logic
│   │   └── validators.py       # File validation utilities
│   └── schemas/
│       ├── __init__.py
│       ├── image.py            # Pydantic models
│       └── error.py            # Error response models
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # FastAPI TestClient fixtures
│   ├── test_image_service.py
│   └── test_routers.py
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── .gitignore
├── pyproject.toml
├── ruff.toml
└── README.md
```

---

## Core Features

### 1. Image Upload Endpoint

- **Route**: `POST /api/v1/images/convert`
- **Input**: Multipart form with image file
- **Parameters**:
  - `file`: Image file (required)
  - `width`: Output width in characters (optional, default: 100, min: 50, max: 200)
  - `height_factor`: Aspect ratio adjustment (optional, default: 0.5, range: 0.3-0.7)
- **Output**: JSON with ASCII art string
- **Auth**: Optional (configurable via environment)

### 2. Health Check Endpoints

- **Route**: `GET /health` - Basic liveness
- **Route**: `GET /health/ready` - Readiness probe (Kubernetes)
- **Route**: `GET /health/live` - Liveness probe (Kubernetes)

### 3. Authentication

- **Route**: N/A (header-based)
- **Header**: `Authorization: Bearer <token>`
- **Environment**: `AUTH_ENABLED=false` (default)
- **API Key**: Configurable via `API_KEY` env var

### 4. Metrics Endpoint

- **Route**: `GET /metrics` - Prometheus metrics
- **Output**: Prometheus text format
- **Metrics**: HTTP requests, duration, images converted

### 5. Error Tracking (Sentry)

- Automatic exception capture
- Request ID correlation
- Performance monitoring (optional)
- Configure via `SENTRY_DSN` environment variable

---

## Security Implementation

### File Size Limits

- **Application level**: 10MB max (configurable via `MAX_FILE_SIZE`)
- **Implementation**: Stream in 1MB chunks, reject if exceeded

### File Type Validation

- **Allowed MIME types**: `image/jpeg`, `image/png`, `image/webp`
- **Method**: Magic number validation using `python-magic`
- **Validation points**:
  1. Check client-provided Content-Type header
  2. Validate magic numbers (first 2048 bytes)
  3. Verify with Pillow image loading

### Filename Sanitization

- **Never use user-provided filenames**
- **Generate UUID-based filenames** for any stored files
- **Allowed extensions**: `.jpg`, `.jpeg`, `.png`, `.webp`

### Rate Limiting

- **Strategy**: fastapi-limiter with in-memory backend (Redis for production)
- **Limits**:
  - Upload endpoint: 10 requests per minute per IP
  - Configurable via environment

### Authentication (Optional)

- **Strategy**: API Key via Authorization header
- **Enabled by**: `AUTH_ENABLED=true` environment variable
- **Key**: Set via `API_KEY` environment variable

---

## Docker Configuration

### Dockerfile (Multi-stage Build)

```dockerfile
# Build stage
FROM python:3.14-slim AS builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --user --no-cache-dir .

# Production stage
FROM python:3.14-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "app.main:app"]
```

### docker-compose.yml

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - AUTH_ENABLED=false
      - MAX_FILE_SIZE=10485760
    volumes:
      - ./app:/app/app
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## Image Processing Pipeline

### ASCII Conversion Flow

```text
1. Load image (Pillow Image.open)
apply2. Check/ MAX_IMAGE_PIXELS limit (decompression bomb protection)
3. Convert RGBA to RGB (if needed)
4. Resize with aspect ratio correction (configurable factor)
5. Convert to grayscale (mode "L")
6. Map pixels to ASCII characters
7. Return formatted ASCII string
```

### Character Mapping

- **Character set**: `"$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^'. "`
- **Mapping method**:

  ```python
  char_index = (pixel_brightness * (len(chars) - 1)) // 255
  ```

### Aspect Ratio Correction

- Terminal characters are approximately 2x taller than wide (0.5 ratio)
- Default `height_factor`: 0.5 (better than previous 0.45)
- Formula: `new_height = int(new_width * (original_height / original_width) * height_factor)`

### Dynamic Aspect Ratio (Optional Enhancement)

For extreme aspect ratios, apply adaptive factors:

```python
aspect_ratio = original_width / original_height

if aspect_ratio > 2:      # Very wide image (panoramas)
    height_factor = 0.55
elif aspect_ratio < 0.5:  # Very tall image
    height_factor = 0.4
else:
    height_factor = 0.5   # Default for normal images
```

### Decompression Bomb Protection

- **Setting**: `Image.MAX_IMAGE_PIXELS = 25_000_000` (25 megapixels)
- **Purpose**: Prevents malicious images with extreme dimensions
- **Error**: Raises `Image.DecompressionBombError` if exceeded

---

## Implementation Tasks

### Phase 1: Project Setup

- [ ] Initialize Python project with pyproject.toml
- [ ] Configure ruff (pyproject.toml or ruff.toml)
- [ ] Create Dockerfile (multi-stage, non-root user)
- [ ] Create docker-compose.yml
- [ ] Create .dockerignore
- [ ] Setup .gitignore
- [ ] Create virtual environment and install dependencies

### Phase 2: Core Application

- [ ] Create app/main.py with FastAPI instance
  - [ ] Add CORS middleware
  - [ ] Add GZip middleware
  - [ ] Register exception handlers
- [ ] Create app/config.py with Settings class (Pydantic BaseSettings)
- [ ] Create app/dependencies.py with common dependencies
- [ ] Create app/auth.py
  - [ ] API Key dependency
  - [ ] Auth enabled/disabled logic
- [ ] Create app/exceptions.py with custom exceptions
- [ ] Add health check endpoints (app/routers/health.py)
  - [ ] GET /health
  - [ ] GET /health/ready
  - [ ] GET /health/live

### Phase 3: Image Processing Service

- [ ] Create app/services/ascii_converter.py
  - [ ] `load_image()` - Load from bytes
  - [ ] `resize_image()` - With aspect ratio correction
  - [ ] `convert_to_grayscale()` - Using Pillow
  - [ ] `map_pixels_to_ascii()` - Core conversion logic
  - [ ] `convert()` - Main orchestrator method
- [ ] Write unit tests for ascii_converter

### Phase 4: Upload Endpoint with Security

- [ ] Create app/services/validators.py
  - [ ] `validate_file_type()` - Magic number validation
  - [ ] `enforce_size_limit()` - Streaming size check
  - [ ] `sanitize_filename()` - UUID-based naming
- [ ] Create app/schemas/image.py
  - [ ] `ImageConvertRequest`
  - [ ] `ImageConvertResponse`
  - [ ] Validation (width: min=50, max=200, height_factor: min=0.3, max=0.7)
- [ ] Create app/schemas/error.py
  - [ ] `ErrorResponse` model
- [ ] Create app/routers/images.py
  - [ ] POST /api/v1/images/convert endpoint
  - [ ] Apply rate limiting
  - [ ] Integrate validators
  - [ ] Integrate authentication (optional)

### Phase 5: Testing

- [ ] Setup pytest configuration (pyproject.toml)
- [ ] Create tests/conftest.py with FastAPI TestClient fixtures
- [ ] Write tests for validators
- [ ] Write tests for routers (mock file uploads)
- [ ] Write tests for auth dependency
- [ ] Add integration tests

### Phase 6: Documentation & Polish

- [ ] Add OpenAPI docs (FastAPI built-in)
- [ ] Update README.md with:
  - Docker instructions
  - API Key setup
  - Example curl commands
- [ ] Test Docker build locally
- [ ] Verify health endpoints

### Phase 7: Observability (Logging, Metrics, Error Tracking)

- [ ] Create app/logging.py with structlog configuration
  - [ ] JSON renderer for production (Loki-compatible)
  - [ ] Console renderer for development
  - [ ] Processor chain (timestamp, level, logger name, exceptions)
- [ ] Create app/middleware.py
  - [ ] Request logging middleware
  - [ ] Correlation ID injection (X-Request-ID)
  - [ ] Suppress uvicorn access logs (re-emit via structlog)
- [ ] Create app/metrics.py with Prometheus metrics
  - [ ] Request count (counter)
  - [ ] Request duration (histogram)
  - [ ] Images converted (counter)
  - [ ] GET /metrics endpoint
- [ ] Integrate Sentry
  - [ ] Add sentry-sdk to dependencies
  - [ ] Initialize in app/main.py
  - [ ] Configure DSN via environment variable
  - [ ] Add request ID to Sentry scope

---

## Logging, Monitoring & Debugging

### Structured Logging (structlog)

**Configuration:**

- Development: `ConsoleRenderer` (colorful, human-readable)
- Production: `JSONRenderer` (Grafana Loki-compatible)

**Processor Chain:**

```text
1. merge_contextvars     - Add request context
2. add_logger_name       - Source logger
3. add_log_level         - Log level
4. TimeStamper           - ISO timestamp
5. format_exc_info       - Exception handling
6. JSONRenderer          - Production output
```

**Log Entry Format (JSON for Loki):**

```json
{
  "timestamp": "2026-03-05T10:30:45.123Z",
  "level": "info",
  "event": "image_convert_started",
  "service": "ascii-api",
  "version": "1.0.0",
  "request_id": "abc-123-def",
  "client_ip": "192.168.1.1",
  "duration_ms": 145.5
}
```

### Correlation IDs

- Generate UUID for each request
- Inject via middleware
- Include in all log messages
- Return in response header: `X-Request-ID`

### HTTP Request Logging

Every request logs:

- Path, method, status code
- Duration (ms)
- Client IP
- Request ID

### Third-Party Log Noise Reduction

Suppress/limit logs from:

- `uvicorn.access` - Re-emit via structlog middleware
- `uvicorn.error` - Keep
- `PIL` - Warning only
- `urllib3` - Warning only

### Prometheus Metrics

**Endpoint**: `GET /metrics`

**Metrics:**

| Metric              | Type      | Description                    |
| ------------------- | --------- | ------------------------------ |
| `http_requests_total` | Counter   | Total HTTP requests           |
| `http_request_duration_seconds` | Histogram | Request duration            |
| `images_converted_total` | Counter   | Total images converted       |
| `conversion_duration_seconds` | Histogram | Image conversion duration   |

### Sentry Integration

**Configuration:**

- DSN via `SENTRY_DSN` environment variable
- Environment: `SENTRY_ENVIRONMENT` (dev/staging/prod)
- Sample rate: `SENTRY_SAMPLE_RATE` (default: 1.0)

**Features:**

- Automatic exception capture
- Request ID correlation
- Performance monitoring (optional)
- Release tracking via `SENTRY_RELEASE`

### Security Best Practices

- **NEVER log:** Passwords, tokens, API keys, PII
- **Sanitize:** User input before logging
- **Prevent log injection:** Escape newlines in user data

---

## Configuration

### Environment Variables

| Variable          | Description                   | Default         |
| ----------------- | ----------------------------- | --------------- |
| `MAX_FILE_SIZE`   | Max upload size (bytes)       | 10485760 (10MB) |
| `MAX_PIXELS`      | Max image pixels (decompression protection) | 25000000 (25MP) |
| `DEFAULT_WIDTH`   | Default ASCII width           | 100             |
| `MAX_WIDTH`       | Maximum width                 | 200             |
| `HEIGHT_FACTOR`  | Default height factor         | 0.5             |
| `RATE_LIMIT`     | Requests/minute               | 10              |
| `AUTH_ENABLED`   | Enable authentication         | false           |
| `API_KEY`        | API key for auth              | (none)          |
| `LOG_LEVEL`      | Logging level                 | INFO            |
| `LOG_JSON_FORMAT`| Output JSON (Loki) vs console | false           |
| `SERVICE_NAME`   | Service identifier            | ascii-api       |
| `SENTRY_DSN`     | Sentry DSN for error tracking | (none)          |
| `SENTRY_ENVIRONMENT` | Environment (dev/prod)   | development     |
| `SENTRY_SAMPLE_RATE` | Trace sample rate        | 1.0             |

### Allowed Settings

- **Image formats**: JPEG, PNG, WebP
- **Max file size**: 10MB
- **Max image pixels**: 25 megapixels (decompression bomb protection)
- **Output width**: 50-200 characters
- **Height factor**: 0.3-0.7 (default: 0.5)

---

## API Specification

### POST /api/v1/images/convert

**Request**:

```bash
curl -X POST "http://localhost:8000/api/v1/images/convert" \
  -H "Authorization: Bearer <token>" \
  -F "file=@image.jpg" \
  -F "width=100" \
  -F "height_factor=0.5"
```

**Response**:

```json
{
  "ascii_art": "$$$@@@BBBB...",
  "width": 100,
  "height": 45,
  "height_factor": 0.5,
  "original_format": "jpeg"
}
```

**Error Responses**:

- `400`: Invalid image file
- `401`: Authentication required
- `413`: File too large
- `415`: Unsupported file type
- `422`: Validation error
- `429`: Rate limit exceeded
- `500`: Internal server error

---

## Acceptance Criteria

1. Service starts without errors
2. Valid images are converted to ASCII art correctly
3. Character density matches the provided character set ordering
4. Invalid files are rejected with appropriate error messages
5. File size limits are enforced
6. Rate limiting prevents abuse
7. Authentication can be enabled/disabled via environment
8. Docker container runs as non-root user
9. Health endpoints work correctly
10. All code passes ruff linting
11. Unit tests cover core conversion logic
12. Structured logging outputs JSON format for Loki
13. Correlation IDs included in all log entries
14. Prometheus metrics available at /metrics
15. Sentry captures exceptions with request correlation

---

## Notes

- ASCII output includes newline characters between rows
- Authentication is optional and disabled by default
- For production: add Redis for rate limiting
- Container runs on non-root user for security
- Health checks are Kubernetes-compatible
- Aspect ratio uses 0.5 as default (better for most terminals)
- Decompression bomb protection limits images to 25 megapixels
- User can adjust `height_factor` (0.3-0.7) for different terminals
- Structured logging with structlog (JSON for Loki, console for dev)
- Correlation IDs for request tracing (X-Request-ID header)
- Prometheus metrics at /metrics endpoint
- Sentry integration for error tracking (configure SENTRY_DSN)
