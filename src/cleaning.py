"""Field-aware cleaning helpers for CBDB identifiers and historical years.

Sentinels are never replaced globally: callers must opt into a field semantic.
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


DEFAULT_YEAR_SENTINELS = frozenset({-9999, -999, -1, 0})
DEFAULT_ID_SENTINELS = frozenset({-10000, -9999, -999, -1, 0})


def valid_historical_year_sql(
    column_sql: str,
    lower_bound: int = -1200,
    upper_bound: int = 2100,
    sentinels: Iterable[int] = DEFAULT_YEAR_SENTINELS,
) -> str:
    """Return a SQL predicate for fields whose semantics are calendar years."""
    sentinel_sql = ",".join(str(int(value)) for value in sorted(set(sentinels)))
    return (
        f"{column_sql} IS NOT NULL AND {column_sql} NOT IN ({sentinel_sql}) "
        f"AND {column_sql} BETWEEN {int(lower_bound)} AND {int(upper_bound)}"
    )


def clean_historical_year(
    values: pd.Series,
    lower_bound: int = -1200,
    upper_bound: int = 2100,
    sentinels: Iterable[int] = DEFAULT_YEAR_SENTINELS,
) -> pd.Series:
    """Clean a known year field while preserving its original companion column."""
    numeric = pd.to_numeric(values, errors="coerce").astype("Float64")
    valid = numeric.between(lower_bound, upper_bound) & ~numeric.isin(set(sentinels))
    return numeric.where(valid)


def clean_person_identifier(
    values: pd.Series,
    sentinels: Iterable[int] = DEFAULT_ID_SENTINELS,
) -> pd.Series:
    """Clean a field known to contain CBDB person IDs; never create a person-0 node."""
    numeric = pd.to_numeric(values, errors="coerce").astype("Int64")
    return numeric.mask(numeric.isin(set(sentinels)))


def sentinel_counts(values: pd.Series, sentinels: Iterable[int]) -> dict[str, int]:
    numeric = pd.to_numeric(values, errors="coerce")
    return {str(value): int(numeric.eq(value).sum()) for value in sentinels}

