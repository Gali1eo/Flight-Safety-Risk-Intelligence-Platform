"""Build integrated analytics marts for Tableau-ready storytelling outputs."""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd

from src.common.config import load_config, resolve_path
from src.common.logging_utils import get_logger
from src.common.validation import standardize_columns


LOGGER = get_logger(__name__)

MONTHLY_RISK_OVERVIEW_COLUMNS = [
    "report_month",
    "airport",
    "region",
    "operational_flight_legs",
    "cancelled_flights",
    "diverted_flights",
    "avg_departure_delay_minutes",
    "avg_arrival_delay_minutes",
    "asrs_report_count",
    "fatigue_related_report_count",
    "ntsb_investigation_count",
    "serious_or_higher_investigation_count",
    "avg_training_completion_rate",
    "avg_safety_engagement_score",
    "fatigue_training_completion_rate",
    "synthetic_elevated_risk_count",
    "data_basis",
]
FATIGUE_THEME_TRENDS_COLUMNS = [
    "report_month",
    "airport",
    "carrier",
    "region",
    "human_factor_theme",
    "fatigue_related_flag",
    "report_count",
    "unique_anomaly_count",
    "data_basis",
]
INVESTIGATION_TRENDS_COLUMNS = [
    "report_month",
    "airport",
    "operator_group",
    "region",
    "investigation_category",
    "severity_normalized",
    "investigation_count",
    "serious_or_higher_count",
    "data_basis",
]
OPERATIONAL_DISRUPTION_SUMMARY_COLUMNS = [
    "report_month",
    "carrier",
    "origin_airport",
    "destination_airport",
    "route",
    "region",
    "flight_leg_count",
    "cancelled_flight_count",
    "diverted_flight_count",
    "avg_departure_delay_minutes",
    "avg_arrival_delay_minutes",
    "cancellation_rate",
    "diversion_rate",
    "data_basis",
]
SAFETY_PROMOTION_SUMMARY_COLUMNS = [
    "report_month",
    "state",
    "region",
    "topic",
    "audience_type",
    "event_count",
    "data_basis",
]

AIRPORT_REGION_MAP = {
    "ATL": "Southeast",
    "BOS": "Northeast",
    "DAL": "South",
    "DTW": "Midwest",
    "HOU": "South",
    "JFK": "Northeast",
    "LAX": "West",
    "MSP": "Midwest",
    "SEA": "West",
    "SLC": "West",
    "UNKNOWN": "Unknown",
}

STATE_REGION_MAP = {
    "GA": "Southeast",
    "MI": "Midwest",
    "WA": "West",
    "TX": "South",
}

CARRIER_GROUP_MAP = {
    "DELTA AIR LINES": "DL",
    "DELTA CONNECTION": "DL",
    "SKYWEST AIRLINES": "OO",
    "SOUTHWEST AIRLINES": "WN",
    "UNKNOWN": "UNKNOWN",
}


def load_csv_output(path_key: str) -> pd.DataFrame:
    """Load a configured CSV output or return an empty dataframe with a warning."""
    config = load_config()
    file_path = resolve_path(config["outputs"][path_key])
    if not file_path.exists():
        LOGGER.warning("Expected input file was not found at %s", file_path)
        return pd.DataFrame()
    return pd.read_csv(file_path, low_memory=False)


def load_raw_dataset(dataset_name: str) -> pd.DataFrame:
    """Load raw source files for analytics summaries that do not yet have trusted adapters."""
    config = load_config()
    dataset_path = resolve_path(config["datasets"][dataset_name]["path"])
    source_files = sorted(dataset_path.glob("*.csv"))
    if not source_files:
        LOGGER.warning("No raw files were found for dataset '%s' in %s", dataset_name, dataset_path)
        return pd.DataFrame()
    frames = [pd.read_csv(file_path, low_memory=False) for file_path in source_files]
    return standardize_columns(pd.concat(frames, ignore_index=True))


