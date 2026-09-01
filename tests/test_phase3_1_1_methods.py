from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from src.feature_builders import load_yaml
from src.geography import FoldSafeLocalEntryEncoder, MISSING_REGION


def test_local_prior_spec_matches_frozen_code_and_config() -> None:
    spec = json.loads(
        (ROOT / "outputs/phase3_1_1/methods/local_target_prior_spec.json").read_text()
    )
    config = load_yaml(ROOT / "configs/phase2_6_features.yaml")
    assert spec["region_key"] == config["region_key"] == "addr_id"
    assert spec["smoothing"]["alpha"] == config["local_prior_alpha"] == 20.0
    assert spec["training_encoding"]["folds"] == config["local_prior_oof_folds"] == 5
    assert spec["training_encoding"]["seed"] == 42
    assert spec["grouping"]["hierarchical"] is False
    assert spec["grouping"]["minimum_group_size_status"] == "NOT_USED"
    assert MISSING_REGION == "__MISSING__"


def test_training_oof_value_does_not_use_its_own_label() -> None:
    regions = pd.Series(["r1"] * 20 + ["r2"] * 20)
    ids = pd.Series(np.arange(40))
    y1 = pd.Series(([0, 1] * 20), dtype=float)
    y2 = y1.copy()
    target_index = 7
    y2.iloc[target_index] = 1.0 - y2.iloc[target_index]
    encoded1 = FoldSafeLocalEntryEncoder(alpha=20.0, n_folds=5, seed=42).fit_transform_train(
        regions, y1, ids
    )
    encoded2 = FoldSafeLocalEntryEncoder(alpha=20.0, n_folds=5, seed=42).fit_transform_train(
        regions, y2, ids
    )
    assert encoded1.iloc[target_index] == encoded2.iloc[target_index]


def test_forward_transform_has_no_label_argument_and_uses_training_only_mapping() -> None:
    encoder = FoldSafeLocalEntryEncoder(alpha=20.0, n_folds=5, seed=42)
    encoder.fit(pd.Series(["r1", "r1", "r2", "r2"]), pd.Series([0, 1, 1, 1]))
    assert list(encoder.transform(pd.Series(["r1", "r2"]))) == [
        encoder.mapping_["r1"], encoder.mapping_["r2"]
    ]
    assert tuple(FoldSafeLocalEntryEncoder.transform.__annotations__) == ("regions", "return")


def test_unseen_and_missing_fallback_rules_match_implementation() -> None:
    encoder = FoldSafeLocalEntryEncoder(alpha=20.0, n_folds=5, seed=42)
    encoder.fit(pd.Series(["r1", "r1", None]), pd.Series([0, 1, 1]))
    observed_missing = encoder.transform(pd.Series([None])).iloc[0]
    unseen = encoder.transform(pd.Series(["never-seen"])).iloc[0]
    assert observed_missing == encoder.mapping_[MISSING_REGION]
    assert unseen == encoder.global_prior_


def test_operating_parameter_table_uses_not_retained_instead_of_reconstruction() -> None:
    table = pd.read_csv(ROOT / "outputs/phase3_1_1/tables/operating_parameters.csv")
    assert len(table) == 12
    assert set(table["numeric_class_weights"]) == {"NOT_RETAINED"}
    logistic = table.loc[table["model_id"].eq("Logistic M6")]
    assert set(logistic["calibrator"]) == {"NOT_RETAINED"}
    assert set(logistic["sigmoid_coefficient"]) == {"NOT_RETAINED"}
