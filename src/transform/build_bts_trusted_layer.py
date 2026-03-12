"""Trusted-layer adapter for public BTS On-Time / Delay operational extracts."""

from __future__ import annotations

import pandas as pd

from src.common.config import load_config, resolve_path
from src.common.logging_utils import get_logger
from src.common.validation import standardize_columns, validate_required_columns
from src.ingest.ingest_datasets import discover_source_files


LOGGER = get_logger(__name__)

BTS_REQUIRED_COLUMNS = [
    "flight_date",
    "reporting_airline",
    "flight_number",
    "origin",
    "dest",
    "cancelled",
    "diverted",
]
BTS_NULL_CHECK_COLUMNS = [
    "flight_date",
    "reporting_airline",
    "flight_number",
    "origin",
    "dest",
    "cancelled",
    "diverted",
]
BTS_DUPLICATE_KEYS = ["flight_date", "reporting_airline", "flight_number", "origin", "dest"]


def load_bts_raw() -> pd.DataFrame:
    """Load all raw BTS CSV files from the configured raw folder."""
    source_files = discover_source_files("bts_on_time")
    if not source_files:
        LOGGER.warning("No raw BTS files were found in data/raw/bts_on_time.")
        return pd.DataFrame()

    LOGGER.info(
        "BTS files discovered: %s",
        ", ".join(file_path.name for file_path in source_files),
    )

    frames = []
    for file_path in source_files:
        frame = pd.read_csv(file_path)
        frame["raw_file_name"] = file_path.name
        frames.append(frame)

    combined = pd.concat(frames, ignore_index=True)
    LOGGER.info("BTS rows loaded: %s", len(combined))
    return combined


def drop_bts_rows_with_required_nulls(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop rows missing required BTS values and report the count."""
    required_mask = frame[BTS_NULL_CHECK_COLUMNS].notna().all(axis=1)
    dropped_rows = int((~required_mask).sum())
    cleaned = frame.loc[required_mask].reset_index(drop=True)
    return cleaned, dropped_rows


def drop_bts_rows_with_invalid_dates(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop rows with invalid flight dates and standardize valid values."""
    trusted = frame.copy()
    parsed_dates = pd.to_datetime(trusted["flight_date"], errors="coerce")
    invalid_date_rows = int(parsed_dates.isna().sum())

    trusted = trusted.loc[parsed_dates.notna()].copy()
    trusted["flight_date"] = parsed_dates.loc[parsed_dates.notna()].dt.date.astype(str)
    trusted = trusted.reset_index(drop=True)
    return trusted, invalid_date_rows


def deduplicate_bts_flights(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop duplicate BTS operational rows using a flight-leg style key."""
    duplicate_count = int(frame.duplicated(subset=BTS_DUPLICATE_KEYS).sum())
    deduplicated = frame.drop_duplicates(subset=BTS_DUPLICATE_KEYS).reset_index(drop=True)
    return deduplicated, duplicate_count


def normalize_indicator(series: pd.Series) -> pd.Series:
    """Normalize cancellation or diversion indicators to 0/1 integers."""
    numeric = pd.to_numeric(series, errors="coerce").fillna(0)
    return numeric.clip(lower=0, upper=1).astype(int)


def normalize_airport_code(series: pd.Series) -> pd.Series:
    """Normalize airport codes for trusted-layer consistency."""
    return series.astype(str).str.strip().str.upper()


def normalize_carrier(series: pd.Series) -> pd.Series:
    """Normalize carrier codes for trusted-layer consistency."""
    return series.astype(str).str.strip().str.upper()


def normalize_bts_fields(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize core operational fields for downstream analysis."""
    normalized = frame.copy()

    normalized["carrier"] = normalize_carrier(normalized["reporting_airline"])
    normalized["origin_airport"] = normalize_airport_code(normalized["origin"])
    normalized["destination_airport"] = normalize_airport_code(normalized["dest"])
    normalized["route"] = (
        normalized["origin_airport"] + "_" + normalized["destination_airport"]
    )

    normalized["departure_delay_minutes"] = pd.to_numeric(
        normalized.get("dep_delay"), errors="coerce"
    )
    normalized["arrival_delay_minutes"] = pd.to_numeric(
        normalized.get("arr_delay"), errors="coerce"
    )
    normalized["cancelled_flag"] = normalize_indicator(normalized["cancelled"])
    normalized["diverted_flag"] = normalize_indicator(normalized["diverted"])
    normalized["operational_status"] = "completed"
    normalized.loc[normalized["cancelled_flag"] == 1, "operational_status"] = "cancelled"
    normalized.loc[
        (normalized["cancelled_flag"] == 0) & (normalized["diverted_flag"] == 1),
        "operational_status",
    ] = "diverted"

    normalized["flight_number"] = normalized["flight_number"].astype(str).str.strip()
    return normalized


def build_bts_trusted_operations() -> pd.DataFrame:
    """Build a trusted BTS operational table from public on-time extracts."""
    raw_bts = load_bts_raw()
    if raw_bts.empty:
        return raw_bts

    trusted_bts = standardize_columns(raw_bts)
    validate_required_columns(trusted_bts, BTS_REQUIRED_COLUMNS)

    trusted_bts, duplicate_rows_dropped = deduplicate_bts_flights(trusted_bts)
    LOGGER.info("BTS rows dropped for duplicates: %s", duplicate_rows_dropped)

    trusted_bts, null_rows_dropped = drop_bts_rows_with_required_nulls(trusted_bts)
    LOGGER.info("BTS rows dropped for required nulls: %s", null_rows_dropped)

    trusted_bts, invalid_date_rows_dropped = drop_bts_rows_with_invalid_dates(trusted_bts)
    LOGGER.info("BTS rows dropped for invalid dates: %s", invalid_date_rows_dropped)

    if trusted_bts.empty:
        LOGGER.warning("All BTS rows were dropped during validation; no trusted BTS output will be produced.")
        return trusted_bts

    trusted_bts = normalize_bts_fields(trusted_bts)

    LOGGER.info(
        "Built trusted BTS table with %s row(s) and %s column(s)",
        len(trusted_bts),
        len(trusted_bts.columns),
    )
    return trusted_bts


def persist_bts_trusted_operations(frame: pd.DataFrame) -> None:
    """Persist the trusted BTS operations table as CSV."""
    if frame.empty:
        LOGGER.warning("No BTS trusted output was written because the dataframe is empty.")
        return

    config = load_config()
    output_path = resolve_path(config["outputs"]["trusted_bts_table"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)
    LOGGER.info("BTS trusted output path written: %s", output_path)


def main() -> None:
    """Run the trusted-layer adapter for BTS On-Time / Delay files."""
    trusted_bts = build_bts_trusted_operations()
    persist_bts_trusted_operations(trusted_bts)


if __name__ == "__main__":
    main()
