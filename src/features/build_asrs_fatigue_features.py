"""Transparent ASRS fatigue feature engineering for the second benchmark.

This module builds a small feature table from the
rule-enriched ASRS pilot output. It keeps the target proxy label available
for modeling convenience while adding only narrative-derived features:
text length, explicit fatigue language, rest/sleep/duty context, hypothetical
counterfactual cues, and operational-noise counts that correspond to the
main false-positive patterns seen in the first benchmark.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

from src.common.config import load_config, resolve_path
from src.common.logging_utils import get_logger
from src.common.validation import (
    standardize_columns,
    validate_no_duplicates,
    validate_required_columns,
)


LOGGER = get_logger(__name__)

INPUT_REQUIRED_COLUMNS = [
    "report_id",
    "event_date",
    "narrative_clean",
]
TARGET_COLUMN = "weak_fatigue_label"

FATIGUE_EXPLICIT_TERMS = [
    "fatigue",
    "fatigued",
    "tired",
    "tiredness",
    "exhausted",
    "exhaustion",
    "sleepy",
    "drowsy",
    "worn out",
]
FATIGUE_CONTEXT_TERMS = [
    "rest period",
    "rest break",
    "inadequate rest",
    "minimal rest",
    "poor rest",
    "short rest",
    "sleep",
    "lack of sleep",
    "sleep deprived",
    "sleep deprivation",
    "overnight duty",
    "extended duty",
    "long duty day",
    "duty period",
    "circadian",
    "late night",
    "early morning",
    "reduced alertness",
]
HYPOTHETICAL_FATIGUE_PATTERNS = [
    r"\bif(?:\s+\w+){0,5}\s+(?:tired|tiredness|fatigue|fatigued|sleepy|drowsy|"
    r"exhausted|exhaustion|sharp|alert|alertness)\b",
    r"\b(?:could|might|may|would)\s+have(?:\s+been)?(?:\s+\w+){0,5}\s+"
    r"(?:tired|tiredness|fatigue|fatigued|sleepy|drowsy|exhausted|exhaustion|"
    r"sharp|alert|alertness)\b",
    r"\bif\s+not\s+sharp\b",
    r"\bnot\s+sharp\b",
]
OPERATIONAL_THEME_TERMS: dict[str, list[str]] = {
    "communication": [
        "communication",
        "communications",
        "miscommunication",
        "misunderstood",
        "misheard",
        "readback",
        "hearback",
        "coordination",
        "phraseology",
        "clarification",
    ],
    "workload": [
        "workload",
        "task saturated",
        "task saturation",
        "busy",
        "overloaded",
        "overload",
        "rushed",
        "hectic",
        "time pressure",
    ],
    "distraction": [
        "distraction",
        "distracted",
        "distracting",
        "interrupted",
        "interruption",
        "diverted attention",
        "attention diverted",
        "lost focus",
        "loss of focus",
        "startled",
        "startle",
    ],
    "procedure": [
        "checklist",
        "checklists",
        "procedure",
        "procedures",
        "procedural",
        "sop",
        "sops",
        "standard operating procedure",
        "missed step",
        "omitted",
        "skipped",
        "not completed",
        "failed to complete",
    ],
    "approach_landing": [
        "unstable approach",
        "unstabilized approach",
        "approach became unstable",
        "unstable on final",
        "unstable final",
        "hard landing",
        "go around",
        "missed approach",
        "late runway change",
        "bounced landing",
        "landing long",
        "landed long",
        "below glide slope",
        "above glide slope",
    ],
    "ground_taxi": [
        "taxiway",
        "runway incursion",
        "ground incursion",
        "surface movement",
        "hold short",
        "pushback",
        "tow bar",
        "taxi conflict",
        "ground conflict",
    ],
}

FEATURE_COLUMNS = [
    "narrative_word_count",
    "narrative_char_count",
    "sentence_count",
    "first_person_pronoun_count",
    "explicit_fatigue_term_count",
    "fatigue_context_term_count",
    "fatigue_keyword_count",
    "explicit_fatigue_clause_count",
    "context_fatigue_clause_count",
    "fatigue_clause_count",
    "hypothetical_fatigue_clause_count",
    "hypothetical_fatigue_flag",
    "operational_communication_term_count",
    "operational_workload_term_count",
    "operational_distraction_term_count",
    "operational_procedure_term_count",
    "operational_approach_landing_term_count",
    "operational_ground_taxi_term_count",
    "operational_noise_count",
    "fatigue_density",
    "operational_density",
    "fatigue_clause_share",
    "fatigue_to_noise_ratio",
]

FIRST_PERSON_PATTERN = r"\b(?:i|we|my|our|me|us|mine|ours)\b"


def coerce_text(value: object) -> str:
    """Return a safe string representation for text matching."""
    if pd.isna(value):
        return ""
    return str(value)


def clean_text_for_review(value: object) -> str:
    """Lowercase and normalize whitespace while preserving readable punctuation."""
    text = unicodedata.normalize("NFKC", coerce_text(value))
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    return re.sub(r"\s+", " ", text.lower()).strip()


def normalize_for_matching(value: object) -> str:
    """Normalize text into a space-delimited form for transparent phrase matching."""
    text = clean_text_for_review(value)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def split_clauses(text: str) -> list[str]:
    """Split a narrative into coarse clauses for clause-level features."""
    return [clause.strip() for clause in re.split(r"[.!?;]+", text) if clause.strip()]


def find_phrase_matches(text: str, phrases: list[str]) -> list[str]:
    """Return the distinct phrase rules matched in a normalized text blob."""
    if not text:
        return []

    padded_text = f" {text} "
    return [phrase for phrase in phrases if f" {phrase} " in padded_text]


def has_hypothetical_fatigue_signal(text: str) -> bool:
    """Detect counterfactual fatigue phrasing at the clause level."""
    for clause in split_clauses(text):
        clause_match_text = normalize_for_matching(clause)
        if not clause_match_text:
            continue
        if any(re.search(pattern, clause_match_text) for pattern in HYPOTHETICAL_FATIGUE_PATTERNS):
            return True
    return False


def count_pattern_occurrences(text: str, pattern: str) -> int:
    """Count word-level regex matches in normalized text."""
    return len(re.findall(pattern, text))


class ASRSFatigueFeatureEngineer(BaseEstimator, TransformerMixin):
    """Derive transparent narrative-only fatigue features from ASRS reports."""

    def __init__(self, text_column: str = "narrative_clean") -> None:
        self.text_column = text_column

    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> "ASRSFatigueFeatureEngineer":
        """No-op fit for scikit-learn compatibility."""
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform ASRS narratives into a compact feature table."""
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)

        frame = standardize_columns(X)
        validate_required_columns(frame, INPUT_REQUIRED_COLUMNS)
        validate_no_duplicates(frame, ["report_id"])

        if self.text_column not in frame.columns:
            raise ValueError(f"Missing text column: {self.text_column}")

        work = frame.copy()
        work[self.text_column] = work[self.text_column].fillna("").astype(str)

        if TARGET_COLUMN in work.columns:
            target_series = pd.to_numeric(work[TARGET_COLUMN], errors="coerce")
            if target_series.isna().any():
                raise ValueError("weak_fatigue_label contains null or non-numeric values.")
            work[TARGET_COLUMN] = target_series.astype(int)

        feature_rows = work[self.text_column].apply(self._derive_feature_row)
        feature_frame = pd.DataFrame(feature_rows.tolist(), index=work.index)

        output_columns = ["report_id", "event_date"]
        if TARGET_COLUMN in work.columns:
            output_columns.append(TARGET_COLUMN)

        output = work[output_columns].copy()
        output = pd.concat([output, feature_frame], axis=1)
        output = output[output_columns + FEATURE_COLUMNS]
        return output.reset_index(drop=True)

    def _derive_feature_row(self, value: object) -> dict[str, Any]:
        """Compute row-level narrative features."""
        raw_text = clean_text_for_review(value)
        normalized_text = normalize_for_matching(value)
        clauses = [normalize_for_matching(clause) for clause in split_clauses(raw_text)]

        explicit_matches = find_phrase_matches(normalized_text, FATIGUE_EXPLICIT_TERMS)
        context_matches = find_phrase_matches(normalized_text, FATIGUE_CONTEXT_TERMS)
        explicit_clause_count = 0
        context_clause_count = 0
        fatigue_clause_count = 0
        hypothetical_clause_count = 0

        for clause in clauses:
            explicit_clause_matches = find_phrase_matches(clause, FATIGUE_EXPLICIT_TERMS)
            context_clause_matches = find_phrase_matches(clause, FATIGUE_CONTEXT_TERMS)
            if explicit_clause_matches:
                explicit_clause_count += 1
            if context_clause_matches:
                context_clause_count += 1
            if explicit_clause_matches or context_clause_matches:
                fatigue_clause_count += 1
            if any(re.search(pattern, clause) for pattern in HYPOTHETICAL_FATIGUE_PATTERNS):
                hypothetical_clause_count += 1

        operational_counts = {
            f"operational_{theme}_term_count": len(find_phrase_matches(normalized_text, phrases))
            for theme, phrases in OPERATIONAL_THEME_TERMS.items()
        }
        operational_noise_count = sum(operational_counts.values())

        word_count = len(re.findall(r"\b[a-z0-9]+\b", normalized_text))
        sentence_count = len(clauses)
        first_person_pronoun_count = count_pattern_occurrences(
            normalized_text, FIRST_PERSON_PATTERN
        )
        fatigue_keyword_count = len(explicit_matches) + len(context_matches)
        fatigue_density = round(fatigue_keyword_count / word_count, 6) if word_count else 0.0
        operational_density = (
            round(operational_noise_count / word_count, 6) if word_count else 0.0
        )
        fatigue_clause_share = (
            round(fatigue_clause_count / sentence_count, 6) if sentence_count else 0.0
        )
        fatigue_to_noise_ratio = (
            round(fatigue_keyword_count / operational_noise_count, 6)
            if operational_noise_count
            else float(fatigue_keyword_count)
        )

        feature_row: dict[str, Any] = {
            "narrative_word_count": int(word_count),
            "narrative_char_count": int(len(raw_text)),
            "sentence_count": int(sentence_count),
            "first_person_pronoun_count": int(first_person_pronoun_count),
            "explicit_fatigue_term_count": int(len(explicit_matches)),
            "fatigue_context_term_count": int(len(context_matches)),
            "fatigue_keyword_count": int(fatigue_keyword_count),
            "explicit_fatigue_clause_count": int(explicit_clause_count),
            "context_fatigue_clause_count": int(context_clause_count),
            "fatigue_clause_count": int(fatigue_clause_count),
            "hypothetical_fatigue_clause_count": int(hypothetical_clause_count),
            "hypothetical_fatigue_flag": int(has_hypothetical_fatigue_signal(raw_text)),
            "operational_noise_count": int(operational_noise_count),
            "fatigue_density": fatigue_density,
            "operational_density": operational_density,
            "fatigue_clause_share": fatigue_clause_share,
            "fatigue_to_noise_ratio": fatigue_to_noise_ratio,
        }
        feature_row.update({key: int(value) for key, value in operational_counts.items()})
        return feature_row


