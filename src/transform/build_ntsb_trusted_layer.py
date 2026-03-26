"""Trusted-layer adapter for public NTSB aviation investigation extracts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.common.config import load_config, resolve_path
from src.common.logging_utils import get_logger
from src.common.validation import standardize_columns, validate_required_columns


LOGGER = get_logger(__name__)

NTSB_SOURCE_FILES = {
    "events": "ntsb_events.csv",
    "aircraft": "ntsb_aircraft.csv",
    "injury": "ntsb_injury.csv",
}

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
    "NO INJURY": "no_injury",
    "NO_INJURY": "no_injury",
    "MINR": "minor_injury",
    "MINOR": "minor_injury",
    "SERS": "serious_injury",
    "SERIOUS": "serious_injury",
    "FATL": "fatal_injury",
    "FATAL": "fatal_injury",
}

EVENT_CATEGORY_NORMALIZATION_MAP = {
    "ACC": "accident",
    "ACCIDENT": "accident",
    "INC": "incident",
    "INCIDENT": "incident",
    "GROUND DAMAGE": "ground_event",
    "TURBULENCE INJURY": "in_flight_injury",
    "HARD LANDING": "landing_event",
    "MAINTENANCE ISSUE": "maintenance_event",
}

EVENT_TYPE_DISPLAY_MAP = {
    "ACC": "Accident",
    "ACCIDENT": "Accident",
    "INC": "Incident",
    "INCIDENT": "Incident",
}

AIRCRAFT_DAMAGE_NORMALIZATION_MAP = {
    "DEST": "destroyed",
    "DESTROYED": "destroyed",
    "MINR": "minor",
    "MINOR": "minor",
    "SUBS": "substantial",
    "SUBSTANTIAL": "substantial",
    "UNK": "unknown",
    "UNKNOWN": "unknown",
    "NONE": "none",
}

NTSB_INJURY_PRIORITY = {"NONE": 0, "MINR": 1, "SERS": 2, "FATL": 3}

NTSB_COLUMN_ALIASES = {
    "ev_id": "ntsb_event_id",
    "event_id": "ntsb_event_id",
    "ev_date": "event_date",
    "ev_type": "event_type",
    "investigation_type": "event_type",
    "broad_phase_of_flight": "event_type",
    "ev_highest_injury": "injury_severity",
    "injury_level": "injury_severity_from_injury",
    "ev_nr_apt_id": "airport_code",
    "airport_code": "airport_code",
    "oper_name": "operator_name",
    "air_carrier": "operator_name",
    "damage": "aircraft_damage",
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


def _first_non_empty(series: pd.Series) -> object:
    """Return the first non-empty, non-null value from a grouped series."""
    cleaned = series.dropna().astype(str).str.strip()
    cleaned = cleaned[cleaned.ne("")]
    if cleaned.empty:
        return pd.NA
    return cleaned.iloc[0]


def _load_ntsb_source_frame(file_path: Path) -> pd.DataFrame:
    """Load a single raw NTSB CSV file and standardize its column names."""
    if not file_path.exists():
        return pd.DataFrame()
    return standardize_columns(pd.read_csv(file_path, low_memory=False))


def _build_ntsb_aircraft_lookup(aircraft: pd.DataFrame) -> pd.DataFrame:
    """Collapse the aircraft extract to one row per NTSB event."""
    if aircraft.empty:
        return pd.DataFrame(columns=["ntsb_event_id", "operator_name", "aircraft_damage"])

    lookup = aircraft.loc[aircraft["ev_id"].notna()].copy()
    if lookup.empty:
        return pd.DataFrame(columns=["ntsb_event_id", "operator_name", "aircraft_damage"])

    lookup = lookup.groupby("ev_id", as_index=False).agg(
        operator_name=("oper_name", _first_non_empty),
        aircraft_damage=("damage", _first_non_empty),
    )
    lookup = lookup.rename(columns={"ev_id": "ntsb_event_id"})
    return lookup


def _build_ntsb_injury_lookup(injury: pd.DataFrame) -> pd.DataFrame:
    """Collapse the injury extract to a best-effort severity fallback per event."""
    if injury.empty:
        return pd.DataFrame(columns=["ntsb_event_id", "injury_severity_from_injury"])

    lookup = injury.loc[injury["ev_id"].notna()].copy()
    if lookup.empty:
        return pd.DataFrame(columns=["ntsb_event_id", "injury_severity_from_injury"])

    lookup["injury_level"] = lookup["injury_level"].astype("string").str.strip().str.upper()
    lookup["inj_person_count"] = pd.to_numeric(lookup["inj_person_count"], errors="coerce").fillna(0)
    lookup = lookup.loc[
        lookup["injury_level"].isin(NTSB_INJURY_PRIORITY) & (lookup["inj_person_count"] > 0)
    ].copy()
    if lookup.empty:
        return pd.DataFrame(columns=["ntsb_event_id", "injury_severity_from_injury"])

    lookup["severity_rank"] = lookup["injury_level"].map(NTSB_INJURY_PRIORITY)
    lookup = lookup.sort_values(
        ["ev_id", "severity_rank", "inj_person_count"],
        ascending=[True, True, False],
    )
    lookup = lookup.groupby("ev_id", as_index=False).tail(1)[["ev_id", "injury_level"]]
    lookup = lookup.rename(
        columns={"ev_id": "ntsb_event_id", "injury_level": "injury_severity_from_injury"}
    )
    return lookup


def _infer_no_injury_from_event_totals(frame: pd.DataFrame) -> pd.Series:
    """Flag rows whose event-level injury totals are all zero or blank."""
    injury_total_columns = [
        "inj_f_grnd",
        "inj_m_grnd",
        "inj_s_grnd",
        "inj_tot_f",
        "inj_tot_m",
        "inj_tot_n",
        "inj_tot_s",
        "inj_tot_t",
    ]
    available_columns = [column for column in injury_total_columns if column in frame.columns]
    if not available_columns:
        return pd.Series(False, index=frame.index)

    total_counts = pd.Series(0, index=frame.index, dtype="float64")
    for column in available_columns:
        total_counts = total_counts + pd.to_numeric(frame[column], errors="coerce").fillna(0)
    return total_counts.eq(0)


def load_ntsb_raw() -> pd.DataFrame:
    """Load and join the exported NTSB CSV intermediates at event grain."""
    config = load_config()
    raw_directory = resolve_path(config["datasets"]["ntsb_investigations"]["path"])
    events_path = raw_directory / NTSB_SOURCE_FILES["events"]
    aircraft_path = raw_directory / NTSB_SOURCE_FILES["aircraft"]
    injury_path = raw_directory / NTSB_SOURCE_FILES["injury"]

    if not events_path.exists():
        mdb_candidates = sorted(raw_directory.glob("*.mdb")) + sorted(raw_directory.glob("*.zip"))
        if mdb_candidates:
            LOGGER.warning(
                "NTSB MDB or ZIP files were found but direct MDB ingestion is not implemented in this project environment. "
                "Please extract an official CSV intermediate and place it in data/raw/ntsb_investigations."
            )
        else:
            LOGGER.warning("No raw NTSB files were found in data/raw/ntsb_investigations.")
        return pd.DataFrame()

    events = _load_ntsb_source_frame(events_path)
    aircraft = _load_ntsb_source_frame(aircraft_path)
    injury = _load_ntsb_source_frame(injury_path)

    if events.empty:
        LOGGER.warning("NTSB events CSV was found but did not contain any rows.")
        return pd.DataFrame()

    LOGGER.info(
        "NTSB source tables loaded: events=%s row(s), aircraft=%s row(s), injury=%s row(s)",
        len(events),
        len(aircraft),
        len(injury),
    )

    # Build the event-level trusted record from the split public tables.
    merged = events.copy()
    merged["ntsb_event_id"] = merged["ev_id"]
    merged["event_date"] = merged["ev_date"]
    merged["event_type"] = merged["ev_type"]
    merged["injury_severity"] = merged["ev_highest_injury"]
    merged["airport_code"] = merged["ev_nr_apt_id"]
    merged["source_system"] = "NTSB"
    merged["raw_file_name"] = "|".join(
        [path.name for path in [events_path, aircraft_path, injury_path] if path.exists()]
    )

    aircraft_lookup = _build_ntsb_aircraft_lookup(aircraft)
    if not aircraft_lookup.empty:
        merged = merged.merge(aircraft_lookup, on="ntsb_event_id", how="left")
    else:
        merged["operator_name"] = pd.NA
        merged["aircraft_damage"] = pd.NA

    injury_lookup = _build_ntsb_injury_lookup(injury)
    if not injury_lookup.empty:
        merged = merged.merge(injury_lookup, on="ntsb_event_id", how="left")
        merged["injury_severity"] = merged["injury_severity"].combine_first(
            merged["injury_severity_from_injury"]
        )
        merged = merged.drop(columns=["injury_severity_from_injury"])

    blank_severity_mask = merged["injury_severity"].isna() | (
        merged["injury_severity"].astype("string").str.strip() == ""
    )
    inferred_no_injury_mask = blank_severity_mask & _infer_no_injury_from_event_totals(merged)
    inferred_no_injury_rows = int(inferred_no_injury_mask.sum())
    if inferred_no_injury_rows:
        merged.loc[inferred_no_injury_mask, "injury_severity"] = "NONE"
        LOGGER.info(
            "NTSB rows inferred as no injury from zero injury totals: %s",
            inferred_no_injury_rows,
        )

    LOGGER.info("NTSB event-level rows prepared: %s", len(merged))
    return merged


def standardize_ntsb_schema(frame: pd.DataFrame) -> pd.DataFrame:
    """Map real NTSB extract fields into the adapter's canonical schema where practical."""
    standardized = frame.copy()

    for source_column, target_column in NTSB_COLUMN_ALIASES.items():
        if source_column not in standardized.columns:
            continue
        if target_column not in standardized.columns:
            standardized[target_column] = standardized[source_column]
        else:
            standardized[target_column] = standardized[target_column].combine_first(
                standardized[source_column]
            )

    if "source_system" not in standardized.columns:
        standardized["source_system"] = "NTSB"
    else:
        standardized["source_system"] = standardized["source_system"].fillna("NTSB")

    if "raw_file_name" not in standardized.columns:
        standardized["raw_file_name"] = "|".join(NTSB_SOURCE_FILES.values())
    else:
        standardized["raw_file_name"] = standardized["raw_file_name"].fillna(
            "|".join(NTSB_SOURCE_FILES.values())
        )

    for column in NTSB_NULL_CHECK_COLUMNS:
        if column in standardized.columns:
            standardized[column] = standardized[column].replace(r"^\s*$", pd.NA, regex=True)

    return standardized


def drop_ntsb_rows_with_required_nulls(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop rows missing required NTSB values and report the count."""
    required_values = frame[NTSB_NULL_CHECK_COLUMNS].replace(r"^\s*$", pd.NA, regex=True)
    required_mask = required_values.notna().all(axis=1)
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
    """Normalize investigation severity, event type, and aircraft damage values."""
    normalized = frame.copy()

    normalized["injury_severity_raw"] = normalized["injury_severity"]
    normalized["event_type_raw"] = normalized["event_type"]

    severity_source = normalized["injury_severity"].astype("string").str.strip().str.upper()
    severity_source = severity_source.replace({"": pd.NA})
    normalized["severity_normalized"] = severity_source.map(SEVERITY_NORMALIZATION_MAP).fillna(
        "other_or_unknown"
    )
    normalized["injury_severity"] = normalized["severity_normalized"]

    event_type_source = normalized["event_type"].astype("string").str.strip().str.upper()
    event_type_source = event_type_source.replace({"": pd.NA})
    normalized["event_type"] = event_type_source.map(EVENT_TYPE_DISPLAY_MAP).fillna(
        normalized["event_type"].astype("string").str.strip().str.title()
    )
    normalized["investigation_category"] = event_type_source.map(
        EVENT_CATEGORY_NORMALIZATION_MAP
    ).fillna("other_or_unknown")

    aircraft_damage_source = normalized["aircraft_damage"].astype("string").str.strip().str.upper()
    aircraft_damage_source = aircraft_damage_source.replace({"": pd.NA})
    normalized["aircraft_damage"] = aircraft_damage_source.map(
        AIRCRAFT_DAMAGE_NORMALIZATION_MAP
    ).fillna(
        normalized["aircraft_damage"].astype("string").str.strip().str.lower().str.replace(" ", "_")
    )
    normalized["aircraft_damage"] = normalized["aircraft_damage"].fillna("unknown")

    normalized["airport_code"] = (
        normalized["airport_code"]
        .astype("string")
        .str.strip()
        .replace({"": pd.NA})
        .fillna("UNKNOWN")
    )
    normalized["operator_name"] = (
        normalized["operator_name"]
        .astype("string")
        .str.strip()
        .replace({"": pd.NA})
        .fillna("UNKNOWN")
    )
    normalized["source_system"] = normalized["source_system"].fillna("NTSB")
    normalized["raw_file_name"] = normalized["raw_file_name"].fillna(
        "|".join(NTSB_SOURCE_FILES.values())
    )
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
        LOGGER.warning(
            "All NTSB rows were dropped during validation; no trusted NTSB output will be produced."
        )
        return trusted_ntsb

    trusted_ntsb = normalize_ntsb_fields(trusted_ntsb)
    trusted_ntsb = trusted_ntsb.reindex(columns=NTSB_TRUSTED_OUTPUT_COLUMNS)

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
