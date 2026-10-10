"""Structured logging configuration for AI Business Architect.

Provides request correlation IDs and safe masking of sensitive credentials.
"""

import json
import logging
import re
import sys
from typing import Any, Dict

# Keys whose values must never appear in logs
SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "secret_key",
    "gemini_api_key",
    "api_key",
    "token",
    "authorization",
    "cookie",
    "session",
    "access_token",
    "refresh_token",
}

# Regex to mask passwords and secrets in connection strings or JSON strings
PASSWORD_URL_PATTERN = re.compile(r"://([^:]+):([^@]+)@")


def mask_sensitive_url(url: str) -> str:
    """Mask password in database URL: postgresql://user:****@host:5432/db"""
    return PASSWORD_URL_PATTERN.sub(r"://\1:****@", url)


def mask_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively mask sensitive values in dictionaries."""
    sanitized = {}
    for k, v in data.items():
        if any(sens in k.lower() for sens in SENSITIVE_KEYS):
            sanitized[k] = "********"
        elif isinstance(v, dict):
            sanitized[k] = mask_dict(v)
        elif isinstance(v, list):
            sanitized[k] = [mask_dict(item) if isinstance(item, dict) else item for item in v]
        elif isinstance(v, str) and ("://" in v and "@" in v):
            sanitized[k] = mask_sensitive_url(v)
        else:
            sanitized[k] = v
    return sanitized


class StructuredLogFormatter(logging.Formatter):
    """JSON/Structured formatter for application logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include correlation/request ID if present
        request_id = getattr(record, "request_id", None)
        if request_id:
            log_obj["request_id"] = request_id

        # Include structured extra fields if present
        extra = getattr(record, "extra_fields", None)
        if extra and isinstance(extra, dict):
            log_obj.update(mask_dict(extra))

        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            log_obj["exception"] = record.exc_text

        return json.dumps(log_obj)


def configure_logging(level: str = "INFO") -> None:
    """Configure root logger with structured formatter."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    # Avoid duplicate handlers
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredLogFormatter())
        root_logger.addHandler(handler)
    else:
        for h in root_logger.handlers:
            h.setFormatter(StructuredLogFormatter())

    # Suppress verbose third-party logs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
