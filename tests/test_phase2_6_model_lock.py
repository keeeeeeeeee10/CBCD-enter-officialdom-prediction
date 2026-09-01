import json
from pathlib import Path

import pandas as pd

from src.phase26 import FULL_RECORD_FAMILY, FORBIDDEN_STRUCTURAL, validate_locked_feature_sets


ROOT = Path(__file__).resolve().parents[1]


def test_final_model_lock_and_allowlists():
    resolved = validate_locked_feature_sets()
    assert not (set(resolved["H_STRUCT"]["features"]) & FORBIDDEN_STRUCTURAL)
    assert not (set(resolved["D5_MAIN"]["features"]) & FULL_RECORD_FAMILY)
    assert set(resolved["D6_UPPER"]["features"]) - set(resolved["D5_MAIN"]["features"]) == FULL_RECORD_FAMILY
    manifest = json.loads((ROOT / "outputs/phase2_6/tables/final_model_lock_manifest.json").read_text())
    assert manifest["status"] == "FINAL_MODELS_LOCKED"
    assert manifest["canonical_seed"] == 42
    assert manifest["best_seed_selection_performed"] is False
    assert manifest["test_set_used_for_model_selection"] is False


def test_canonical_prediction_alignment_and_models():
    predictions = pd.read_parquet(ROOT / "data/phase2_6/predictions/final_model_predictions.parquet")
    split = pd.read_parquet(ROOT / "data/splits/split_primary_dynasty_target.parquet")
    features = pd.read_parquet(ROOT / "data/modeling/person_phase2_features.parquet", columns=["person_id", "dynasty_name"])
    expected = split.loc[split["split"].eq("test")].merge(features, on="person_id", validate="one_to_one")
    for population in ["Global", "Song", "Ming"]:
        ids = set(expected["person_id"] if population == "Global" else expected.loc[expected["dynasty_name"].eq(population), "person_id"])
        for model in ["H_STRUCT", "D5_MAIN", "D6_UPPER"]:
            observed = predictions.loc[predictions["population"].eq(population) & predictions["model_id"].eq(model)]
            assert set(observed["person_id"]) == ids
            assert (ROOT / f"outputs/phase2_6/models/{population.lower()}/{model}.cbm").stat().st_size > 0
