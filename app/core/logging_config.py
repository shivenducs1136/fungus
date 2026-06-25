"""Central logging configuration for the knowledge server."""

import logging
import logging.handlers
import os
from pathlib import Path


_LOG_DIR = Path(os.getenv("FUNGUS_LOG_DIR", Path(__file__).resolve().parents[2] / "logs"))
_LOG_DIR.mkdir(parents=True, exist_ok=True)

_HANDLERS_BY_FILE: dict[str, logging.Handler] = {}


def _get_handler(log_file_name: str) -> logging.Handler:
    """Return a cached rotating file handler for the requested log file."""
    existing = _HANDLERS_BY_FILE.get(log_file_name)
    if existing is not None:
        return existing

    handler = logging.handlers.RotatingFileHandler(
        _LOG_DIR / log_file_name,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(name)s  %(funcName)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    _HANDLERS_BY_FILE[log_file_name] = handler
    return handler


def get_logger(name: str, log_file_name: str = "knowledge_server.log") -> logging.Logger:
    """Return a logger configured for the requested server log file."""
    logger = logging.getLogger(name)
    logger.setLevel(os.getenv("FUNGUS_LOG_LEVEL", "INFO").upper())

    handler = _get_handler(log_file_name)
    if handler not in logger.handlers:
        logger.addHandler(handler)

    logger.propagate = False
    return logger
