"""Rule-based ASRS NLP baseline for the Jan-Feb 2025 pilot.

This module uses the trusted public NASA ASRS extract as a voluntary
safety-report and fatigue proxy. The output is intentionally lightweight,
transparent, and suitable for manual review before any supervised ML step.
"""

from __future__ import annotations

import re
import unicodedata

import pandas as pd

from src.common.config import load_config, resolve_path
from src.common.logging_utils import get_logger
from src.common.validation import (
    standardize_columns,
    validate_no_duplicates,
    validate_required_columns,
)


LOGGER = get_logger(__name__)

ASRS_REQUIRED_COLUMNS = [
    "report_id",
    "event_date",
    "location",
    "aircraft_operator",
    "narrative",
    "human_factors",
]
ASRS_OPTIONAL_TEXT_COLUMNS = [
    "assessments_contributing_factors_situations",
    "assessments_primary_problem",
    "narrative_synopsis",
]

FATIGUE_KEYWORD_RULES = [
    "fatigue",
    "fatigued",
    "tired",
    "tiredness",
    "exhausted",
    "exhaustion",
    "drowsy",
    "sleepy",
    "sleep",
    "lack of sleep",
    "sleep deprived",
    "sleep deprivation",
    "reduced alertness",
    "alertness",
    "long duty day",
    "extended duty",
    "duty period",
    "circadian",
    "rest period",
    "inadequate rest",
    "minimal rest",
    "poor rest",
    "short rest",
    "overnight duty",
    "rest break",
    "poor rest break",
]
FATIGUE_STRONG_RULES = [
    "fatigue",
    "fatigued",
    "tired",
    "tiredness",
    "exhausted",
    "exhaustion",
    "drowsy",
    "sleepy",
    "lack of sleep",
    "sleep deprived",
    "sleep deprivation",
    "reduced alertness",
    "long duty day",
    "extended duty",
    "duty period",
    "circadian",
    "rest period",
    "inadequate rest",
    "minimal rest",
    "poor rest",
    "short rest",
    "overnight duty",
    "rest break",
    "poor rest break",
]
FATIGUE_SLEEP_REST_RULES = [
    "sleep",
    "lack of sleep",
    "sleep deprived",
    "sleep deprivation",
    "rest period",
    "inadequate rest",
    "minimal rest",
    "poor rest",
    "short rest",
    "overnight duty",
    "extended duty",
    "long duty day",
    "rest break",
    "poor rest break",
]
FATIGUE_ALERTNESS_PERFORMANCE_RULES = [
    "alertness",
    "reduced alertness",
    "performance",
    "attention",
    "focus",
    "workload",
    "time pressure",
    "task saturated",
    "busy",
    "circadian",
]
FATIGUE_CONTEXT_RULES = [
    "long duty day",
    "extended duty",
    "duty period",
    "circadian",
    "rest period",
    "inadequate rest",
    "minimal rest",
    "poor rest",
    "short rest",
    "overnight duty",
    "rest break",
    "poor rest break",
]
HYPOTHETICAL_FATIGUE_PATTERNS = [
    r"\bif(?:\s+\w+){0,5}\s+(?:tired|tiredness|fatigue|fatigued|sleepy|drowsy|exhausted|exhaustion|sharp|alert|alertness)\b",
    r"\b(?:could|might|may|would)\s+have(?:\s+been)?(?:\s+\w+){0,5}\s+(?:tired|tiredness|fatigue|fatigued|sleepy|drowsy|exhausted|exhaustion|sharp|alert|alertness)\b",
    r"\bif\s+not\s+sharp\b",
    r"\bnot\s+sharp\b",
]

