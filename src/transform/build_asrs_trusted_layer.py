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
ASRS_CANONICAL_COLUMN_MAP = {
    "acn": "report_id",
    "time_date": "event_date",
    "place_locale_reference": "location",
    "aircraft_1_aircraft_operator": "aircraft_operator",
    "events_anomaly": "anomaly",
    "person_1_human_factors": "human_factors",
    "report_1_narrative": "narrative",
    "report_1_synopsis": "narrative_synopsis",
}


def _flatten_asrs_headers(top_row: list[str], bottom_row: list[str]) -> list[str]:
    """Flatten the NASA ASRS two-row export header into single snake_case names."""
    flattened_headers = []
    for left, right in zip(top_row, bottom_row):
        left = left.strip()
        right = right.strip()
        if left and right:
            flattened_headers.append(f"{left}_{right}")
        else:
            flattened_headers.append(left or right)
    return flattened_headers


def load_asrs_export_file(file_path: str) -> pd.DataFrame:
    """Load a NASA ASRS CSV export that uses a two-row header and blank separator row."""
    frame = pd.read_csv(file_path, header=None, dtype=str)
    if len(frame) < 3:
        return pd.DataFrame()

    top_row = frame.iloc[0].fillna("").astype(str).tolist()
    bottom_row = frame.iloc[1].fillna("").astype(str).tolist()
    flattened_headers = _flatten_asrs_headers(top_row, bottom_row)

    data = frame.iloc[3:].copy()
    data.columns = flattened_headers
    data = data.dropna(how="all").reset_index(drop=True)
    return data


def load_asrs_raw() -> pd.DataFrame:
    """Load all raw ASRS CSV files from the configured raw folder."""
    source_files = discover_source_files("nasa_asrs")
    if not source_files:
        LOGGER.warning("No raw ASRS files were found in data/raw/nasa_asrs.")
        return pd.DataFrame()

    LOGGER.info(
        "ASRS files discovered: %s",
        ", ".join(file_path.name for file_path in source_files),
    )

    frames = []
    for file_path in source_files:
        frame = load_asrs_export_file(file_path)
        frame["raw_file_name"] = file_path.name
        frames.append(frame)

    combined = pd.concat(frames, ignore_index=True)
    LOGGER.info("ASRS rows loaded: %s", len(combined))
    return combined


def standardize_asrs_schema(frame: pd.DataFrame) -> pd.DataFrame:
    """Map real NASA ASRS export fields into the adapter's canonical schema."""
    standardized = frame.copy()
    rename_map = {
        source: target
        for source, target in ASRS_CANONICAL_COLUMN_MAP.items()
        if source in standardized.columns and target not in standardized.columns
    }
    standardized = standardized.rename(columns=rename_map)

    if "narrative" not in standardized.columns and "narrative_synopsis" in standardized.columns:
        standardized["narrative"] = standardized["narrative_synopsis"]

    if "narrative" in standardized.columns and "narrative_synopsis" in standardized.columns:
        standardized["narrative"] = standardized["narrative"].fillna("").replace("", pd.NA)
        standardized["narrative"] = standardized["narrative"].fillna(
            standardized["narrative_synopsis"]
        )

    if "source_system" not in standardized.columns:
        standardized["source_system"] = "NASA_ASRS"

    return standardized


def drop_asrs_rows_with_required_nulls(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop rows missing required ASRS values and report the count."""
    required_mask = frame[ASRS_NULL_CHECK_COLUMNS].notna().all(axis=1)
    dropped_rows = int((~required_mask).sum())
    cleaned = frame.loc[required_mask].reset_index(drop=True)
    return cleaned, dropped_rows


def drop_asrs_rows_with_invalid_dates(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop rows with invalid event dates, filter to the pilot window, and standardize valid values."""
    trusted = frame.copy()
    event_date_text = trusted["event_date"].astype(str).str.strip()
    parsed_dates = pd.to_datetime(event_date_text, format="%Y%m", errors="coerce")
    missing_mask = parsed_dates.isna()
    if missing_mask.any():
        parsed_dates.loc[missing_mask] = pd.to_datetime(
            event_date_text.loc[missing_mask], errors="coerce"
        )
    invalid_date_rows = int(parsed_dates.isna().sum())

    trusted = trusted.loc[parsed_dates.notna()].copy()
    parsed_dates = parsed_dates.loc[parsed_dates.notna()]
    config = load_config()
    pilot_start = pd.Timestamp(config["project"]["pilot_window_start"])
    pilot_end = pd.Timestamp(config["project"]["pilot_window_end"])
    in_window_mask = parsed_dates.between(pilot_start, pilot_end)
    outside_window_rows = int((~in_window_mask).sum())
    if outside_window_rows:
        LOGGER.info("ASRS rows dropped outside pilot window: %s", outside_window_rows)

    trusted = trusted.loc[in_window_mask].copy()
    trusted["event_date"] = parsed_dates.loc[in_window_mask].dt.date.astype(str)
    trusted = trusted.reset_index(drop=True)
    return trusted, invalid_date_rows


def deduplicate_asrs_reports(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop duplicate ASRS reports using the report identifier."""
    duplicate_count = int(frame.duplicated(subset=ASRS_DUPLICATE_KEYS).sum())
    deduplicated = frame.drop_duplicates(subset=ASRS_DUPLICATE_KEYS).reset_index(drop=True)
    return deduplicated, duplicate_count


def build_asrs_trusted_reports() -> pd.DataFrame:
    """Build a trusted ASRS table from public raw report extracts."""
    raw_asrs = load_asrs_raw()
    if raw_asrs.empty:
        return raw_asrs

    trusted_asrs = standardize_columns(raw_asrs)
    trusted_asrs = standardize_asrs_schema(trusted_asrs)
    validate_required_columns(trusted_asrs, ASRS_REQUIRED_COLUMNS)

    trusted_asrs, duplicate_rows_dropped = deduplicate_asrs_reports(trusted_asrs)
    LOGGER.info("ASRS rows dropped for duplicates: %s", duplicate_rows_dropped)

    trusted_asrs, null_rows_dropped = drop_asrs_rows_with_required_nulls(trusted_asrs)
    LOGGER.info("ASRS rows dropped for required nulls: %s", null_rows_dropped)

    trusted_asrs, invalid_date_rows_dropped = drop_asrs_rows_with_invalid_dates(trusted_asrs)
    LOGGER.info("ASRS rows dropped for invalid dates: %s", invalid_date_rows_dropped)

    if trusted_asrs.empty:
        LOGGER.warning("All ASRS rows were dropped during validation; no trusted ASRS output will be produced.")
        return trusted_asrs

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
    LOGGER.info("ASRS trusted output path written: %s", output_path)


def main() -> None:
    """Run the trusted-layer adapter for NASA ASRS files."""
    trusted_asrs = build_asrs_trusted_reports()
    persist_asrs_trusted_reports(trusted_asrs)


if __name__ == "__main__":
    main()
