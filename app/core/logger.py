# app/core/logger.py
from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

_DEFAULT_LOG_LEVEL = "INFO"
_DEFAULT_LOG_DIR = os.getenv("APP_LOG_DIR", "./logs")  # 환경변수로 덮어쓰기 가능
_DEFAULT_LOG_FILE = os.getenv("APP_LOG_FILE", "app.log")


def _build_logger(
    name: str = "app",
    level: str = _DEFAULT_LOG_LEVEL,
    log_dir: str = _DEFAULT_LOG_DIR,
    log_file: str = _DEFAULT_LOG_FILE,
) -> logging.Logger:
    """
    Create a process-wide logger that writes to both console and file.

    - Console: stdout
    - File: Rotating file under log_dir/log_file
    - Safe against duplicate handlers on repeated imports
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times (very common in FastAPI reload / multi-import)
    if logger.handlers:
        return logger

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    logger.propagate = False  # prevent double logging via root logger

    fmt = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (print-like)
    sh = logging.StreamHandler(stream=sys.stdout)
    sh.setLevel(numeric_level)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    # File handler (rotating)
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    fh = RotatingFileHandler(
        filename=str(Path(log_dir) / log_file),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    fh.setLevel(numeric_level)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


# Create a shared logger instance for the whole app
LOGGER = _build_logger()


def set_logging_level(level: str) -> None:
    """
    Update logger and handler levels at runtime.
    """
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")

    LOGGER.setLevel(numeric_level)
    for h in LOGGER.handlers:
        h.setLevel(numeric_level)

    LOGGER.info("Log level set to %s", level.upper())


def set_log(message: str, *, level: str = "INFO") -> None:
    """
    Public logging function you can import and use anywhere.

    - Prints to console via StreamHandler
    - Persists to file via RotatingFileHandler
    """
    lvl = level.upper()
    if lvl == "DEBUG":
        LOGGER.debug("%s", message)
    elif lvl == "WARNING":
        LOGGER.warning("%s", message)
    elif lvl == "ERROR":
        LOGGER.error("%s", message)
    elif lvl == "CRITICAL":
        LOGGER.critical("%s", message)
    else:
        LOGGER.info("%s", message)


def get_log_path() -> str:
    """
    Useful for debugging: shows where the file logs are being written.
    """
    log_dir = _DEFAULT_LOG_DIR
    log_file = _DEFAULT_LOG_FILE
    return str(Path(log_dir) / log_file)
