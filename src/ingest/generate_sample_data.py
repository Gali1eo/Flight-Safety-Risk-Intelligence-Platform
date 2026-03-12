"""Generate small synthetic sample datasets for local end-to-end testing."""

from __future__ import annotations

import csv
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGGER = logging.getLogger(__name__)

if not LOGGER.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def resolve_path(path_value: str) -> Path:
    """Resolve a repository-relative path without requiring project dependencies."""
    return (PROJECT_ROOT / path_value).resolve()


def _write_csv(rows: list[dict[str, object]], output_path: Path) -> None:
    """Write records to a CSV file using only the standard library."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    LOGGER.info("Wrote %s rows to %s", len(rows), output_path)


def build_operations_sample() -> list[dict[str, object]]:
    """Create a BTS-style operational sample."""
    return [
        {
            "flight_date": "2025-01-03",
            "reporting_airline": "DL",
            "flight_number": "1045",
            "origin": "ATL",
            "dest": "JFK",
            "dep_delay": 12,
            "arr_delay": 6,
            "cancelled": 0,
            "diverted": 0,
            "tail_number": "N123DN",
        },
        {
            "flight_date": "2025-01-03",
            "reporting_airline": "DL",
            "flight_number": "1045",
            "origin": "ATL",
            "dest": "JFK",
            "dep_delay": 12,
            "arr_delay": 6,
            "cancelled": 0,
            "diverted": 0,
            "tail_number": "N123DN",
        },
        {
            "flight_date": "2025-01-05",
            "reporting_airline": "DL",
            "flight_number": "2201",
            "origin": "MSP",
            "dest": "DTW",
            "dep_delay": 0,
            "arr_delay": -3,
            "cancelled": 0,
            "diverted": 0,
            "tail_number": "N784DN",
        },
        {
            "flight_date": "2025-01-08",
            "reporting_airline": "OO",
            "flight_number": "3912",
            "origin": "SLC",
            "dest": "LAX",
            "dep_delay": None,
            "arr_delay": None,
            "cancelled": 1,
            "diverted": 0,
            "tail_number": None,
        },
        {
            "flight_date": "2025-01-11",
            "reporting_airline": "WN",
            "flight_number": "611",
            "origin": "DAL",
            "dest": "HOU",
            "dep_delay": 47,
            "arr_delay": 39,
            "cancelled": 0,
            "diverted": 0,
            "tail_number": "N771SA",
        },
        {
            "flight_date": "2025-01-14",
            "reporting_airline": "DL",
            "flight_number": "998",
            "origin": "SEA",
            "dest": "ATL",
            "dep_delay": 4,
            "arr_delay": None,
            "cancelled": 0,
            "diverted": 1,
            "tail_number": "N519DN",
        },
    ]


def build_incidents_sample() -> list[dict[str, object]]:
    """Create an ASRS-style incident and fatigue proxy sample."""
    return [
        {
            "report_id": "ASRS-1001",
            "event_date": "2025-01-04",
            "location": "ATL",
            "aircraft_operator": "Delta Air Lines",
            "anomaly": "Altitude Deviation",
            "human_factors": "Fatigue",
            "narrative": "Crew reported reduced alertness during descent after extended duty period.",
            "source_system": "NASA_ASRS",
        },
        {
            "report_id": "ASRS-1002",
            "event_date": "2025-01-07",
            "location": "MSP",
            "aircraft_operator": "Delta Connection",
            "anomaly": "Runway Incursion",
            "human_factors": "Communication Breakdown",
            "narrative": "Ground coordination issue led to near-conflict on taxiway.",
            "source_system": "NASA_ASRS",
        },
        {
            "report_id": "ASRS-1002",
            "event_date": "2025-01-07",
            "location": "MSP",
            "aircraft_operator": "Delta Connection",
            "anomaly": "Runway Incursion",
            "human_factors": "Communication Breakdown",
            "narrative": "Ground coordination issue led to near-conflict on taxiway.",
            "source_system": "NASA_ASRS",
        },
        {
            "report_id": "ASRS-1003",
            "event_date": "2025-01-09",
            "location": None,
            "aircraft_operator": "Southwest Airlines",
            "anomaly": "Checklist Deviation",
            "human_factors": "Distraction",
            "narrative": None,
            "source_system": "NASA_ASRS",
        },
        {
            "report_id": "ASRS-1004",
            "event_date": "2025-01-12",
            "location": "JFK",
            "aircraft_operator": None,
            "anomaly": "Unstable Approach",
            "human_factors": "Fatigue",
            "narrative": "Approach became unstable after late runway change and high workload.",
            "source_system": "NASA_ASRS",
        },
    ]


def build_investigations_sample() -> list[dict[str, object]]:
    """Create an NTSB-style investigation sample."""
    return [
        {
            "ntsb_event_id": "NTSB-ATL-001",
            "event_date": "2025-01-02",
            "airport_code": "ATL",
            "operator_name": "Delta Air Lines",
            "injury_severity": "None",
            "event_type": "Ground Damage",
            "aircraft_damage": "Minor",
            "source_system": "NTSB",
        },
        {
            "ntsb_event_id": "NTSB-DTW-002",
            "event_date": "2025-01-06",
            "airport_code": "DTW",
            "operator_name": "Delta Connection",
            "injury_severity": "Minor",
            "event_type": "Turbulence Injury",
            "aircraft_damage": "None",
            "source_system": "NTSB",
        },
        {
            "ntsb_event_id": "NTSB-DTW-002",
            "event_date": "2025-01-06",
            "airport_code": "DTW",
            "operator_name": "Delta Connection",
            "injury_severity": "Minor",
            "event_type": "Turbulence Injury",
            "aircraft_damage": "None",
            "source_system": "NTSB",
        },
        {
            "ntsb_event_id": "NTSB-LAX-003",
            "event_date": "2025-01-10",
            "airport_code": None,
            "operator_name": "SkyWest Airlines",
            "injury_severity": "Serious",
            "event_type": "Hard Landing",
            "aircraft_damage": "Substantial",
            "source_system": "NTSB",
        },
        {
            "ntsb_event_id": "NTSB-SEA-004",
            "event_date": "2025-01-15",
            "airport_code": "SEA",
            "operator_name": None,
            "injury_severity": "None",
            "event_type": "Maintenance Issue",
            "aircraft_damage": None,
            "source_system": "NTSB",
        },
    ]


def build_safety_promotion_sample() -> list[dict[str, object]]:
    """Create a FAASTeam-style safety promotion sample."""
    return [
        {
            "event_id": "FAAST-001",
            "event_date": "2025-01-05",
            "location": "Atlanta",
            "state": "GA",
            "topic": "Fatigue Risk Management",
            "audience_type": "Pilots",
            "source_system": "FAASTEAM",
        },
        {
            "event_id": "FAAST-002",
            "event_date": "2025-01-08",
            "location": "Detroit",
            "state": "MI",
            "topic": "Runway Safety",
            "audience_type": "Mixed",
            "source_system": "FAASTEAM",
        },
        {
            "event_id": "FAAST-002",
            "event_date": "2025-01-08",
            "location": "Detroit",
            "state": "MI",
            "topic": "Runway Safety",
            "audience_type": "Mixed",
            "source_system": "FAASTEAM",
        },
        {
            "event_id": "FAAST-003",
            "event_date": "2025-01-13",
            "location": None,
            "state": "WA",
            "topic": "Human Factors",
            "audience_type": "Mechanics",
            "source_system": "FAASTEAM",
        },
        {
            "event_id": "FAAST-004",
            "event_date": "2025-01-16",
            "location": "Dallas",
            "state": None,
            "topic": "Safety Culture",
            "audience_type": "Dispatch",
            "source_system": "FAASTEAM",
        },
    ]


def build_safety_culture_sample() -> list[dict[str, object]]:
    """Create a synthetic internal safety culture sample that the starter pipeline can transform."""
    return [
        {
            "event_id": "CULT-001",
            "employee_period_key": "EMP-1001-2025-01",
            "event_date": "2025-01-01",
            "period_start_date": "2025-01-01",
            "source_system": "Synthetic_Safety_Culture",
            "base_location": "ATL",
            "fleet_group": "Mainline",
            "severity_score": 0.0,
            "training_completion_rate": 0.98,
            "safety_engagement_score": 4.6,
            "fatigue_training_flag": 1,
        },
        {
            "event_id": "CULT-002",
            "employee_period_key": "EMP-1002-2025-01",
            "event_date": "2025-01-01",
            "period_start_date": "2025-01-01",
            "source_system": "Synthetic_Safety_Culture",
            "base_location": "MSP",
            "fleet_group": "Regional",
            "severity_score": 1.0,
            "training_completion_rate": 0.77,
            "safety_engagement_score": 3.9,
            "fatigue_training_flag": 0,
        },
        {
            "event_id": "CULT-002",
            "employee_period_key": "EMP-1002-2025-01",
            "event_date": "2025-01-01",
            "period_start_date": "2025-01-01",
            "source_system": "Synthetic_Safety_Culture",
            "base_location": "MSP",
            "fleet_group": "Regional",
            "severity_score": 1.0,
            "training_completion_rate": 0.77,
            "safety_engagement_score": 3.9,
            "fatigue_training_flag": 0,
        },
        {
            "event_id": "CULT-003",
            "employee_period_key": "EMP-1003-2025-01",
            "event_date": "2025-01-01",
            "period_start_date": "2025-01-01",
            "source_system": "Synthetic_Safety_Culture",
            "base_location": None,
            "fleet_group": "Mainline",
            "severity_score": 0.0,
            "training_completion_rate": None,
            "safety_engagement_score": 4.2,
            "fatigue_training_flag": 1,
        },
        {
            "event_id": "CULT-004",
            "employee_period_key": "EMP-1004-2025-01",
            "event_date": "2025-01-01",
            "period_start_date": "2025-01-01",
            "source_system": "Synthetic_Safety_Culture",
            "base_location": "SEA",
            "fleet_group": None,
            "severity_score": 2.0,
            "training_completion_rate": 0.61,
            "safety_engagement_score": None,
            "fatigue_training_flag": 0,
        },
        {
            "event_id": "CULT-005",
            "employee_period_key": "EMP-1005-2025-01",
            "event_date": "2025-01-01",
            "period_start_date": "2025-01-01",
            "source_system": "Synthetic_Safety_Culture",
            "base_location": "DTW",
            "fleet_group": "Regional",
            "severity_score": 0.0,
            "training_completion_rate": 0.93,
            "safety_engagement_score": 4.8,
            "fatigue_training_flag": 1,
        },
        {
            "event_id": "CULT-006",
            "employee_period_key": "EMP-1006-2025-01",
            "event_date": "2025-01-01",
            "period_start_date": "2025-01-01",
            "source_system": "Synthetic_Safety_Culture",
            "base_location": "JFK",
            "fleet_group": "Mainline",
            "severity_score": 1.0,
            "training_completion_rate": 0.84,
            "safety_engagement_score": 3.7,
            "fatigue_training_flag": 1,
        },
        {
            "event_id": "CULT-007",
            "employee_period_key": "EMP-1007-2025-01",
            "event_date": "2025-01-01",
            "period_start_date": "2025-01-01",
            "source_system": "Synthetic_Safety_Culture",
            "base_location": "ATL",
            "fleet_group": "Mainline",
            "severity_score": 0.0,
            "training_completion_rate": 0.88,
            "safety_engagement_score": 4.1,
            "fatigue_training_flag": 0,
        },
        {
            "event_id": "CULT-008",
            "employee_period_key": "EMP-1008-2025-01",
            "event_date": "2025-01-01",
            "period_start_date": "2025-01-01",
            "source_system": "Synthetic_Safety_Culture",
            "base_location": "SEA",
            "fleet_group": "Regional",
            "severity_score": 2.0,
            "training_completion_rate": 0.55,
            "safety_engagement_score": 3.3,
            "fatigue_training_flag": 0,
        },
        {
            "event_id": "CULT-009",
            "employee_period_key": "EMP-1009-2025-01",
            "event_date": "2025-01-01",
            "period_start_date": "2025-01-01",
            "source_system": "Synthetic_Safety_Culture",
            "base_location": "MSP",
            "fleet_group": "Regional",
            "severity_score": 1.0,
            "training_completion_rate": 0.73,
            "safety_engagement_score": 3.8,
            "fatigue_training_flag": 1,
        },
        {
            "event_id": "CULT-010",
            "employee_period_key": "EMP-1010-2025-01",
            "event_date": "2025-01-01",
            "period_start_date": "2025-01-01",
            "source_system": "Synthetic_Safety_Culture",
            "base_location": "BOS",
            "fleet_group": "Mainline",
            "severity_score": 0.0,
            "training_completion_rate": 0.9,
            "safety_engagement_score": 4.4,
            "fatigue_training_flag": 1,
        },
    ]


def generate_sample_data() -> None:
    """Generate all local sample datasets used by the project."""
    samples = {
        "operations": (
            build_operations_sample(),
            resolve_path("data/raw/operations/operations_sample.csv"),
        ),
        "incidents": (
            build_incidents_sample(),
            resolve_path("data/raw/incidents/incidents_sample.csv"),
        ),
        "investigations": (
            build_investigations_sample(),
            resolve_path("data/raw/investigations/investigations_sample.csv"),
        ),
        "safety_promotion": (
            build_safety_promotion_sample(),
            resolve_path("data/raw/safety_promotion/safety_promotion_sample.csv"),
        ),
        "bts_on_time": (
            build_operations_sample(),
            resolve_path("data/raw/bts_on_time/bts_on_time_2025_01.csv"),
        ),
        "nasa_asrs": (
            build_incidents_sample(),
            resolve_path("data/raw/nasa_asrs/asrs_reports_2025.csv"),
        ),
        "ntsb_investigations": (
            build_investigations_sample(),
            resolve_path("data/raw/ntsb_investigations/ntsb_aviation_events_2025.csv"),
        ),
        "faasteam_events": (
            build_safety_promotion_sample(),
            resolve_path("data/raw/faasteam_events/faasteam_events_2025.csv"),
        ),
        "synthetic_safety_culture": (
            build_safety_culture_sample(),
            resolve_path(
                "data/raw/synthetic_safety_culture/synthetic_safety_culture_monthly.csv"
            ),
        ),
    }

    for dataset_name, (rows, output_path) in samples.items():
        _write_csv(rows, output_path)
        LOGGER.info("Generated sample dataset for %s", dataset_name)


def main() -> None:
    """Entrypoint for local sample data generation."""
    generate_sample_data()


if __name__ == "__main__":
    main()
