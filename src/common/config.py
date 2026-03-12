"""Configuration loading helpers for the project."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load the YAML configuration used by the pipeline."""
    resolved_path = config_path or CONFIG_PATH
    with resolved_path.open("r", encoding="utf-8") as config_file:
        return yaml.safe_load(config_file)


def resolve_path(path_value: str) -> Path:
    """Resolve a repository-relative path from the config."""
    return (PROJECT_ROOT / path_value).resolve()
