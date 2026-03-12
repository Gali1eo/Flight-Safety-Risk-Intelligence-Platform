"""Starter ingestion pipeline for approved source datasets."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.common.config import load_config, resolve_path
from src.common.logging_utils import get_logger


LOGGER = get_logger(__name__)


def discover_source_files(dataset_name: str) -> list[Path]:
    """Return CSV files located under the configured raw dataset path."""
    config = load_config()
    dataset_path = resolve_path(config["datasets"][dataset_name]["path"])
    dataset_path.mkdir(parents=True, exist_ok=True)
    source_files = sorted(dataset_path.glob("*.csv"))
    LOGGER.info("Discovered %s file(s) for dataset '%s'", len(source_files), dataset_name)
    return source_files


def load_dataset(dataset_name: str) -> pd.DataFrame:
    """Load and concatenate all CSV files for a configured dataset."""
    source_files = discover_source_files(dataset_name)
    if not source_files:
        LOGGER.warning(
            "No files found for dataset '%s'. Returning an empty dataframe.",
            dataset_name,
        )
        return pd.DataFrame()

    dataframes = [pd.read_csv(file_path) for file_path in source_files]
    combined = pd.concat(dataframes, ignore_index=True)
    LOGGER.info("Loaded %s rows for dataset '%s'", len(combined), dataset_name)
    return combined


def main() -> None:
    """Run starter ingestion discovery across all configured datasets."""
    config = load_config()
    for dataset_name in config["datasets"]:
        load_dataset(dataset_name)


if __name__ == "__main__":
    main()
