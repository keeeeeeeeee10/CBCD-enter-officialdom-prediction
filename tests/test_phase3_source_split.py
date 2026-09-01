import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def test_source_groups_are_target_independent_and_disjoint():
    status = json.loads((ROOT / "outputs/phase3/tables/source_holdout_status.json").read_text())
    membership = pd.read_parquet(ROOT / "data/phase3/source_person_group_membership.parquet")
    assert set(membership.columns) == {"person_id", "source_group_id"}
    assert not membership["person_id"].duplicated().any()
    assert membership["source_group_id"].nunique() == status["source_groups"]
    assert status["target_used_for_group_definition"] is False
    assert status["target_used_for_split_assignment"] is False
    assert status["model_performance_used_for_split_assignment"] is False


def test_source_feasibility_gate_is_respected():
    status = json.loads((ROOT / "outputs/phase3/tables/source_holdout_status.json").read_text())
    split_path = ROOT / "data/phase3/splits/split_source_group_confirmation.parquet"
    if status["status"] == "SOURCE_GROUP_CONFIRMATION_FEASIBLE":
        split = pd.read_parquet(split_path)
        groups = {name: set(part["source_group_id"]) for name, part in split.groupby("split")}
        assert not groups["train"] & groups["validation"]
        assert not groups["train"] & groups["test"]
        assert not groups["validation"] & groups["test"]
    else:
        assert status["status"] == "SOURCE_GROUP_CONFIRMATION_NOT_FEASIBLE"
        assert status["failed_criteria"]
        assert not split_path.exists()
        confirmation = json.loads(
            (ROOT / "outputs/phase3/tables/source_group_confirmation_status.json").read_text()
        )
        assert confirmation["models_trained"] == []
