from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def test_prediction_rows_are_frozen_test_ids() -> None:
    paths = {
        "predictions_primary_core.parquet": ROOT / "data/splits/split_primary_dynasty_target.parquet",
        "predictions_family_robustness.parquet": ROOT / "data/splits/split_family_group_robustness.parquet",
    }
    for name, split_path in paths.items():
        predictions = pd.read_parquet(ROOT / "data/phase2_5/predictions" / name, columns=["person_id"])
        split = pd.read_parquet(split_path)
        test_ids = set(split.loc[split["split"].eq("test"), "person_id"])
        assert set(predictions["person_id"]).issubset(test_ids)
    spatial = pd.read_parquet(ROOT / "data/phase2_5/predictions/predictions_spatial_robustness.parquet", columns=["person_id", "population"])
    for population, group in spatial.groupby("population"):
        split = pd.read_parquet(ROOT / f"data/phase2_5/splits/split_spatial_group_{population.lower()}.parquet")
        assert set(group["person_id"]).issubset(set(split.loc[split["split"].eq("test"), "person_id"]))


def test_paired_model_ids_align_exactly() -> None:
    predictions = pd.read_parquet(ROOT / "data/phase2_5/predictions/predictions_primary_core.parquet")
    for population in ["Global", "Song", "Ming"]:
        block = predictions.loc[
            predictions["population"].eq(population)
            & predictions["algorithm"].eq("CatBoost")
            & predictions["model_id"].isin(["G4", "G5"])
        ]
        ids = {model: set(group["person_id"]) for model, group in block.groupby("model_id")}
        assert ids["G4"] == ids["G5"]
