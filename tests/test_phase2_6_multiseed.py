from pathlib import Path

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_complete_fixed_seed_matrix_without_best_seed_selection():
    metrics = pd.read_csv(ROOT / "outputs/phase2_6/tables/multiseed_model_metrics.csv")
    assert set(metrics["seed"].astype(int)) == {42, 202, 2024, 2025, 2026}
    expected_models = {"F2", "F3", "F4", "D5", "D6", "D6i", "H_STRUCT"}
    assert set(metrics["model_id"]) == expected_models
    assert metrics.groupby(["population", "model_id"])["seed"].nunique().eq(5).all()
    config = yaml.safe_load((ROOT / "configs/phase2_6_models.yaml").read_text())
    assert config["canonical_seed"] == 42
    assert config["lock_policy"]["select_best_seed"] is False
    summary = pd.read_csv(ROOT / "outputs/phase2_6/tables/multiseed_delta_summary.csv")
    assert summary["n_seeds"].eq(5).all()
    small = summary.loc[summary["metric"].eq("roc_auc") & summary["mean_delta"].abs().lt(0.002)]
    assert small["practical_magnitude"].eq("small").all()
