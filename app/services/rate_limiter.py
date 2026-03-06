"""In-memory rate limiter for request throttling.

Provides a simple per-IP in-memory rate limiter using a sliding window algorithm.
"""

import time
from collections import defaultdict
from threading import Lock

from fastapi import Request

from app.config import Settings
from app.exceptions import RateLimitError


class InMemoryRateLimiter:
    """Simple in-memory rate limiter per IP address.

    Uses a sliding window algorithm to track requests per IP address.
    Thread-safe using a lock for concurrent access.
    """

    def __init__(self, requests_per_minute: int = 10):  # noqa: ANN204
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request.

        Checks X-Forwarded-For header first for reverse proxy scenarios,
        then falls back to the direct client host.
        """
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def check(self, request: Request) -> None:
        """Check if request is within rate limit.

        Raises:
            RateLimitError: If the client has exceeded their rate limit.
        """
        client_ip = self._get_client_ip(request)
        now = time.time()
        window_start = now - 60  # 1 minute window

        with self._lock:
            # Clean old requests
            self.requests[client_ip] = [
                ts for ts in self.requests[client_ip] if ts > window_start
            ]

            # Check limit
            if len(self.requests[client_ip]) >= self.requests_per_minute:
                raise RateLimitError()

            # Record this request
            self.requests[client_ip].append(now)


# Global rate limiter instance (created on first request to get settings)
_rate_limiter: InMemoryRateLimiter | None = None


def get_rate_limiter(settings: Settings) -> InMemoryRateLimiter:
    """Get or create the rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = InMemoryRateLimiter(requests_per_minute=settings.rate_limit)
    return _rate_limiter
