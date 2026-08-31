#!/usr/bin/env python3
"""Build leakage-controlled personal and SAFE birth-cohort features."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import atomic_to_parquet, ensure_unique_people
from src.utils import setup_logging


def main() -> int:
    logger = setup_logging("phase2_personal", PROJECT_ROOT / "outputs/logs/phase2_personal.log")
    population = pd.read_parquet(
        PROJECT_ROOT / "data/interim/person_modeling_population.parquet",
        columns=["person_id", "dynasty_code", "dynasty", "gender"],
    )
    safe = pd.read_parquet(
        PROJECT_ROOT / "data/interim/person_safe_time_anchor.parquet",
        columns=["person_id", "birth_year", "safe_index_year", "index_year_leakage_class", "safe_index_year_available"],
    )
    frame = population.merge(safe, on="person_id", how="left", validate="one_to_one")
    confirmed = frame["index_year_leakage_class"].eq("SAFE") & frame["safe_index_year_available"].eq(1)
    frame["safe_birth_year"] = pd.to_numeric(frame["safe_index_year"], errors="coerce").where(confirmed)
    frame["safe_birth_decade"] = np.floor(frame["safe_birth_year"] / 10.0) * 10.0
    frame["has_safe_birth_year"] = frame["safe_birth_year"].notna().astype("int8")
    frame["dynasty_name"] = frame["dynasty"].astype("string").fillna("unknown")
    frame["gender"] = frame["gender"].astype("string").fillna("unknown")
    output = frame[[
        "person_id", "dynasty_code", "dynasty_name", "gender",
        "safe_birth_year", "safe_birth_decade", "has_safe_birth_year",
    ]].sort_values("person_id").reset_index(drop=True)
    ensure_unique_people(output)
    if int(output["has_safe_birth_year"].sum()) != 59_851:
        raise RuntimeError("SAFE birth-year count differs from the frozen Phase 1.5 audit")
    atomic_to_parquet(output, PROJECT_ROOT / "data/features/personal_features.parquet")
    logger.info(
        "Personal features complete: people=%d safe_birth=%d (%.2f%%)",
        len(output), int(output["has_safe_birth_year"].sum()), 100 * output["has_safe_birth_year"].mean(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
