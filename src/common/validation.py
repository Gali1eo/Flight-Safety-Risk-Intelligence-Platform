"""Basic validation helpers for trusted and analytics data layers."""

from __future__ import annotations

import re
from collections.abc import Iterable

import pandas as pd


def to_snake_case(value: str) -> str:
    """Convert a column name to snake_case."""
    normalized = re.sub(r"[^0-9a-zA-Z]+", "_", value).strip("_")
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", normalized).lower()


def standardize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with snake_case column names."""
    standardized = frame.copy()
    standardized.columns = [to_snake_case(column) for column in standardized.columns]
    return standardized


def validate_required_columns(frame: pd.DataFrame, required_columns: Iterable[str]) -> None:
    """Raise an error if required columns are missing."""
    missing_columns = sorted(set(required_columns) - set(frame.columns))
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")


def validate_null_threshold(frame: pd.DataFrame, threshold: float) -> None:
    """Raise an error if any column exceeds the allowed null ratio."""
    null_ratios = frame.isna().mean()
    failing_columns = null_ratios[null_ratios > threshold]
    if not failing_columns.empty:
        summary = failing_columns.round(3).to_dict()
        raise ValueError(f"Null threshold exceeded: {summary}")


def validate_no_duplicates(frame: pd.DataFrame, key_columns: list[str]) -> None:
    """Raise an error if duplicate key rows are found."""
    duplicate_count = int(frame.duplicated(subset=key_columns).sum())
    if duplicate_count:
        raise ValueError(
            f"Found {duplicate_count} duplicate rows for keys {key_columns}"
        )


def mask_identifier_columns(frame: pd.DataFrame, id_columns: Iterable[str]) -> pd.DataFrame:
    """Mask direct identifier fields before analytics-layer publication."""
    masked = frame.copy()
    for column in id_columns:
        if column in masked.columns:
            masked[column] = "***MASKED***"
    return masked
