"""Phase 2 family feature helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd


def smoothed_ratio(
    positive_count: pd.Series,
    eligible_count: pd.Series,
    prior: float,
    alpha: float = 20.0,
) -> pd.Series:
    numerator = pd.to_numeric(positive_count, errors="coerce").fillna(0.0)
    denominator = pd.to_numeric(eligible_count, errors="coerce").fillna(0.0)
    values = (numerator + alpha * float(prior)) / (denominator + alpha)
    return values.replace([np.inf, -np.inf], np.nan).astype(float)


def training_family_prior(positive_count: pd.Series, eligible_count: pd.Series) -> float:
    positives = float(pd.to_numeric(positive_count, errors="coerce").fillna(0.0).sum())
    eligible = float(pd.to_numeric(eligible_count, errors="coerce").fillna(0.0).sum())
    return positives / eligible if eligible > 0 else 0.0