THEME_RULES: dict[str, list[str]] = {
    "fatigue": FATIGUE_KEYWORD_RULES,
    "communication": [
        "communication",
        "communication breakdown",
        "miscommunication",
        "misunderstood",
        "misheard",
        "readback",
        "hearback",
        "coordination",
        "phraseology",
        "clarification",
        "communications",
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
        "startle",
        "startled",
    ],
    "workload": [
        "workload",
        "high workload",
        "task saturated",
        "task saturation",
        "busy",
        "overloaded",
        "overload",
        "rushed",
        "hectic",
        "time pressure",
    ],
    "procedure_checklist": [
        "checklist",
        "checklists",
        "check list",
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
    "ground_taxi_conflict": [
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
    "approach_landing_instability": [
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
}

THEME_PRIORITY = [
    "fatigue",
    "communication",
    "distraction",
    "workload",
    "ground_taxi_conflict",
    "approach_landing_instability",
    "procedure_checklist",
]

OUTPUT_COLUMNS = [
    "report_id",
    "event_date",
    "location",
    "aircraft_operator",
    "narrative",
    "human_factors",
    "assessments_contributing_factors_situations",
    "assessments_primary_problem",
    "narrative_clean",
    "fatigue_keyword_flag",
    "fatigue_keyword_count",
    "fatigue_confidence_tier",
    "weak_fatigue_label",
    "theme_fatigue_flag",
    "theme_communication_flag",
    "theme_distraction_flag",
    "theme_workload_flag",
    "theme_procedure_checklist_flag",
    "theme_ground_taxi_conflict_flag",
    "theme_approach_landing_instability_flag",
    "theme_primary_label",
]


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


def join_normalized_text(values: list[object]) -> str:
    """Join multiple text fields into one normalized matching string."""
    parts = [normalize_for_matching(value) for value in values]
    return " ".join(part for part in parts if part)


def find_phrase_matches(text: str, phrases: list[str]) -> list[str]:
    """Return the distinct phrase rules matched in a normalized text blob."""
    if not text:
        return []

    padded_text = f" {text} "
    return [phrase for phrase in phrases if f" {phrase} " in padded_text]


def has_hypothetical_fatigue_signal(text: str) -> bool:
    """Detect counterfactual fatigue phrasing that should stay low confidence."""
    for clause in re.split(r"[.!?;]+", text):
        clause_match_text = normalize_for_matching(clause)
        if not clause_match_text:
            continue
        if any(re.search(pattern, clause_match_text) for pattern in HYPOTHETICAL_FATIGUE_PATTERNS):
            return True
    return False


def pick_primary_theme(theme_matches: dict[str, list[str]]) -> str:
    """Pick the strongest matched theme using match count and a deterministic tie-break."""
    best_theme = "none"
    best_score = 0
    best_rank = len(THEME_PRIORITY)

    for rank, theme in enumerate(THEME_PRIORITY):
        score = len(theme_matches.get(theme, []))
        if score > best_score or (score == best_score and score > 0 and rank < best_rank):
            best_theme = theme
            best_score = score
            best_rank = rank

    return best_theme


def load_trusted_asrs() -> pd.DataFrame:
    """Load the trusted ASRS pilot file from the configured analytics inputs."""
    config = load_config()
    trusted_path = resolve_path(config["outputs"]["trusted_asrs_table"])
    if not trusted_path.exists():
        raise FileNotFoundError(f"Trusted ASRS file was not found at {trusted_path}")

    frame = pd.read_csv(trusted_path, low_memory=False, dtype=str)
    frame = standardize_columns(frame)
    LOGGER.info("Loaded trusted ASRS input from %s with %s row(s)", trusted_path, len(frame))
    return frame


def filter_pilot_window(frame: pd.DataFrame) -> pd.DataFrame:
    """Keep only the Jan-Feb 2025 pilot window and standardize event_date formatting."""
    config = load_config()
    pilot_start = pd.Timestamp(config["project"]["pilot_window_start"])
    pilot_end = pd.Timestamp(config["project"]["pilot_window_end"])

    filtered = frame.copy()
    parsed_dates = pd.to_datetime(filtered["event_date"], errors="coerce")
    invalid_dates = int(parsed_dates.isna().sum())
    if invalid_dates:
        LOGGER.warning("Dropping %s ASRS row(s) with invalid event_date values.", invalid_dates)

    valid_mask = parsed_dates.notna()
    filtered = filtered.loc[valid_mask].copy()
    parsed_dates = parsed_dates.loc[valid_mask]

    in_window_mask = parsed_dates.between(pilot_start, pilot_end)
    outside_window = int((~in_window_mask).sum())
    if outside_window:
        LOGGER.info("Dropping %s ASRS row(s) outside the Jan-Feb 2025 pilot window.", outside_window)

    filtered = filtered.loc[in_window_mask].copy()
    parsed_dates = parsed_dates.loc[in_window_mask]
    filtered["event_date"] = parsed_dates.dt.strftime("%Y-%m-%d")
    return filtered.reset_index(drop=True)


def derive_row_features(row: pd.Series) -> pd.Series:
    """Derive rule-based NLP features for a single trusted ASRS record."""
    narrative_clean = clean_text_for_review(row["narrative"])
    narrative_match_text = normalize_for_matching(row["narrative"])
    structured_match_text = join_normalized_text(
        [row.get(column, "") for column in ASRS_OPTIONAL_TEXT_COLUMNS] + [row.get("human_factors", "")]
    )
    analysis_text = " ".join(part for part in [narrative_match_text, structured_match_text] if part)

    fatigue_keyword_matches = find_phrase_matches(analysis_text, FATIGUE_KEYWORD_RULES)
    structured_fatigue_matches = find_phrase_matches(structured_match_text, FATIGUE_STRONG_RULES)
    narrative_fatigue_matches = find_phrase_matches(narrative_match_text, FATIGUE_STRONG_RULES)
    contextual_fatigue_matches = find_phrase_matches(narrative_match_text, FATIGUE_CONTEXT_RULES)
    hypothetical_fatigue_signal = has_hypothetical_fatigue_signal(narrative_clean)
    narrative_sleep_rest_matches = find_phrase_matches(narrative_match_text, FATIGUE_SLEEP_REST_RULES)
    narrative_alertness_matches = find_phrase_matches(
        narrative_match_text, FATIGUE_ALERTNESS_PERFORMANCE_RULES
    )

    fatigue_keyword_flag = int(bool(fatigue_keyword_matches))
    fatigue_keyword_count = len(fatigue_keyword_matches)
    fatigue_confidence_tier = "low_or_none"
    explicit_fatigue_signal = bool(structured_fatigue_matches) or (
        bool(narrative_fatigue_matches) and not hypothetical_fatigue_signal
    )
    contextual_fatigue_signal = bool(contextual_fatigue_matches) or (
        bool(narrative_sleep_rest_matches) and bool(narrative_alertness_matches)
    )

    if explicit_fatigue_signal:
        fatigue_confidence_tier = "high"
    elif hypothetical_fatigue_signal:
        fatigue_confidence_tier = "low_or_none"
    elif contextual_fatigue_signal:
        fatigue_confidence_tier = "medium"

    weak_fatigue_label = int(fatigue_confidence_tier in {"high", "medium"})

    theme_matches = {
        theme: find_phrase_matches(analysis_text, phrases)
        for theme, phrases in THEME_RULES.items()
    }
    theme_primary_label = pick_primary_theme(theme_matches)
    if theme_primary_label == "communication" and explicit_fatigue_signal:
        theme_primary_label = "fatigue"

    return pd.Series(
        {
            "narrative_clean": narrative_clean,
            "fatigue_keyword_flag": fatigue_keyword_flag,
            "fatigue_keyword_count": fatigue_keyword_count,
            "fatigue_confidence_tier": fatigue_confidence_tier,
            "weak_fatigue_label": weak_fatigue_label,
            "theme_fatigue_flag": int(bool(theme_matches["fatigue"])),
            "theme_communication_flag": int(bool(theme_matches["communication"])),
            "theme_distraction_flag": int(bool(theme_matches["distraction"])),
            "theme_workload_flag": int(bool(theme_matches["workload"])),
            "theme_procedure_checklist_flag": int(bool(theme_matches["procedure_checklist"])),
            "theme_ground_taxi_conflict_flag": int(bool(theme_matches["ground_taxi_conflict"])),
            "theme_approach_landing_instability_flag": int(
                bool(theme_matches["approach_landing_instability"])
            ),
            "theme_primary_label": theme_primary_label,
        }
    )


def build_asrs_nlp_baseline(frame: pd.DataFrame) -> pd.DataFrame:
    """Build the pilot ASRS NLP enrichment table."""
    if frame.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    validate_required_columns(frame, ASRS_REQUIRED_COLUMNS)
    validate_no_duplicates(frame, ["report_id"])

    required_null_counts = frame[ASRS_REQUIRED_COLUMNS].isna().sum().to_dict()
    LOGGER.info("Required ASRS null counts before NLP enrichment: %s", required_null_counts)

    enriched = filter_pilot_window(frame)
    if enriched.empty:
        LOGGER.warning("No ASRS rows remained after pilot-window filtering.")
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    for column in ASRS_OPTIONAL_TEXT_COLUMNS:
        if column not in enriched.columns:
            enriched[column] = ""

    feature_frame = enriched.apply(derive_row_features, axis=1)
    enriched = pd.concat([enriched, feature_frame], axis=1)

    for column in OUTPUT_COLUMNS:
        if column not in enriched.columns:
            enriched[column] = ""

    enriched = enriched[OUTPUT_COLUMNS]

    LOGGER.info("Built ASRS NLP baseline with %s row(s) and %s column(s)", *enriched.shape)
    LOGGER.info(
        "Fatigue keyword flag count: %s | Weak fatigue label count: %s",
        int(enriched["fatigue_keyword_flag"].sum()),
        int(enriched["weak_fatigue_label"].sum()),
    )
    LOGGER.info(
        "Primary label distribution: %s",
        enriched["theme_primary_label"].value_counts(dropna=False).to_dict(),
    )
    return enriched


def persist_asrs_nlp_baseline(frame: pd.DataFrame) -> None:
    """Write the ASRS NLP enrichment to the configured analytics output path."""
    config = load_config()
    output_path = resolve_path(config["outputs"]["asrs_nlp_enriched"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if frame.empty:
        frame.to_csv(output_path, index=False)
        LOGGER.warning(
            "No ASRS NLP baseline rows were available; wrote an empty CSV to %s",
            output_path,
        )
        return

    frame.to_csv(output_path, index=False)
    LOGGER.info("Wrote ASRS NLP baseline output to %s", output_path)


def main() -> None:
    """Run the pilot ASRS NLP baseline end-to-end."""
    trusted_asrs = load_trusted_asrs()
    enriched = build_asrs_nlp_baseline(trusted_asrs)
    persist_asrs_nlp_baseline(enriched)


if __name__ == "__main__":
    main()