def add_month_column(frame: pd.DataFrame, date_column: str, month_column: str = "report_month") -> pd.DataFrame:
    """Add a normalized YYYY-MM month column from a date field."""
    enriched = frame.copy()
    enriched[date_column] = pd.to_datetime(enriched[date_column], errors="coerce")
    enriched = enriched.loc[enriched[date_column].notna()].copy()
    enriched[month_column] = enriched[date_column].dt.to_period("M").astype(str)
    return enriched


def map_airport_region(series: pd.Series) -> pd.Series:
    """Map airport codes to a lightweight region dimension for portfolio storytelling."""
    normalized = series.fillna("UNKNOWN").astype(str).str.strip().str.upper()
    return normalized.map(AIRPORT_REGION_MAP).fillna("Unknown")


def map_state_region(series: pd.Series) -> pd.Series:
    """Map state codes to a region dimension for FAASTeam summaries."""
    normalized = series.fillna("UNKNOWN").astype(str).str.strip().str.upper()
    return normalized.map(STATE_REGION_MAP).fillna("Unknown")


def map_operator_to_carrier(series: pd.Series) -> pd.Series:
    """Map operator names to coarse carrier groups where reasonable."""
    normalized = series.fillna("UNKNOWN").astype(str).str.strip().str.upper()
    return normalized.map(CARRIER_GROUP_MAP).fillna("OTHER_PUBLIC_OPERATOR")


def build_operational_disruption_summary(bts: pd.DataFrame) -> pd.DataFrame:
    """Summarize BTS operational disruption signals by month, carrier, airport, and route."""
    if bts.empty:
        return pd.DataFrame(columns=OPERATIONAL_DISRUPTION_SUMMARY_COLUMNS)

    operations = add_month_column(bts, "flight_date")
    operations["region"] = map_airport_region(operations["origin_airport"])

    summary = (
        operations.groupby(
            ["report_month", "carrier", "origin_airport", "destination_airport", "route", "region"],
            dropna=False,
        )
        .agg(
            flight_leg_count=("flight_number", "count"),
            cancelled_flight_count=("cancelled_flag", "sum"),
            diverted_flight_count=("diverted_flag", "sum"),
            avg_departure_delay_minutes=("departure_delay_minutes", "mean"),
            avg_arrival_delay_minutes=("arrival_delay_minutes", "mean"),
        )
        .reset_index()
    )
    summary["cancellation_rate"] = (
        summary["cancelled_flight_count"] / summary["flight_leg_count"]
    ).round(4)
    summary["diversion_rate"] = (
        summary["diverted_flight_count"] / summary["flight_leg_count"]
    ).round(4)
    summary["data_basis"] = "Public BTS On-Time / Delay data used as an operational proxy, not FOQA."
    return summary


def build_fatigue_theme_trends(asrs: pd.DataFrame) -> pd.DataFrame:
    """Summarize ASRS fatigue and human-factor themes for monthly trend analysis."""
    if asrs.empty:
        return pd.DataFrame(columns=FATIGUE_THEME_TRENDS_COLUMNS)

    reports = add_month_column(asrs, "event_date")
    reports["airport"] = reports["location"].fillna("UNKNOWN").astype(str).str.strip().str.upper()
    reports["carrier"] = map_operator_to_carrier(reports["aircraft_operator"])
    reports["region"] = map_airport_region(reports["airport"])
    reports["human_factor_theme"] = (
        reports["human_factors"].fillna("UNKNOWN").astype(str).str.strip().str.lower().str.replace(" ", "_")
    )
    reports["fatigue_related_flag"] = reports["human_factor_theme"].str.contains("fatigue", na=False).astype(int)

    summary = (
        reports.groupby(
            ["report_month", "airport", "carrier", "region", "human_factor_theme", "fatigue_related_flag"],
            dropna=False,
        )
        .agg(
            report_count=("report_id", "count"),
            unique_anomaly_count=("anomaly", pd.Series.nunique),
        )
        .reset_index()
    )
    summary["data_basis"] = "Public NASA ASRS reports used as a voluntary safety-report and fatigue proxy, not ASAP."
    return summary


