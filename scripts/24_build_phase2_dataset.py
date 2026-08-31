#!/usr/bin/env python3
"""Assemble the one-person Phase 2 feature master table without auto-selecting predictors."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import atomic_to_parquet, ensure_unique_people
from src.utils import setup_logging


def load_split(filename: str, column: str) -> pd.DataFrame:
    return pd.read_parquet(PROJECT_ROOT / "data/splits" / filename).rename(columns={"split": column})


def main() -> int:
    logger = setup_logging("phase2_dataset", PROJECT_ROOT / "outputs/logs/phase2_dataset.log")
    personal = pd.read_parquet(PROJECT_ROOT / "data/features/personal_features.parquet")
    geography = pd.read_parquet(PROJECT_ROOT / "data/features/geography_features.parquet")
    structure = pd.read_parquet(PROJECT_ROOT / "data/features/family_structural_features.parquet")
    capital = pd.read_parquet(PROJECT_ROOT / "data/features/family_capital_features.parquet")
    target = pd.read_parquet(
        PROJECT_ROOT / "data/interim/person_target.parquet", columns=["person_id", "target_entry"]
    ).rename(columns={"target_entry": "target_entry_v1"})
    documentation = pd.read_parquet(
        PROJECT_ROOT / "data/interim/person_modeling_population.parquet",
        columns=[
            "person_id", "has_address", "has_kin_record", "has_assoc_record",
            "has_status_record", "has_text_record", "has_institution_record",
            "documentation_intensity",
        ],
    ).rename(columns={
        "has_kin_record": "has_kin",
        "has_assoc_record": "has_assoc",
        "has_status_record": "has_status",
        "has_text_record": "has_text",
        "has_institution_record": "has_institution",
    })
    frame = target.merge(personal, on="person_id", how="left", validate="one_to_one")
    for addition in (geography, structure, capital, documentation):
        frame = frame.merge(addition, on="person_id", how="left", validate="one_to_one")
    for split_frame in (
        load_split("split_primary_dynasty_target.parquet", "split_primary"),
        load_split("split_random_benchmark.parquet", "split_random"),
        load_split("split_family_group_robustness.parquet", "split_family"),
        load_split("split_safe_temporal.parquet", "split_temporal"),
    ):
        frame = frame.merge(split_frame, on="person_id", how="left", validate="one_to_one")
    frame = frame.sort_values("person_id").reset_index(drop=True)
    ensure_unique_people(frame)
    if int(frame["target_entry_v1"].sum()) != 220_627:
        raise RuntimeError("Phase 2 dataset changed the frozen V1 target")
    if frame[["split_primary", "split_random", "split_family", "split_temporal"]].isna().any().any():
        raise RuntimeError("Phase 2 dataset has missing frozen split IDs")
    atomic_to_parquet(frame, PROJECT_ROOT / "data/modeling/person_phase2_features.parquet")
    logger.info("Phase 2 master dataset complete: people=%d columns=%d", len(frame), len(frame.columns))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
