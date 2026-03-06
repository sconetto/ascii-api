"""Structured logging configuration using structlog.

Configures logging for both development (console) and production (JSON for Loki).
"""

import logging

import structlog
from structlog.types import EventDict

from app.config import Settings


def add_log_level(
    logger: structlog.stdlib.Logger, method_name: int, event_dict: EventDict
) -> EventDict:
    """Add the log level to the event dict."""
    event_dict["level"] = logging.getLevelName(method_name)
    return event_dict


def timestamper() -> structlog.processors.TimeStamper:
    """Create a TimeStamper processor for ISO timestamps."""
    return structlog.processors.TimeStamper(fmt="iso", utc=True)


def configure_logging(settings: Settings) -> None:
    """Configure structlog based on settings.

    In development (LOG_JSON_FORMAT=false): uses ConsoleRenderer
    for human-readable output.
    In production (LOG_JSON_FORMAT=true): uses JSONRenderer
    for Loki compatibility.
    """
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        add_log_level,
        timestamper(),
        structlog.processors.format_exc_info,
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.log_json_format:
        # Production: JSON output for Loki
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Development: human-readable console output
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structlog logger instance.

    Args:
        name: Optional logger name. If None, uses __name__ from caller.

    Returns:
        A configured structlog BoundLogger.
    """
    if name is None:
        import inspect

        frame = inspect.currentframe()
        if frame is not None:
            caller_frame = frame.f_back
            name = caller_frame.f_globals.get("__name__", "ascii-api")
    return structlog.get_logger(name)
