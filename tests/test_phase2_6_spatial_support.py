import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def test_matched_support_ids_and_zero_group_overlap():
    overlap = json.loads((ROOT / "outputs/phase2_6/tables/matched_spatial_overlap_check.json").read_text())
    assert overlap["status"] == "PASS"
    for population in ["global", "song", "ming"]:
        random = pd.read_parquet(ROOT / f"data/phase2_6/splits/matched_random_{population}.parquet")
        spatial = pd.read_parquet(ROOT / f"data/phase2_6/splits/matched_spatial_{population}.parquet")
        assert set(random["person_id"]) == set(spatial["person_id"])
        groups = {part: set(spatial.loc[spatial["split"].eq(part), "spatial_group_id"]) for part in ["train", "validation", "test"]}
        assert not groups["train"] & groups["validation"]
        assert not groups["train"] & groups["test"]
        assert not groups["validation"] & groups["test"]


def test_matched_results_are_not_claimed_paired():
    results = pd.read_csv(ROOT / "outputs/phase2_6/tables/matched_random_vs_spatial_results.csv")
    assert len(results) == 6
    assert not results["paired_individual_bootstrap_used"].astype(bool).any()
    assert results["interpretation"].eq("matched-support spatial distribution-shift sensitivity").all()
