"""
Structured logging configuration using structlog.

Security Features:
- PII masking for emails, credit cards, SSNs, API keys
- Based on pii_patterns.json and secret_patterns.json from knowledge base
"""
import logging
import re
import sys
from typing import Any

import structlog
from structlog.types import Processor

from indexer_api.core.config import settings


# PII Masking Patterns (from knowledge base pii_patterns.json)
PII_PATTERNS = {
    "email": (
        re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        lambda m: f"{m.group(0)[:3]}***@***{m.group(0).split('@')[1][-4:]}" if '@' in m.group(0) else "***"
    ),
    "credit_card": (
        re.compile(r'\b(?:4[0-9]{3}|5[1-5][0-9]{2}|3[47][0-9]{2}|6(?:011|5[0-9]{2}))[- ]?[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\b'),
        lambda m: "****-****-****-" + m.group(0)[-4:]
    ),
    "ssn": (
        re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        lambda m: "***-**-" + m.group(0)[-4:]
    ),
    "api_key": (
        re.compile(r'(sk_(?:live|test)_[A-Za-z0-9]{24,}|ghp_[A-Za-z0-9]{36,}|sk-[A-Za-z0-9]{48}|sk-ant-[A-Za-z0-9-]{80,})'),
        lambda m: m.group(0)[:10] + "***REDACTED***"
    ),
    "jwt": (
        re.compile(r'eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+'),
        lambda m: "eyJ***REDACTED***"
    ),
    "password": (
        re.compile(r'(?:password|passwd|pwd|secret)["\']?\s*[:=]\s*["\']?[^\s"\']+', re.IGNORECASE),
        lambda m: re.sub(r'([:=]\s*["\']?)[^\s"\']+', r'\1***REDACTED***', m.group(0))
    ),
}


def mask_pii(value: Any) -> Any:
    """
    Mask PII in a value.

    Handles strings, dicts, and lists recursively.
    Uses patterns from knowledge base for GDPR/CCPA compliance.
    """
    if isinstance(value, str):
        masked = value
        for pattern_name, (pattern, replacer) in PII_PATTERNS.items():
            masked = pattern.sub(replacer, masked)
        return masked
    elif isinstance(value, dict):
        return {k: mask_pii(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [mask_pii(item) for item in value]
    return value


def pii_masking_processor(
    logger: structlog.BoundLogger,
    method_name: str,
    event_dict: dict[str, Any]
) -> dict[str, Any]:
    """
    Structlog processor to mask PII in log entries.

    Applied to all log entries to ensure GDPR/CCPA compliance.
    """
    return mask_pii(event_dict)


def setup_logging() -> None:
    """Configure structured logging for the application."""

    # Shared processors for all outputs
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        pii_masking_processor,  # Add PII masking
    ]

    if settings.log_format == "json":
        # JSON format for production
        processors: list[Processor] = [
            *shared_processors,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Console format for development
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Also configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def bind_context(**kwargs: Any) -> None:
    """Bind context variables to the current logging context."""
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context() -> None:
    """Clear all context variables."""
    structlog.contextvars.clear_contextvars()
