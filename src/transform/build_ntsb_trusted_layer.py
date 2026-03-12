"""Trusted-layer adapter for public NTSB aviation investigation extracts."""

from __future__ import annotations

import pandas as pd

from src.common.config import load_config, resolve_path
from src.common.logging_utils import get_logger
from src.common.validation import standardize_columns, validate_required_columns
from src.ingest.ingest_datasets import discover_source_files


LOGGER = get_logger(__name__)

NTSB_REQUIRED_COLUMNS = [
    "ntsb_event_id",
    "event_date",
    "injury_severity",
    "event_type",
]
NTSB_NULL_CHECK_COLUMNS = ["ntsb_event_id", "event_date", "injury_severity", "event_type"]
NTSB_DUPLICATE_KEYS = ["ntsb_event_id"]

SEVERITY_NORMALIZATION_MAP = {
    "NONE": "no_injury",
    "MINOR": "minor_injury",
    "SERIOUS": "serious_injury",
    "FATAL": "fatal_injury",
}

EVENT_CATEGORY_NORMALIZATION_MAP = {
    "GROUND DAMAGE": "ground_event",
    "TURBULENCE INJURY": "in_flight_injury",
    "HARD LANDING": "landing_event",
    "MAINTENANCE ISSUE": "maintenance_event",
}


def load_ntsb_raw() -> pd.DataFrame:
    """Load all raw NTSB CSV files from the configured raw folder."""
    source_files = discover_source_files("ntsb_investigations")
    if not source_files:
        LOGGER.warning("No raw NTSB files were found in data/raw/ntsb_investigations.")
        return pd.DataFrame()

    LOGGER.info(
        "NTSB files discovered: %s",
        ", ".join(file_path.name for file_path in source_files),
    )

    frames = []
    for file_path in source_files:
        frame = pd.read_csv(file_path)
        frame["raw_file_name"] = file_path.name
        frames.append(frame)

    combined = pd.concat(frames, ignore_index=True)
    LOGGER.info("NTSB rows loaded: %s", len(combined))
    return combined


def drop_ntsb_rows_with_required_nulls(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop rows missing required NTSB values and report the count."""
    required_mask = frame[NTSB_NULL_CHECK_COLUMNS].notna().all(axis=1)
    dropped_rows = int((~required_mask).sum())
    cleaned = frame.loc[required_mask].reset_index(drop=True)
    return cleaned, dropped_rows


def drop_ntsb_rows_with_invalid_dates(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop rows with invalid event dates and standardize valid values."""
    trusted = frame.copy()
    parsed_dates = pd.to_datetime(trusted["event_date"], errors="coerce")
    invalid_date_rows = int(parsed_dates.isna().sum())

    trusted = trusted.loc[parsed_dates.notna()].copy()
    trusted["event_date"] = parsed_dates.loc[parsed_dates.notna()].dt.date.astype(str)
    trusted = trusted.reset_index(drop=True)
    return trusted, invalid_date_rows


def deduplicate_ntsb_events(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop duplicate NTSB investigations using the event identifier."""
    duplicate_count = int(frame.duplicated(subset=NTSB_DUPLICATE_KEYS).sum())
    deduplicated = frame.drop_duplicates(subset=NTSB_DUPLICATE_KEYS).reset_index(drop=True)
    return deduplicated, duplicate_count


def normalize_ntsb_fields(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize investigation severity and event category values."""
    normalized = frame.copy()
    severity_upper = normalized["injury_severity"].astype(str).str.strip().str.upper()
    category_upper = normalized["event_type"].astype(str).str.strip().str.upper()

    normalized["injury_severity_raw"] = normalized["injury_severity"]
    normalized["event_type_raw"] = normalized["event_type"]
    normalized["severity_normalized"] = severity_upper.map(SEVERITY_NORMALIZATION_MAP).fillna(
        "other_or_unknown"
    )
    normalized["investigation_category"] = category_upper.map(
        EVENT_CATEGORY_NORMALIZATION_MAP
    ).fillna("other_or_unknown")

    normalized["injury_severity"] = severity_upper.str.lower().str.replace(" ", "_")
    normalized["event_type"] = category_upper.str.title()

    normalized["airport_code"] = normalized["airport_code"].fillna("UNKNOWN")
    normalized["operator_name"] = normalized["operator_name"].fillna("UNKNOWN")
    normalized["aircraft_damage"] = normalized["aircraft_damage"].fillna("UNKNOWN")
    return normalized


def build_ntsb_trusted_investigations() -> pd.DataFrame:
    """Build a trusted NTSB table from public investigation extracts."""
    raw_ntsb = load_ntsb_raw()
    if raw_ntsb.empty:
        return raw_ntsb

    trusted_ntsb = standardize_columns(raw_ntsb)
    validate_required_columns(trusted_ntsb, NTSB_REQUIRED_COLUMNS)

    trusted_ntsb, duplicate_rows_dropped = deduplicate_ntsb_events(trusted_ntsb)
    LOGGER.info("NTSB rows dropped for duplicates: %s", duplicate_rows_dropped)

    trusted_ntsb, null_rows_dropped = drop_ntsb_rows_with_required_nulls(trusted_ntsb)
    LOGGER.info("NTSB rows dropped for required nulls: %s", null_rows_dropped)

    trusted_ntsb, invalid_date_rows_dropped = drop_ntsb_rows_with_invalid_dates(trusted_ntsb)
    LOGGER.info("NTSB rows dropped for invalid dates: %s", invalid_date_rows_dropped)

    if trusted_ntsb.empty:
        LOGGER.warning("All NTSB rows were dropped during validation; no trusted NTSB output will be produced.")
        return trusted_ntsb

    trusted_ntsb = normalize_ntsb_fields(trusted_ntsb)

    LOGGER.info(
        "Built trusted NTSB table with %s row(s) and %s column(s)",
        len(trusted_ntsb),
        len(trusted_ntsb.columns),
    )
    return trusted_ntsb


def persist_ntsb_trusted_investigations(frame: pd.DataFrame) -> None:
    """Persist the trusted NTSB investigations table as CSV."""
    if frame.empty:
        LOGGER.warning("No NTSB trusted output was written because the dataframe is empty.")
        return

    config = load_config()
    output_path = resolve_path(config["outputs"]["trusted_ntsb_table"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)
    LOGGER.info("NTSB trusted output path written: %s", output_path)


def main() -> None:
    """Run the trusted-layer adapter for NTSB aviation investigation files."""
    trusted_ntsb = build_ntsb_trusted_investigations()
    persist_ntsb_trusted_investigations(trusted_ntsb)


if __name__ == "__main__":
    main()
