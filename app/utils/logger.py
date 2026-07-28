"""Centralized logging configuration.

Provides structured logging across all modules with configurable levels.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """Configure root logger with console and optional file output.

    Args:
        level: Logging level (default: INFO).
        log_file: Optional path to log file.

    Returns:
        Configured root logger instance.
    """
    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-7s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger("remoteollama")
    root.setLevel(level)

    # Console handler
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(fmt)
        root.addHandler(console)

    # File handler (optional)
    if log_file:
        file_path = Path(log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(file_path), encoding="utf-8")
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)

    return root


def get_logger(name: str) -> logging.Logger:
    """Get a named logger under the 'remoteollama' namespace.

    Args:
        name: Logger name (typically __name__ of the calling module).

    Returns:
        Logger instance.
    """
    return logging.getLogger(f"remoteollama.{name}")
