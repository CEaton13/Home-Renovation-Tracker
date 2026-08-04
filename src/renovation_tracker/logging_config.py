"""Structured JSON logging configuration using structlog."""

import logging
import sys

import structlog


def configure_logging() -> None:
    """Configure structlog to emit machine-parseable JSON log lines.

    Should be called once, during app startup, before any log calls
    are made.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )