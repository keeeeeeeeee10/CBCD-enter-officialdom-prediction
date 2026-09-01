from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.feature_builders import load_yaml
from src.utils import sha256_file


ROOT = Path(__file__).resolve().parents[1]


def test_frozen_hashes_and_master_shape() -> None:
    expected = load_yaml("configs/phase2_5_protocol.yaml")["expected_sha256"]
    paths = {
        "database": "database/cbdb_20260829.sqlite3",
        "target": "data/interim/person_target.parquet",
        "base": "data/processed/person_base_v0.parquet",
        "primary": "data/splits/split_primary_dynasty_target.parquet",
        "random": "data/splits/split_random_benchmark.parquet",
        "family": "data/splits/split_family_group_robustness.parquet",
        "temporal": "data/splits/split_safe_temporal.parquet",
    }
    for key, path in paths.items():
        assert sha256_file(ROOT / path) == expected[key]
    master = pd.read_parquet(ROOT / "data/modeling/person_phase2_features.parquet", columns=["person_id", "target_entry_v1"])
    assert len(master) == 661_124
    assert master["person_id"].is_unique
    assert int(master["target_entry_v1"].sum()) == 220_627


def test_forbidden_features_are_not_registered() -> None:
    registry = load_yaml("configs/phase2_5_features.yaml")
    text = str(registry["feature_sets"])
    for forbidden in ["raw_index_year", "index_year", "c_index_year", "target_posting", "family_group_id"]:
        assert forbidden not in text