def load_asrs_nlp_output() -> pd.DataFrame:
    """Load the ASRS NLP pilot output from the analytics layer."""
    config = load_config()
    input_path = resolve_path(config["outputs"]["asrs_nlp_enriched"])
    if not input_path.exists():
        LOGGER.warning("ASRS NLP enriched input was not found at %s", input_path)
        return pd.DataFrame()

    frame = pd.read_csv(input_path, low_memory=False)
    frame = standardize_columns(frame)
    LOGGER.info("Loaded ASRS NLP input from %s with %s row(s)", input_path, len(frame))
    return frame


def build_asrs_fatigue_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Build the fatigue feature table from the rule-enriched ASRS pilot."""
    if frame.empty:
        return pd.DataFrame(columns=["report_id", "event_date", TARGET_COLUMN, *FEATURE_COLUMNS])

    engineer = ASRSFatigueFeatureEngineer()
    features = engineer.transform(frame)

    LOGGER.info("Built ASRS fatigue features with %s row(s) and %s column(s)", *features.shape)
    LOGGER.info(
        "Feature totals: explicit_fatigue_term_count=%s | hypothetical_fatigue_flag=%s | "
        "operational_noise_count=%s",
        int(features["explicit_fatigue_term_count"].sum()),
        int(features["hypothetical_fatigue_flag"].sum()),
        int(features["operational_noise_count"].sum()),
    )
    return features


def persist_asrs_fatigue_features(frame: pd.DataFrame) -> None:
    """Write the fatigue feature table to the configured analytics output path."""
    config = load_config()
    output_path = resolve_path(config["outputs"]["asrs_fatigue_features"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if frame.empty:
        frame.to_csv(output_path, index=False)
        LOGGER.warning(
            "No ASRS fatigue features were available; wrote an empty CSV to %s",
            output_path,
        )
        return

    frame.to_csv(output_path, index=False)
    LOGGER.info("Wrote ASRS fatigue features to %s", output_path)


def main() -> None:
    """Run the ASRS fatigue feature engineering pipeline end-to-end."""
    frame = load_asrs_nlp_output()
    features = build_asrs_fatigue_features(frame)
    persist_asrs_fatigue_features(features)


if __name__ == "__main__":
    main()
