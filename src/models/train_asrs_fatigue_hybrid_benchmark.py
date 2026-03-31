"""Second ASRS fatigue benchmark using engineered narrative features.

This benchmark keeps the modeling stack lightweight and interpretable:
TF-IDF from `narrative_clean` is combined with the narrative-derived fatigue
feature table, then evaluated with 3-fold stratified cross-validation.
The proxy target remains `weak_fatigue_label`.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.common.config import load_config, resolve_path
from src.common.logging_utils import get_logger
from src.common.validation import (
    standardize_columns,
    validate_no_duplicates,
    validate_required_columns,
)
from src.features.build_asrs_fatigue_features import FEATURE_COLUMNS
from src.models.train_asrs_fatigue_benchmark import (
    make_metric_bundle,
    select_decision_threshold,
)


LOGGER = get_logger(__name__)

BASE_REQUIRED_COLUMNS = [
    "report_id",
    "event_date",
    "location",
    "aircraft_operator",
    "theme_primary_label",
    "fatigue_confidence_tier",
    "narrative_clean",
    "weak_fatigue_label",
]
FEATURE_REQUIRED_COLUMNS = ["report_id", *FEATURE_COLUMNS]


def load_asrs_nlp_output() -> pd.DataFrame:
    """Load the enriched ASRS NLP pilot output from the analytics layer."""
    config = load_config()
    input_path = resolve_path(config["outputs"]["asrs_nlp_enriched"])
    if not input_path.exists():
        LOGGER.warning("ASRS NLP enriched input was not found at %s", input_path)
        return pd.DataFrame()

    frame = pd.read_csv(input_path, low_memory=False)
    frame = standardize_columns(frame)
    LOGGER.info("Loaded ASRS NLP input from %s with %s row(s)", input_path, len(frame))
    return frame


def load_asrs_fatigue_features() -> pd.DataFrame:
    """Load the engineered ASRS fatigue feature table."""
    config = load_config()
    input_path = resolve_path(config["outputs"]["asrs_fatigue_features"])
    if not input_path.exists():
        LOGGER.warning("ASRS fatigue features were not found at %s", input_path)
        return pd.DataFrame()

    frame = pd.read_csv(input_path, low_memory=False)
    frame = standardize_columns(frame)
    LOGGER.info("Loaded ASRS fatigue features from %s with %s row(s)", input_path, len(frame))
    return frame


def load_benchmark_one_outputs() -> tuple[dict[str, Any], pd.DataFrame]:
    """Load the benchmark 1 summary and out-of-fold predictions."""
    config = load_config()
    summary_path = resolve_path(config["outputs"]["asrs_fatigue_model_summary"])
    predictions_path = resolve_path(config["outputs"]["asrs_fatigue_predictions"])

    if not summary_path.exists():
        raise FileNotFoundError(f"Benchmark 1 summary was not found at {summary_path}")
    if not predictions_path.exists():
        raise FileNotFoundError(f"Benchmark 1 predictions were not found at {predictions_path}")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    predictions = pd.read_csv(predictions_path, low_memory=False)
    predictions = standardize_columns(predictions)
    LOGGER.info(
        "Loaded benchmark 1 outputs from %s and %s",
        summary_path,
        predictions_path,
    )
    return summary, predictions


def merge_inputs(base: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    """Join the narrative and engineered feature tables on report_id."""
    validate_required_columns(base, BASE_REQUIRED_COLUMNS)
    validate_required_columns(features, FEATURE_REQUIRED_COLUMNS)
    validate_no_duplicates(base, ["report_id"])
    validate_no_duplicates(features, ["report_id"])

    merged = base.copy()
    overlapping_feature_columns = [
        column for column in FEATURE_COLUMNS if column in merged.columns
    ]
    if overlapping_feature_columns:
        LOGGER.info(
            "Dropping overlapping baseline column(s) before feature merge: %s",
            ", ".join(sorted(overlapping_feature_columns)),
        )
        merged = merged.drop(columns=overlapping_feature_columns)

    feature_frame = features[FEATURE_REQUIRED_COLUMNS].copy()
    merged = merged.merge(feature_frame, on="report_id", how="inner", validate="one_to_one")
    if len(merged) != len(base):
        raise ValueError(
            "Benchmark 2 merge lost rows; the ASRS enriched and feature tables should align 1:1."
        )
    return merged


def build_model_pipeline() -> Pipeline:
    """Build the hybrid TF-IDF + engineered feature benchmark pipeline."""
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "text",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.95,
                    sublinear_tf=True,
                    strip_accents="unicode",
                ),
                "narrative_clean",
            ),
            (
                "numeric",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                FEATURE_COLUMNS,
            ),
        ]
    )

    classifier = LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        solver="liblinear",
        random_state=42,
    )
    return Pipeline(steps=[("features", preprocessor), ("classifier", classifier)])


def fit_and_validate(frame: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame]:
    """Run 3-fold CV and produce a compact summary plus OOF predictions."""
    if frame.empty:
        return {"status": "skipped", "reason": "empty_input"}, pd.DataFrame()

    validate_required_columns(frame, BASE_REQUIRED_COLUMNS)
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

    feature_input = work[["narrative_clean", *FEATURE_COLUMNS]]
    for fold_number, (train_index, test_index) in enumerate(cv.split(feature_input, y), start=1):
        pipeline = build_model_pipeline()
        pipeline.fit(feature_input.iloc[train_index], y.iloc[train_index])

        fold_probability = pipeline.predict_proba(feature_input.iloc[test_index])[:, 1]
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
        fold_metrics = make_metric_bundle(
            y.iloc[fold_payload["test_index"]],
            fold_prediction,
            fold_payload["y_prob"],
        )
        fold_summaries.append(
            {
                "fold": int(fold_payload["fold_number"]),
                "train_rows": int(len(fold_payload["train_index"])),
                "test_rows": int(len(fold_payload["test_index"])),
                "train_positive_rows": int(y.iloc[fold_payload["train_index"]].sum()),
                "test_positive_rows": int(y.iloc[fold_payload["test_index"]].sum()),
                "precision": round(float(fold_metrics["positive_class"]["precision"]), 4),
                "recall": round(float(fold_metrics["positive_class"]["recall"]), 4),
                "f1": round(float(fold_metrics["positive_class"]["f1"]), 4),
                "support": int(fold_payload["y_test"].sum()),
                "average_precision": round(float(fold_metrics["average_precision"]), 4),
                "predicted_positive_rate": round(float(np.mean(fold_prediction)), 4),
                "decision_threshold": round(float(decision_threshold), 6),
            }
        )

    final_pipeline = build_model_pipeline()
    final_pipeline.fit(feature_input, y)

    preprocessor: ColumnTransformer = final_pipeline.named_steps["features"]
    classifier: LogisticRegression = final_pipeline.named_steps["classifier"]
    feature_names = preprocessor.get_feature_names_out()
    coefficients = classifier.coef_.ravel()

    top_positive_indices = np.argsort(coefficients)[::-1][:10]
    top_negative_indices = np.argsort(coefficients)[:10]

    summary: dict[str, Any] = {
        "status": "trained",
        "model_name": "tfidf_logistic_regression_plus_engineered_features",
        "target_column": "weak_fatigue_label",
        "text_column": "narrative_clean",
        "numeric_feature_columns": FEATURE_COLUMNS,
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
            "vocabulary_size": int(
                len([name for name in feature_names if name.startswith("text__")])
            ),
        },
        "numeric_feature_count": int(len(FEATURE_COLUMNS)),
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
            "oof_fold": oof_fold,
            "benchmark2_predicted_probability": np.round(oof_probability, 6),
            "benchmark2_predicted_label": oof_prediction,
            "benchmark2_decision_threshold": np.round(np.repeat(decision_threshold, len(work)), 6),
        }
    )

    LOGGER.info("Completed 3-fold CV benchmark 2 on %s ASRS rows", len(work))
    LOGGER.info("OOF positive class metrics: %s", summary["metrics"]["positive_class"])
    LOGGER.info("OOF average precision: %.4f", summary["metrics"]["average_precision"])

    return summary, predictions


def build_comparison_summary(
    benchmark_one: dict[str, Any], benchmark_two: dict[str, Any]
) -> dict[str, Any]:
    """Compare benchmark 2 against benchmark 1 using imbalance-aware metrics."""
    b1_metrics = benchmark_one["metrics"]
    b2_metrics = benchmark_two["metrics"]

    metric_order = ["average_precision", "positive_f1"]
    b1_score = {
        "average_precision": float(b1_metrics["average_precision"]),
        "positive_f1": float(b1_metrics["positive_class"]["f1"]),
    }
    b2_score = {
        "average_precision": float(b2_metrics["average_precision"]),
        "positive_f1": float(b2_metrics["positive_class"]["f1"]),
    }

    selected_model = "benchmark_1_text_only"
    selection_reason = "benchmark_1 retained because benchmark_2 did not improve average_precision"
    if (
        b2_score["average_precision"] > b1_score["average_precision"]
        or (
            abs(b2_score["average_precision"] - b1_score["average_precision"]) < 1e-9
            and b2_score["positive_f1"] > b1_score["positive_f1"]
        )
    ):
        selected_model = "benchmark_2_hybrid_text_plus_features"
        selection_reason = "benchmark_2 selected because it improved average_precision, with positive_f1 as the tiebreaker"

    return {
        "status": "completed",
        "selection_rule": {
            "primary_metric": metric_order[0],
            "tiebreaker": metric_order[1],
        },
        "benchmark_1": {
            "model_name": benchmark_one["model_name"],
            "decision_threshold": benchmark_one["decision_threshold"],
            "metrics": benchmark_one["metrics"],
        },
        "benchmark_2": {
            "model_name": benchmark_two["model_name"],
            "decision_threshold": benchmark_two["decision_threshold"],
            "numeric_feature_count": benchmark_two["numeric_feature_count"],
            "metrics": benchmark_two["metrics"],
            "top_positive_terms": benchmark_two["top_positive_terms"],
            "top_negative_terms": benchmark_two["top_negative_terms"],
        },
        "comparison": {
            "average_precision_delta": round(
                b2_score["average_precision"] - b1_score["average_precision"], 4
            ),
            "positive_f1_delta": round(b2_score["positive_f1"] - b1_score["positive_f1"], 4),
            "selected_model": selected_model,
            "selection_reason": selection_reason,
        },
    }


def build_scored_output(
    base: pd.DataFrame,
    benchmark_one_predictions: pd.DataFrame,
    benchmark_two_predictions: pd.DataFrame,
    selected_model: str,
) -> pd.DataFrame:
    """Build a scored ASRS output with both benchmark scores and the chosen score."""
    benchmark_one = benchmark_one_predictions.rename(
        columns={
            "oof_predicted_probability": "benchmark1_predicted_probability",
            "oof_predicted_label": "benchmark1_predicted_label",
            "decision_threshold": "benchmark1_decision_threshold",
        }
    )[[
        "report_id",
        "benchmark1_predicted_probability",
        "benchmark1_predicted_label",
        "benchmark1_decision_threshold",
    ]]

    benchmark_two = benchmark_two_predictions[[
        "report_id",
        "benchmark2_predicted_probability",
        "benchmark2_predicted_label",
        "benchmark2_decision_threshold",
    ]]

    scored = base.copy()
    scored = scored.merge(benchmark_one, on="report_id", how="left", validate="one_to_one")
    scored = scored.merge(benchmark_two, on="report_id", how="left", validate="one_to_one")

    if selected_model == "benchmark_2_hybrid_text_plus_features":
        scored["selected_model_name"] = selected_model
        scored["selected_probability"] = scored["benchmark2_predicted_probability"]
        scored["selected_prediction"] = scored["benchmark2_predicted_label"]
    else:
        scored["selected_model_name"] = selected_model
        scored["selected_probability"] = scored["benchmark1_predicted_probability"]
        scored["selected_prediction"] = scored["benchmark1_predicted_label"]

    scored["event_month"] = pd.to_datetime(scored["event_date"], errors="coerce").dt.strftime(
        "%Y-%m"
    )

    output_columns = [
        "report_id",
        "event_date",
        "event_month",
        "location",
        "aircraft_operator",
        "theme_primary_label",
        "fatigue_confidence_tier",
        "weak_fatigue_label",
        "benchmark1_predicted_probability",
        "benchmark1_predicted_label",
        "benchmark2_predicted_probability",
        "benchmark2_predicted_label",
        "selected_model_name",
        "selected_probability",
        "selected_prediction",
    ]
    return scored[output_columns].copy()


def build_group_summary(frame: pd.DataFrame, group_column: str) -> pd.DataFrame:
    """Build a compact aggregate summary for a chosen grouping column."""
    work = frame.copy()
    work[group_column] = work[group_column].fillna("unknown").replace("", "unknown")

    work["tp_flag"] = ((work["weak_fatigue_label"] == 1) & (work["selected_prediction"] == 1)).astype(
        int
    )
    work["fp_flag"] = ((work["weak_fatigue_label"] == 0) & (work["selected_prediction"] == 1)).astype(
        int
    )
    work["fn_flag"] = ((work["weak_fatigue_label"] == 1) & (work["selected_prediction"] == 0)).astype(
        int
    )
    work["tn_flag"] = ((work["weak_fatigue_label"] == 0) & (work["selected_prediction"] == 0)).astype(
        int
    )

    summary = (
        work.groupby(group_column, dropna=False)
        .agg(
            n_reports=("report_id", "count"),
            actual_fatigue_count=("weak_fatigue_label", "sum"),
            actual_fatigue_rate=("weak_fatigue_label", "mean"),
            predicted_fatigue_count=("selected_prediction", "sum"),
            predicted_fatigue_rate=("selected_prediction", "mean"),
            mean_selected_probability=("selected_probability", "mean"),
            median_selected_probability=("selected_probability", "median"),
            tp_count=("tp_flag", "sum"),
            fp_count=("fp_flag", "sum"),
            fn_count=("fn_flag", "sum"),
            tn_count=("tn_flag", "sum"),
        )
        .reset_index()
    )

    tp = summary["tp_count"].to_numpy(dtype=float)
    fp = summary["fp_count"].to_numpy(dtype=float)
    fn = summary["fn_count"].to_numpy(dtype=float)
    precision = np.divide(tp, tp + fp, out=np.zeros_like(tp), where=(tp + fp) > 0)
    recall = np.divide(tp, tp + fn, out=np.zeros_like(tp), where=(tp + fn) > 0)
    f1 = np.divide(
        2 * precision * recall,
        precision + recall,
        out=np.zeros_like(precision),
        where=(precision + recall) > 0,
    )
    summary["precision"] = np.round(precision, 4)
    summary["recall"] = np.round(recall, 4)
    summary["f1"] = np.round(f1, 4)
    summary["predicted_positive_rate"] = summary["predicted_fatigue_rate"].round(4)
    summary["actual_positive_rate"] = summary["actual_fatigue_rate"].round(4)

    return summary.sort_values(["n_reports", "actual_fatigue_count"], ascending=[False, False])


def persist_outputs(
    comparison: dict[str, Any],
    scored: pd.DataFrame,
    month_summary: pd.DataFrame,
    operator_summary: pd.DataFrame,
    location_summary: pd.DataFrame,
    theme_summary: pd.DataFrame,
) -> None:
    """Persist the comparison JSON, scored output, and grouped summaries."""
    config = load_config()
    output_paths = {
        "comparison": resolve_path(config["outputs"]["asrs_fatigue_model_comparison"]),
        "scored": resolve_path(config["outputs"]["asrs_nlp_scored"]),
        "month": resolve_path(config["outputs"]["asrs_fatigue_summary_by_month"]),
        "operator": resolve_path(config["outputs"]["asrs_fatigue_summary_by_operator"]),
        "location": resolve_path(config["outputs"]["asrs_fatigue_summary_by_location"]),
        "theme": resolve_path(config["outputs"]["asrs_fatigue_summary_by_theme"]),
    }

    for path in output_paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)

    output_paths["comparison"].write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    scored.to_csv(output_paths["scored"], index=False)
    month_summary.to_csv(output_paths["month"], index=False)
    operator_summary.to_csv(output_paths["operator"], index=False)
    location_summary.to_csv(output_paths["location"], index=False)
    theme_summary.to_csv(output_paths["theme"], index=False)

    LOGGER.info("Wrote benchmark comparison to %s", output_paths["comparison"])
    LOGGER.info("Wrote scored ASRS output to %s", output_paths["scored"])
    LOGGER.info("Wrote monthly fatigue summary to %s", output_paths["month"])
    LOGGER.info("Wrote operator fatigue summary to %s", output_paths["operator"])
    LOGGER.info("Wrote location fatigue summary to %s", output_paths["location"])
    LOGGER.info("Wrote theme fatigue summary to %s", output_paths["theme"])


def main() -> None:
    """Run the second ASRS fatigue benchmark end-to-end."""
    benchmark_one_summary, benchmark_one_predictions = load_benchmark_one_outputs()
    base = load_asrs_nlp_output()
    features = load_asrs_fatigue_features()

    if base.empty or features.empty:
        raise ValueError("ASRS benchmark 2 requires both the enriched NLP output and fatigue features.")

    merged = merge_inputs(base, features)
    summary_two, benchmark_two_predictions = fit_and_validate(merged)
    comparison = build_comparison_summary(benchmark_one_summary, summary_two)

    selected_model = comparison["comparison"]["selected_model"]
    scored = build_scored_output(
        merged[
            [
                "report_id",
                "event_date",
                "location",
                "aircraft_operator",
                "theme_primary_label",
                "fatigue_confidence_tier",
                "weak_fatigue_label",
            ]
        ].copy(),
        benchmark_one_predictions,
        benchmark_two_predictions,
        selected_model,
    )

    month_summary = build_group_summary(scored, "event_month").rename(
        columns={"event_month": "event_month"}
    )
    operator_summary = build_group_summary(scored, "aircraft_operator")
    location_summary = build_group_summary(scored, "location")
    theme_summary = build_group_summary(scored, "theme_primary_label")

    comparison["selected_model"] = selected_model
    comparison["selected_model_metrics"] = (
        summary_two["metrics"] if selected_model == "benchmark_2_hybrid_text_plus_features" else benchmark_one_summary["metrics"]
    )
    comparison["benchmark_2_summary"] = summary_two

    persist_outputs(
        comparison,
        scored,
        month_summary,
        operator_summary,
        location_summary,
        theme_summary,
    )


if __name__ == "__main__":
    main()
