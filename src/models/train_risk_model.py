"""Starter modeling pipeline for a simple safety risk classifier."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.common.config import load_config, resolve_path
from src.common.logging_utils import get_logger


LOGGER = get_logger(__name__)


def load_training_data() -> pd.DataFrame:
    """Load the model-ready CSV training dataset from the analytics layer."""
    config = load_config()
    training_path = resolve_path(config["outputs"]["training_dataset"])
    if not training_path.exists():
        LOGGER.warning("Training dataset was not found at %s", training_path)
        return pd.DataFrame()
    return pd.read_csv(training_path)


def build_training_target(frame: pd.DataFrame) -> pd.DataFrame:
    """Create a defensible starter target using available proxy fields."""
    training_frame = frame.copy()
    if "severity_score" not in training_frame.columns:
        training_frame["severity_score"] = 0.0

    training_frame["elevated_risk_flag"] = (
        training_frame["severity_score"].fillna(0) > 0
    ).astype(int)
    return training_frame


def train_model(frame: pd.DataFrame) -> dict[str, Any]:
    """Train a lightweight baseline model and return summary metrics."""
    if frame.empty:
        LOGGER.warning("Model training skipped because the training dataframe is empty.")
        return {"status": "skipped", "reason": "empty_training_frame"}

    training_frame = build_training_target(frame)
    if len(training_frame) < 10:
        LOGGER.warning("Model training skipped because fewer than 10 rows were available.")
        return {"status": "skipped", "reason": "insufficient_rows", "row_count": int(len(training_frame))}

    if training_frame["elevated_risk_flag"].nunique() < 2:
        LOGGER.warning("Model training skipped because the target has only one class.")
        return {"status": "skipped", "reason": "single_target_class", "row_count": int(len(training_frame))}

    feature_columns = [
        column
        for column in ["event_year", "event_month", "source_system", "is_fatigue_proxy"]
        if column in training_frame.columns
    ]
    if not feature_columns:
        raise ValueError("No valid feature columns were found for model training.")

    X = training_frame[feature_columns]
    y = training_frame["elevated_risk_flag"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y if y.nunique() > 1 else None,
    )

    categorical_features = [
        column for column in X_train.columns if X_train[column].dtype == "object"
    ]
    numeric_features = [
        column for column in X_train.columns if column not in categorical_features
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))]),
                numeric_features,
            ),
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_features,
            ),
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", LogisticRegression(max_iter=500)),
        ]
    )
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)

    summary = {
        "status": "trained",
        "model_type": "logistic_regression_baseline",
        "row_count": int(len(training_frame)),
        "feature_columns": feature_columns,
        "accuracy": round(float(accuracy), 4),
        "target_definition": "severity_score > 0 as a proxy elevated-risk label",
    }
    LOGGER.info("Trained baseline model with accuracy %.4f", accuracy)
    return summary


def persist_model_summary(summary: dict[str, Any]) -> None:
    """Persist a model summary artifact for reproducibility and review."""
    config = load_config()
    output_path = resolve_path(config["outputs"]["model_artifact"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    LOGGER.info("Wrote model summary to %s", output_path)


def main() -> None:
    """Run the baseline model training pipeline."""
    training_frame = load_training_data()
    summary = train_model(training_frame)
    persist_model_summary(summary)


if __name__ == "__main__":
    main()
