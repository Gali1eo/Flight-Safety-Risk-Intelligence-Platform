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
from src.transform.build_asrs_trusted_layer import (
    build_asrs_trusted_reports,
    persist_asrs_trusted_reports,
)
from src.transform.build_bts_trusted_layer import (
    build_bts_trusted_operations,
    persist_bts_trusted_operations,
)
from src.transform.build_ntsb_trusted_layer import (
    build_ntsb_trusted_investigations,
    persist_ntsb_trusted_investigations,
)


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

    duplicate_count = int(trusted_events.duplicated(subset=["event_id"]).sum())
    if duplicate_count:
        LOGGER.warning(
            "Dropping %s duplicate row(s) using event_id before trusted-layer publication.",
            duplicate_count,
        )
        trusted_events = trusted_events.drop_duplicates(subset=["event_id"]).reset_index(
            drop=True
        )

    config = load_config()
    validate_null_threshold(trusted_events, config["metadata"]["null_check_threshold"])
    validate_no_duplicates(trusted_events, ["event_id"])

    LOGGER.info("Built trusted events table with %s rows", len(trusted_events))
    return trusted_events


def persist_trusted_events(frame: pd.DataFrame) -> None:
    """Persist the trusted events table to the trusted layer as CSV for the local demo."""
    if frame.empty:
        LOGGER.warning("No trusted events were written because the dataframe is empty.")
        return

    config = load_config()
    output_path = resolve_path(config["outputs"]["trusted_events_table"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)
    LOGGER.info("Wrote trusted events table to %s", output_path)


def main() -> None:
    """Run the trusted-layer transformation pipeline for synthetic, ASRS, NTSB, and BTS sources."""
    LOGGER.info("Starting main trusted-layer workflow.")

    trusted_asrs = build_asrs_trusted_reports()
    persist_asrs_trusted_reports(trusted_asrs)

    LOGGER.info("Starting NTSB trusted-layer pipeline.")
    trusted_ntsb = build_ntsb_trusted_investigations()
    persist_ntsb_trusted_investigations(trusted_ntsb)

    LOGGER.info("Starting BTS trusted-layer pipeline.")
    trusted_bts = build_bts_trusted_operations()
    persist_bts_trusted_operations(trusted_bts)

    trusted_events = build_trusted_events()
    persist_trusted_events(trusted_events)

    LOGGER.info("Completed main trusted-layer workflow.")


if __name__ == "__main__":
    main()
