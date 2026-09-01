import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def test_shap_samples_are_frozen_test_people_and_shared():
    sample = pd.read_parquet(ROOT / "data/phase2_6/shap_samples/shap_sample_ids.parquet")
    split = pd.read_parquet(ROOT / "data/splits/split_primary_dynasty_target.parquet")
    test_ids = set(split.loc[split["split"].eq("test"), "person_id"])
    assert set(sample["person_id"]).issubset(test_ids)
    assert sample.groupby("population")["person_id"].nunique().le(10_000).all()
    raw = pd.read_parquet(ROOT / "data/phase2_6/shap_samples/shap_values_sample.parquet")
    for population in ["Global", "Song", "Ming"]:
        model_sets = [set(raw.loc[raw["population"].eq(population) & raw["model_id"].eq(model), "person_id"]) for model in ["H_STRUCT", "D5_MAIN", "D6_UPPER"]]
        assert model_sets[0] == model_sets[1] == model_sets[2]


def test_shap_additivity_and_group_shares():
    check = json.loads((ROOT / "outputs/phase2_6/shap/shap_additivity_check.json").read_text())
    assert check["status"] == "PASS"
    assert check["formal_shap_run"] is True
    assert len(check["checks"]) == 9
    assert all(row["status"] == "PASS" and row["rows_checked"] >= 500 for row in check["checks"])
    groups = pd.read_csv(ROOT / "outputs/phase2_6/shap/shap_group_summary.csv")
    sums = groups.groupby(["model_id", "population"])["group_share_of_total_abs_shap"].sum()
    assert ((sums - 1).abs() < 1e-6).all()
