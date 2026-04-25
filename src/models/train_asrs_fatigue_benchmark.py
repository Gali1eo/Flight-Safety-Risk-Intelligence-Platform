"""First ML benchmark for ASRS fatigue signal detection.

This benchmark is intentionally lightweight:
TF-IDF features from `narrative_clean` feed a class-balanced logistic
regression model evaluated with 3-fold stratified cross-validation.
The target is the proxy label `weak_fatigue_label`, not ground truth.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline

from src.common.config import load_config, resolve_path
from src.common.logging_utils import get_logger
from src.common.validation import validate_no_duplicates, validate_required_columns


LOGGER = get_logger(__name__)

INPUT_REQUIRED_COLUMNS = [
    "report_id",
    "event_date",
    "narrative_clean",
    "weak_fatigue_label",
]


def load_asrs_nlp_output() -> pd.DataFrame:
    """Load the enriched ASRS NLP pilot output from the analytics layer."""
    config = load_config()
    input_path = resolve_path(config["outputs"]["asrs_nlp_enriched"])
    if not input_path.exists():
        LOGGER.warning("ASRS NLP enriched input was not found at %s", input_path)
        return pd.DataFrame()

    frame = pd.read_csv(input_path, low_memory=False)
    LOGGER.info("Loaded ASRS NLP enriched input from %s with %s row(s)", input_path, len(frame))
    return frame


def build_model_pipeline() -> Pipeline:
    """Build the TF-IDF + logistic regression benchmark pipeline."""
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.95,
                    sublinear_tf=True,
                    strip_accents="unicode",
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=1000,
                    solver="liblinear",
                    random_state=42,
                ),
            ),
        ]
    )


def make_metric_bundle(y_true: pd.Series, y_pred: np.ndarray, y_prob: np.ndarray) -> dict[str, Any]:
    """Create a compact, imbalance-aware metric summary."""
    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    positive_report = report.get("1", {})
    negative_report = report.get("0", {})
    macro_report = report.get("macro avg", {})
    weighted_report = report.get("weighted avg", {})

    metrics: dict[str, Any] = {
        "positive_class": {
            "precision": round(float(positive_report.get("precision", 0.0)), 4),
            "recall": round(float(positive_report.get("recall", 0.0)), 4),
            "f1": round(float(positive_report.get("f1-score", 0.0)), 4),
            "support": int(positive_report.get("support", 0)),
        },
        "negative_class": {
            "precision": round(float(negative_report.get("precision", 0.0)), 4),
            "recall": round(float(negative_report.get("recall", 0.0)), 4),
            "f1": round(float(negative_report.get("f1-score", 0.0)), 4),
            "support": int(negative_report.get("support", 0)),
        },
        "macro_avg": {
            "precision": round(float(macro_report.get("precision", 0.0)), 4),
            "recall": round(float(macro_report.get("recall", 0.0)), 4),
            "f1": round(float(macro_report.get("f1-score", 0.0)), 4),
            "support": int(macro_report.get("support", 0)),
        },
        "weighted_avg": {
            "precision": round(float(weighted_report.get("precision", 0.0)), 4),
            "recall": round(float(weighted_report.get("recall", 0.0)), 4),
            "f1": round(float(weighted_report.get("f1-score", 0.0)), 4),
            "support": int(weighted_report.get("support", 0)),
        },
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "average_precision": round(float(average_precision_score(y_true, y_prob)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, y_prob)), 4),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
        "predicted_positive_rate": round(float(np.mean(y_pred)), 4),
    }
    return metrics


def select_decision_threshold(y_true: pd.Series, y_prob: np.ndarray) -> dict[str, Any]:
    """Select a conservative decision threshold from the out-of-fold PR curve."""
    precision, recall, thresholds = precision_recall_curve(y_true, y_prob)
    if len(thresholds) == 0:
        return {
            "threshold": 0.5,
            "strategy": "default_0.5",
            "best_f1": 0.0,
        }

    precision = precision[1:]
    recall = recall[1:]
    with np.errstate(divide="ignore", invalid="ignore"):
        f1_scores = np.where(
            (precision + recall) > 0,
            (2 * precision * recall) / (precision + recall),
            0.0,
        )

    best_index = int(np.argmax(f1_scores))
    return {
        "threshold": round(float(thresholds[best_index]), 6),
        "strategy": "oof_pr_curve_max_f1",
        "best_f1": round(float(f1_scores[best_index]), 4),
    }


def summarize_fold(
    fold_number: int,
    train_index: np.ndarray,
    test_index: np.ndarray,
    y_full: pd.Series,
    y_test: pd.Series,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
    threshold: float,
) -> dict[str, Any]:
    """Summarize a single cross-validation fold."""
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    positive_report = report.get("1", {})

    return {
        "fold": int(fold_number),
        "train_rows": int(len(train_index)),
        "test_rows": int(len(test_index)),
        "train_positive_rows": int(y_full.iloc[train_index].sum()),
        "test_positive_rows": int(y_full.iloc[test_index].sum()),
        "precision": round(float(positive_report.get("precision", 0.0)), 4),
        "recall": round(float(positive_report.get("recall", 0.0)), 4),
        "f1": round(float(positive_report.get("f1-score", 0.0)), 4),
        "support": int(positive_report.get("support", 0)),
        "average_precision": round(float(average_precision_score(y_test, y_prob)), 4),
        "predicted_positive_rate": round(float(np.mean(y_pred)), 4),
        "decision_threshold": round(float(threshold), 6),
    }


def fit_and_validate(
    frame: pd.DataFrame,
) -> tuple[dict[str, Any], pd.DataFrame]:
    """Run 3-fold CV and produce a compact summary plus OOF predictions."""
    if frame.empty:
        return {"status": "skipped", "reason": "empty_input"}, pd.DataFrame()

    validate_required_columns(frame, INPUT_REQUIRED_COLUMNS)
    validate_no_duplicates(frame, ["report_id"])

    work = frame.copy()
    work["narrative_clean"] = work["narrative_clean"].fillna("").astype(str)
    work["weak_fatigue_label"] = pd.to_numeric(work["weak_fatigue_label"], errors="coerce")

    if work["weak_fatigue_label"].isna().any():
        raise ValueError("weak_fatigue_label contains null or non-numeric values.")

    work["weak_fatigue_label"] = work["weak_fatigue_label"].astype(int)
    y = work["weak_fatigue_label"]

    if len(work) < 10:
        return {"status": "skipped", "reason": "insufficient_rows", "row_count": int(len(work))}, pd.DataFrame()

    if y.nunique() < 2:
        return {"status": "skipped", "reason": "single_target_class", "row_count": int(len(work))}, pd.DataFrame()

    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    oof_probability = np.zeros(len(work), dtype=float)
    oof_fold = np.zeros(len(work), dtype=int)
    fold_payloads: list[dict[str, Any]] = []

    for fold_number, (train_index, test_index) in enumerate(cv.split(work["narrative_clean"], y), start=1):
        pipeline = build_model_pipeline()
        pipeline.fit(work["narrative_clean"].iloc[train_index], y.iloc[train_index])

        fold_probability = pipeline.predict_proba(work["narrative_clean"].iloc[test_index])[:, 1]

        oof_probability[test_index] = fold_probability
        oof_fold[test_index] = fold_number

        fold_payloads.append(
            {
                "fold_number": fold_number,
                "train_index": train_index,
                "test_index": test_index,
                "y_test": y.iloc[test_index],
                "y_prob": fold_probability,
            }
        )

    threshold_info = select_decision_threshold(y, oof_probability)
    decision_threshold = float(threshold_info["threshold"])
    oof_prediction = (oof_probability >= decision_threshold).astype(int)
    overall_metrics = make_metric_bundle(y, oof_prediction, oof_probability)

    fold_summaries = []
    for fold_payload in fold_payloads:
        fold_prediction = (fold_payload["y_prob"] >= decision_threshold).astype(int)
        fold_summaries.append(
            summarize_fold(
                fold_payload["fold_number"],
                fold_payload["train_index"],
                fold_payload["test_index"],
                y,
                fold_payload["y_test"],
                fold_prediction,
                fold_payload["y_prob"],
                decision_threshold,
            )
        )

    final_pipeline = build_model_pipeline()
    final_pipeline.fit(work["narrative_clean"], y)

    vectorizer: TfidfVectorizer = final_pipeline.named_steps["tfidf"]
    classifier: LogisticRegression = final_pipeline.named_steps["classifier"]
    feature_names = vectorizer.get_feature_names_out()
    coefficients = classifier.coef_.ravel()

    top_positive_indices = np.argsort(coefficients)[::-1][:10]
    top_negative_indices = np.argsort(coefficients)[:10]

    summary: dict[str, Any] = {
        "status": "trained",
        "model_name": "tfidf_logistic_regression",
        "target_column": "weak_fatigue_label",
        "text_column": "narrative_clean",
        "row_count": int(len(work)),
        "positive_count": int(y.sum()),
        "negative_count": int((1 - y).sum()),
        "positive_rate": round(float(y.mean()), 4),
        "cv_strategy": {
            "name": "StratifiedKFold",
            "n_splits": 3,
            "shuffle": True,
            "random_state": 42,
        },
        "decision_threshold": threshold_info["threshold"],
        "threshold_selection": threshold_info["strategy"],
        "threshold_selection_best_f1": threshold_info["best_f1"],
        "vectorizer": {
            "name": "TfidfVectorizer",
            "ngram_range": [1, 2],
            "min_df": 2,
            "max_df": 0.95,
            "sublinear_tf": True,
            "strip_accents": "unicode",
            "vocabulary_size": int(len(feature_names)),
        },
        "classifier": {
            "name": "LogisticRegression",
            "class_weight": "balanced",
            "solver": "liblinear",
            "max_iter": 1000,
        },
        "metrics": overall_metrics,
        "fold_metrics": fold_summaries,
        "top_positive_terms": [
            {"term": str(feature_names[idx]), "weight": round(float(coefficients[idx]), 4)}
            for idx in top_positive_indices
        ],
        "top_negative_terms": [
            {"term": str(feature_names[idx]), "weight": round(float(coefficients[idx]), 4)}
            for idx in top_negative_indices
        ],
        "interpretation_note": (
            "Metrics are out-of-fold from 3-fold stratified cross-validation. "
            "Coefficient terms come from a final refit on the full pilot dataset for interpretability only."
        ),
    }

    predictions = pd.DataFrame(
        {
            "report_id": work["report_id"].values,
            "event_date": work["event_date"].values,
            "weak_fatigue_label": y.values,
            "oof_fold": oof_fold,
            "oof_predicted_probability": np.round(oof_probability, 6),
            "oof_predicted_label": oof_prediction,
            "decision_threshold": np.round(np.repeat(decision_threshold, len(work)), 6),
            "theme_primary_label": work["theme_primary_label"].values
            if "theme_primary_label" in work.columns
            else "unknown",
            "fatigue_confidence_tier": work["fatigue_confidence_tier"].values
            if "fatigue_confidence_tier" in work.columns
            else "unknown",
        }
    )

    LOGGER.info("Completed 3-fold CV benchmark on %s ASRS rows", len(work))
    LOGGER.info("OOF positive class metrics: %s", summary["metrics"]["positive_class"])
    LOGGER.info("OOF average precision: %.4f", summary["metrics"]["average_precision"])

    return summary, predictions


def persist_outputs(summary: dict[str, Any], predictions: pd.DataFrame) -> None:
    """Persist the model summary JSON and OOF prediction CSV."""
    config = load_config()
    summary_path = resolve_path(config["outputs"]["asrs_fatigue_model_summary"])
    predictions_path = resolve_path(config["outputs"]["asrs_fatigue_predictions"])

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    predictions_path.parent.mkdir(parents=True, exist_ok=True)

    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    predictions.to_csv(predictions_path, index=False)

    LOGGER.info("Wrote ASRS fatigue model summary to %s", summary_path)
    LOGGER.info("Wrote ASRS fatigue predictions to %s", predictions_path)


def main() -> None:
    """Run the first ASRS ML benchmark."""
    frame = load_asrs_nlp_output()
    summary, predictions = fit_and_validate(frame)
    persist_outputs(summary, predictions)


if __name__ == "__main__":
    main()
