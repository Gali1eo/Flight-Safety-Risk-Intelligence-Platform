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
NTSB_COLUMN_ALIASES = {
    "event_id": "ntsb_event_id",
    "event_date": "event_date",
    "airport_code": "airport_code",
    "air_carrier": "operator_name",
    "operator_name": "operator_name",
    "injury_severity": "injury_severity",
    "investigation_type": "event_type",
    "broad_phase_of_flight": "event_type",
    "aircraft_damage": "aircraft_damage",
}
NTSB_TRUSTED_OUTPUT_COLUMNS = [
    "ntsb_event_id",
    "event_date",
    "airport_code",
    "operator_name",
    "injury_severity",
    "event_type",
    "aircraft_damage",
    "source_system",
    "raw_file_name",
    "injury_severity_raw",
    "event_type_raw",
    "severity_normalized",
    "investigation_category",
]


def load_ntsb_raw() -> pd.DataFrame:
    """Load all raw NTSB CSV files from the configured raw folder."""
    source_files = discover_source_files("ntsb_investigations")
    if not source_files:
        raw_directory = resolve_path(load_config()["datasets"]["ntsb_investigations"]["path"])
        mdb_candidates = sorted(raw_directory.glob("*.mdb")) + sorted(raw_directory.glob("*.zip"))
        if mdb_candidates:
            LOGGER.warning(
                "NTSB MDB or ZIP files were found but direct MDB ingestion is not implemented in this project environment. "
                "Please extract an official CSV intermediate and place it in data/raw/ntsb_investigations."
            )
        else:
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


def standardize_ntsb_schema(frame: pd.DataFrame) -> pd.DataFrame:
    """Map real NTSB extract fields into the adapter's canonical schema where practical."""
    standardized = frame.copy()

    if "event_type" not in standardized.columns:
        for source_column in ["investigation_type", "broad_phase_of_flight"]:
            if source_column in standardized.columns:
                standardized["event_type"] = standardized[source_column]
                break

    if "operator_name" not in standardized.columns and "air_carrier" in standardized.columns:
        standardized["operator_name"] = standardized["air_carrier"]

    if "ntsb_event_id" not in standardized.columns and "event_id" in standardized.columns:
        standardized["ntsb_event_id"] = standardized["event_id"]

    return standardized


def drop_ntsb_rows_with_required_nulls(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop rows missing required NTSB values and report the count."""
    required_mask = frame[NTSB_NULL_CHECK_COLUMNS].notna().all(axis=1)
    dropped_rows = int((~required_mask).sum())
    cleaned = frame.loc[required_mask].reset_index(drop=True)
    return cleaned, dropped_rows


def drop_ntsb_rows_with_invalid_dates(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop rows with invalid event dates, filter to the pilot window, and standardize valid values."""
    trusted = frame.copy()
    parsed_dates = pd.to_datetime(trusted["event_date"], errors="coerce")
    invalid_date_rows = int(parsed_dates.isna().sum())

    trusted = trusted.loc[parsed_dates.notna()].copy()
    parsed_dates = parsed_dates.loc[parsed_dates.notna()]
    config = load_config()
    pilot_start = pd.Timestamp(config["project"]["pilot_window_start"])
    pilot_end = pd.Timestamp(config["project"]["pilot_window_end"])
    in_window_mask = parsed_dates.between(pilot_start, pilot_end)
    outside_window_rows = int((~in_window_mask).sum())
    if outside_window_rows:
        LOGGER.info("NTSB rows dropped outside pilot window: %s", outside_window_rows)

    trusted = trusted.loc[in_window_mask].copy()
    trusted["event_date"] = parsed_dates.loc[in_window_mask].dt.date.astype(str)
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
    trusted_ntsb = standardize_ntsb_schema(trusted_ntsb)
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
    config = load_config()
    output_path = resolve_path(config["outputs"]["trusted_ntsb_table"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if frame.empty:
        pd.DataFrame(columns=NTSB_TRUSTED_OUTPUT_COLUMNS).to_csv(output_path, index=False)
        LOGGER.warning(
            "No NTSB trusted output rows were available; wrote an empty trusted CSV to %s to avoid stale sample data.",
            output_path,
        )
        return

    frame.to_csv(output_path, index=False)
    LOGGER.info("NTSB trusted output path written: %s", output_path)


def main() -> None:
    """Run the trusted-layer adapter for NTSB aviation investigation files."""
    trusted_ntsb = build_ntsb_trusted_investigations()
    persist_ntsb_trusted_investigations(trusted_ntsb)


if __name__ == "__main__":
    main()
