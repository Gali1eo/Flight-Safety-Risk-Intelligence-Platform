"""Trusted-layer adapter for public NASA ASRS report extracts."""

from __future__ import annotations

import pandas as pd

from src.common.config import load_config, resolve_path
from src.common.logging_utils import get_logger
from src.common.validation import standardize_columns, validate_required_columns
from src.ingest.ingest_datasets import discover_source_files


LOGGER = get_logger(__name__)

ASRS_REQUIRED_COLUMNS = [
    "report_id",
    "event_date",
    "anomaly",
    "human_factors",
    "narrative",
]
ASRS_NULL_CHECK_COLUMNS = ["report_id", "event_date", "anomaly", "human_factors"]
ASRS_DUPLICATE_KEYS = ["report_id"]


def load_asrs_raw() -> pd.DataFrame:
    """Load all raw ASRS CSV files from the configured raw folder."""
    source_files = discover_source_files("nasa_asrs")
    if not source_files:
        LOGGER.warning("No raw ASRS files were found.")
        return pd.DataFrame()

    frames = []
    for file_path in source_files:
        frame = pd.read_csv(file_path)
        frame["raw_file_name"] = file_path.name
        frames.append(frame)

    combined = pd.concat(frames, ignore_index=True)
    LOGGER.info("Loaded %s ASRS row(s) from %s file(s)", len(combined), len(source_files))
    return combined


def validate_asrs_required_nulls(frame: pd.DataFrame) -> None:
    """Validate that core ASRS fields are populated."""
    null_summary = {
        column: int(frame[column].isna().sum())
        for column in ASRS_NULL_CHECK_COLUMNS
        if column in frame.columns
    }
    failing = {column: count for column, count in null_summary.items() if count > 0}
    if failing:
        raise ValueError(f"Core ASRS fields contain nulls: {failing}")


def coerce_and_validate_dates(frame: pd.DataFrame) -> pd.DataFrame:
    """Parse event dates and raise if invalid values are found."""
    trusted = frame.copy()
    trusted["event_date"] = pd.to_datetime(trusted["event_date"], errors="coerce")

    invalid_date_rows = trusted["event_date"].isna().sum()
    if invalid_date_rows:
        raise ValueError(f"Found {int(invalid_date_rows)} ASRS row(s) with invalid event_date values")

    trusted["event_date"] = trusted["event_date"].dt.date.astype(str)
    return trusted


def deduplicate_asrs_reports(frame: pd.DataFrame) -> pd.DataFrame:
    """Drop duplicate ASRS reports using the report identifier."""
    duplicate_count = int(frame.duplicated(subset=ASRS_DUPLICATE_KEYS).sum())
    if duplicate_count:
        LOGGER.warning(
            "Dropping %s duplicate ASRS row(s) using keys %s.",
            duplicate_count,
            ASRS_DUPLICATE_KEYS,
        )
        return frame.drop_duplicates(subset=ASRS_DUPLICATE_KEYS).reset_index(drop=True)
    return frame


def build_asrs_trusted_reports() -> pd.DataFrame:
    """Build a trusted ASRS table from public raw report extracts."""
    raw_asrs = load_asrs_raw()
    if raw_asrs.empty:
        return raw_asrs

    trusted_asrs = standardize_columns(raw_asrs)
    validate_required_columns(trusted_asrs, ASRS_REQUIRED_COLUMNS)
    trusted_asrs = deduplicate_asrs_reports(trusted_asrs)
    trusted_asrs = coerce_and_validate_dates(trusted_asrs)
    validate_asrs_required_nulls(trusted_asrs)

    trusted_asrs["location"] = trusted_asrs["location"].fillna("UNKNOWN")
    trusted_asrs["aircraft_operator"] = trusted_asrs["aircraft_operator"].fillna(
        "UNKNOWN"
    )
    trusted_asrs["narrative_privacy_note"] = (
        "Narratives are preserved in the trusted layer for analysis, but downstream "
        "analytics should minimize exposure and avoid broad audience access."
    )

    LOGGER.info(
        "Built trusted ASRS table with %s row(s) and %s column(s)",
        len(trusted_asrs),
        len(trusted_asrs.columns),
    )
    return trusted_asrs


def persist_asrs_trusted_reports(frame: pd.DataFrame) -> None:
    """Persist the trusted ASRS report table as CSV."""
    if frame.empty:
        LOGGER.warning("No ASRS trusted output was written because the dataframe is empty.")
        return

    config = load_config()
    output_path = resolve_path(config["outputs"]["trusted_asrs_table"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)
    LOGGER.info("Wrote trusted ASRS reports to %s", output_path)


def main() -> None:
    """Run the trusted-layer adapter for NASA ASRS files."""
    trusted_asrs = build_asrs_trusted_reports()
    persist_asrs_trusted_reports(trusted_asrs)


if __name__ == "__main__":
    main()
