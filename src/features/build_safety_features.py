"""Starter feature engineering pipeline for safety risk analytics."""

from __future__ import annotations

import pandas as pd

from src.common.config import load_config, resolve_path
from src.common.logging_utils import get_logger
from src.common.validation import mask_identifier_columns, validate_required_columns


LOGGER = get_logger(__name__)


FEATURE_REQUIRED_COLUMNS = ["event_id", "event_date", "source_system"]


def load_trusted_events() -> pd.DataFrame:
    """Load the trusted events CSV if it exists."""
    config = load_config()
    trusted_path = resolve_path(config["outputs"]["trusted_events_table"])
    if not trusted_path.exists():
        LOGGER.warning("Trusted events table was not found at %s", trusted_path)
        return pd.DataFrame()
    return pd.read_csv(trusted_path)


def build_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Derive starter safety features from the trusted layer."""
    if frame.empty:
        return frame

    validate_required_columns(frame, FEATURE_REQUIRED_COLUMNS)

    features = frame.copy()
    features["event_date"] = pd.to_datetime(features["event_date"], errors="coerce")
    features["event_year"] = features["event_date"].dt.year
    features["event_month"] = features["event_date"].dt.month
    features["is_fatigue_proxy"] = features["source_system"].str.contains(
        "asrs", case=False, na=False
    ).astype(int)

    if "severity_score" not in features.columns:
        features["severity_score"] = 0.0

    if "report_text" in features.columns:
        features["report_text_length"] = features["report_text"].fillna("").str.len()

    safe_features = mask_identifier_columns(features, ["employee_id", "reporter_id"])
    LOGGER.info("Built feature table with %s rows and %s columns", *safe_features.shape)
    return safe_features


def persist_features(frame: pd.DataFrame) -> None:
    """Persist analytics-layer features as CSV for downstream local demo use."""
    if frame.empty:
        LOGGER.warning("No features were written because the dataframe is empty.")
        return

    config = load_config()
    feature_path = resolve_path(config["outputs"]["feature_table"])
    training_path = resolve_path(config["outputs"]["training_dataset"])

    feature_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(feature_path, index=False)
    frame.to_csv(training_path, index=False)
    LOGGER.info("Wrote feature table to %s", feature_path)


def main() -> None:
    """Run the feature engineering pipeline."""
    trusted_events = load_trusted_events()
    features = build_features(trusted_events)
    persist_features(features)


if __name__ == "__main__":
    main()
