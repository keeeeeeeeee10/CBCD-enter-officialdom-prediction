"""Shared definitions for Phase 1.5 target and temporal audits."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.cleaning import clean_historical_year, valid_historical_year_sql


MAJOR_DYNASTIES = ("Tang", "Song", "Yuan", "Ming", "Qing")


def phase15_year_settings(config: dict[str, Any]) -> tuple[int, int, tuple[int, ...]]:
    section = config["phase1_5"]
    return (
        int(section["historical_year_lower_bound"]),
        int(section["historical_year_upper_bound"]),
        tuple(int(value) for value in section["year_sentinels"]),
    )


def year_predicate(column_sql: str, config: dict[str, Any]) -> str:
    lower, upper, sentinels = phase15_year_settings(config)
    return valid_historical_year_sql(column_sql, lower, upper, sentinels)


def clean_year_series(series: pd.Series, config: dict[str, Any]) -> pd.Series:
    lower, upper, sentinels = phase15_year_settings(config)
    return clean_historical_year(series, lower, upper, sentinels)


def safe_divide(numerator: int | float, denominator: int | float) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0