def build_investigation_trends(ntsb: pd.DataFrame) -> pd.DataFrame:
    """Summarize NTSB investigation activity and severity by month and airport."""
    if ntsb.empty:
        return pd.DataFrame(columns=INVESTIGATION_TRENDS_COLUMNS)

    investigations = add_month_column(ntsb, "event_date")
    investigations["airport"] = investigations["airport_code"].fillna("UNKNOWN").astype(str).str.strip().str.upper()
    investigations["operator_group"] = map_operator_to_carrier(investigations["operator_name"])
    investigations["region"] = map_airport_region(investigations["airport"])
    investigations["serious_or_higher_flag"] = investigations["severity_normalized"].isin(
        ["serious_injury", "fatal_injury"]
    ).astype(int)

    summary = (
        investigations.groupby(
            [
                "report_month",
                "airport",
                "operator_group",
                "region",
                "investigation_category",
                "severity_normalized",
            ],
            dropna=False,
        )
        .agg(
            investigation_count=("ntsb_event_id", "count"),
            serious_or_higher_count=("serious_or_higher_flag", "sum"),
        )
        .reset_index()
    )
    summary["data_basis"] = "Public NTSB investigations used as external investigation context, not an internal SMS system."
    return summary


def build_safety_promotion_summary(faasteam: pd.DataFrame) -> pd.DataFrame:
    """Summarize FAASTeam public safety-promotion events for portfolio dashboards."""
    if faasteam.empty:
        return pd.DataFrame(columns=SAFETY_PROMOTION_SUMMARY_COLUMNS)

    events = add_month_column(faasteam, "event_date")
    events["state"] = events["state"].fillna("UNKNOWN").astype(str).str.strip().str.upper()
    events["region"] = map_state_region(events["state"])
    events["topic"] = events["topic"].fillna("UNKNOWN").astype(str).str.strip()
    events["audience_type"] = events["audience_type"].fillna("UNKNOWN").astype(str).str.strip()

    summary = (
        events.groupby(["report_month", "state", "region", "topic", "audience_type"], dropna=False)
        .agg(event_count=("event_id", "count"))
        .reset_index()
    )
    summary["data_basis"] = "Public FAASTeam event listings used as a safety-promotion proxy, not internal training completion data."
    return summary


def build_monthly_risk_overview(
    bts: pd.DataFrame, asrs: pd.DataFrame, ntsb: pd.DataFrame, culture: pd.DataFrame
) -> pd.DataFrame:
    """Create an integrated monthly airport-level overview from trusted public and synthetic sources."""
    frames: list[pd.DataFrame] = []

    if not bts.empty:
        operations = add_month_column(bts, "flight_date")
        operations["airport"] = operations["origin_airport"]
        operations["region"] = map_airport_region(operations["airport"])
        bts_summary = (
            operations.groupby(["report_month", "airport", "region"], dropna=False)
            .agg(
                operational_flight_legs=("flight_number", "count"),
                cancelled_flights=("cancelled_flag", "sum"),
                diverted_flights=("diverted_flag", "sum"),
                avg_departure_delay_minutes=("departure_delay_minutes", "mean"),
                avg_arrival_delay_minutes=("arrival_delay_minutes", "mean"),
            )
            .reset_index()
        )
        frames.append(bts_summary)

    if not asrs.empty:
        reports = add_month_column(asrs, "event_date")
        reports["airport"] = reports["location"].fillna("UNKNOWN").astype(str).str.strip().str.upper()
        reports["region"] = map_airport_region(reports["airport"])
        reports["fatigue_related_flag"] = reports["human_factors"].fillna("").str.contains(
            "fatigue", case=False, na=False
        ).astype(int)
        asrs_summary = (
            reports.groupby(["report_month", "airport", "region"], dropna=False)
            .agg(
                asrs_report_count=("report_id", "count"),
                fatigue_related_report_count=("fatigue_related_flag", "sum"),
            )
            .reset_index()
        )
        frames.append(asrs_summary)

    if not ntsb.empty:
        investigations = add_month_column(ntsb, "event_date")
        investigations["airport"] = investigations["airport_code"].fillna("UNKNOWN").astype(str).str.strip().str.upper()
        investigations["region"] = map_airport_region(investigations["airport"])
        investigations["serious_or_higher_flag"] = investigations["severity_normalized"].isin(
            ["serious_injury", "fatal_injury"]
        ).astype(int)
        ntsb_summary = (
            investigations.groupby(["report_month", "airport", "region"], dropna=False)
            .agg(
                ntsb_investigation_count=("ntsb_event_id", "count"),
                serious_or_higher_investigation_count=("serious_or_higher_flag", "sum"),
            )
            .reset_index()
        )
        frames.append(ntsb_summary)

    if not culture.empty:
        culture_frame = add_month_column(culture, "event_date")
        culture_frame["airport"] = culture_frame["base_location"].fillna("UNKNOWN").astype(str).str.strip().str.upper()
        culture_frame["region"] = map_airport_region(culture_frame["airport"])
        culture_summary = (
            culture_frame.groupby(["report_month", "airport", "region"], dropna=False)
            .agg(
                avg_training_completion_rate=("training_completion_rate", "mean"),
                avg_safety_engagement_score=("safety_engagement_score", "mean"),
                fatigue_training_completion_rate=("fatigue_training_flag", "mean"),
                synthetic_elevated_risk_count=("severity_score", lambda values: int((values.fillna(0) > 0).sum())),
            )
            .reset_index()
        )
        frames.append(culture_summary)

    if not frames:
        return pd.DataFrame(columns=MONTHLY_RISK_OVERVIEW_COLUMNS)

    overview = frames[0]
    for frame in frames[1:]:
        overview = overview.merge(frame, on=["report_month", "airport", "region"], how="outer")

    overview = overview.sort_values(["report_month", "airport"]).reset_index(drop=True)
    overview["data_basis"] = (
        "Integrated from public BTS, ASRS, and NTSB sources plus synthetic safety-culture data at monthly airport level; all links are proxy-driven and aggregate only."
    )
    return overview


def write_output(frame: pd.DataFrame, output_key: str) -> None:
    """Write an analytics output CSV if data is available."""
    config = load_config()
    output_path = resolve_path(config["outputs"][output_key])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if frame.empty:
        frame.to_csv(output_path, index=False)
        LOGGER.warning(
            "No data was available for analytics output '%s'; wrote an empty CSV to %s to avoid stale outputs.",
            output_key,
            output_path,
        )
        return

    frame.to_csv(output_path, index=False)
    LOGGER.info("Wrote analytics output '%s' to %s", output_key, output_path)


def main() -> None:
    """Build Tableau-ready analytical marts from trusted public and synthetic sources."""
    bts = load_csv_output("trusted_bts_table")
    asrs = load_csv_output("trusted_asrs_table")
    ntsb = load_csv_output("trusted_ntsb_table")
    culture = load_csv_output("trusted_events_table")
    faasteam = load_raw_dataset("faasteam_events")

    outputs: dict[str, Callable[[], pd.DataFrame]] = {
        "monthly_risk_overview": lambda: build_monthly_risk_overview(bts, asrs, ntsb, culture),
        "fatigue_theme_trends": lambda: build_fatigue_theme_trends(asrs),
        "investigation_trends": lambda: build_investigation_trends(ntsb),
        "operational_disruption_summary": lambda: build_operational_disruption_summary(bts),
        "safety_promotion_summary": lambda: build_safety_promotion_summary(faasteam),
    }

    for output_key, builder in outputs.items():
        write_output(builder(), output_key)


if __name__ == "__main__":
    main()
