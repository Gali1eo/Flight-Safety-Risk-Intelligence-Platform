"""Logging helpers for consistent pipeline observability."""

from __future__ import annotations

import logging
from pathlib import Path

from src.common.config import load_config, resolve_path


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for pipeline modules."""
    config = load_config()
    logs_dir = resolve_path(config["paths"]["logs"])
    logs_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(Path(logs_dir) / "pipeline.log")
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger
