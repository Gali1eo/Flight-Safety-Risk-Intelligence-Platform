"""Starter trusted-layer transformation pipeline."""

from __future__ import annotations

import pandas as pd

from src.common.config import load_config, resolve_path
from src.common.logging_utils import get_logger
from src.common.validation import (
    standardize_columns,
    validate_no_duplicates,
    validate_null_threshold,
    validate_required_columns,
)
from src.ingest.ingest_datasets import load_dataset


LOGGER = get_logger(__name__)


TRUSTED_REQUIRED_COLUMNS = ["event_id", "event_date", "source_system"]


def build_trusted_events() -> pd.DataFrame:
    """Build a starter trusted events table from synthetic or public raw inputs."""
    raw_events = load_dataset("synthetic_safety_culture")
    if raw_events.empty:
        LOGGER.warning("Trusted layer build skipped because no raw records were found.")
        return raw_events

    trusted_events = standardize_columns(raw_events)
    validate_required_columns(trusted_events, TRUSTED_REQUIRED_COLUMNS)

    config = load_config()
    validate_null_threshold(trusted_events, config["metadata"]["null_check_threshold"])
    validate_no_duplicates(trusted_events, ["event_id"])

    LOGGER.info("Built trusted events table with %s rows", len(trusted_events))
    return trusted_events


def persist_trusted_events(frame: pd.DataFrame) -> None:
    """Persist the trusted events table to the trusted layer."""
    if frame.empty:
        LOGGER.warning("No trusted events were written because the dataframe is empty.")
        return

    config = load_config()
    output_path = resolve_path(config["outputs"]["trusted_events_table"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(output_path, index=False)
    LOGGER.info("Wrote trusted events table to %s", output_path)


def main() -> None:
    """Run the trusted-layer transformation pipeline."""
    trusted_events = build_trusted_events()
    persist_trusted_events(trusted_events)


if __name__ == "__main__":
    main()
