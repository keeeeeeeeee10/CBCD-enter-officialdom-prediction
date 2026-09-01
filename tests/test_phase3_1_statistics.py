import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs/phase3_1/tables"


def test_prediction_artifact_schema_and_headline_metrics():
    path = ROOT / "data/phase3_1/final_model_test_predictions.parquet"
    data = pd.read_parquet(path)
    assert list(data.columns) == [
        "person_id", "population", "model_id", "y_true", "y_probability_raw",
        "y_probability_calibrated", "frozen_threshold", "split",
    ]
    assert len(data) == 436_881
    assert set(data["population"]) == {"Global", "Song", "Ming"}
    assert set(data["model_id"]) == {"H_STRUCT", "D5_MAIN", "D6_UPPER"}
    assert data["split"].eq("test").all()
    assert data["y_true"].isin([0, 1]).all()
    assert data[["y_probability_raw", "y_probability_calibrated"]].apply(lambda s: s.between(0, 1).all()).all()

    reported = pd.read_csv(ROOT / "outputs/phase3/tables/main_model_performance.csv").set_index(["population", "model_id"])
    for keys, group in data.groupby(["population", "model_id"], sort=False):
        y = group["y_true"].to_numpy()
        p = group["y_probability_raw"].to_numpy()
        row = reported.loc[keys]
        assert np.isclose(roc_auc_score(y, p), row["roc_auc"], atol=5e-10)
        assert np.isclose(average_precision_score(y, p), row["pr_auc"], atol=5e-10)
        assert np.isclose(log_loss(y, p), row["log_loss"], atol=5e-10)
        assert np.isclose(brier_score_loss(y, p), row["brier_score"], atol=5e-10)


def test_recomputed_metrics_and_table3_are_consistent():
    audit = pd.read_csv(TABLES / "final_metric_recomputation.csv")
    assert len(audit) == 90
    assert audit["status"].eq("PASS").all()
    assert np.allclose(audit["recomputed"], audit["reported"], atol=5e-10, equal_nan=True)
    tex = (ROOT / "paper/revised/tables/table3_performance.tex").read_text(encoding="utf-8")
    assert all(term in tex for term in ["Raw LogLoss", "Raw Brier", "Validation-calibrated ECE"])
    main = pd.read_csv(ROOT / "outputs/phase3/tables/main_model_performance.csv")
    for row in main.itertuples(index=False):
        assert f"{row.roc_auc:.4f}" in tex
        assert f"{row.pr_auc:.4f}" in tex


def test_physical_geography_interval_is_not_mismatched():
    data = pd.read_csv(TABLES / "grouped_ablation_corrected.csv")
    row = data.loc[(data["population"] == "Global") & (data["feature_block"] == "Physical geography")].iloc[0]
    assert row["comparison"] == "A3 - A2"
    assert pd.isna(row["roc_ci_lower"]) and pd.isna(row["roc_ci_upper"])
    assert pd.isna(row["pr_ci_lower"]) and pd.isna(row["pr_ci_upper"])
    assert "not retained" in row["ci_status"].lower().replace("_", " ")
    tex = (ROOT / "paper/revised/tables/table4_ablation.tex").read_text(encoding="utf-8")
    physical_line = next(line for line in tex.splitlines() if line.startswith("Physical geography"))
    assert physical_line.count("--") == 2
    assert "exact paired prediction pair" in tex
    assert not (TABLES / "physical_geography_exact_bootstrap.csv").exists()
    appendix = (ROOT / "paper/revised/tables/tableA3_full_ablation.tex").read_text(encoding="utf-8")
    appendix_lines = [line for line in appendix.splitlines() if "& Physical geography & A3 - A2 &" in line]
    assert len(appendix_lines) == 3
    assert all(line.count("--") == 2 and "[" not in line for line in appendix_lines)


def test_every_retained_interval_contains_its_point_estimate():
    data = pd.read_csv(TABLES / "grouped_ablation_corrected.csv")
    for metric, point in [("roc", "delta_roc_auc"), ("pr", "delta_pr_auc")]:
        lower, upper = f"{metric}_ci_lower", f"{metric}_ci_upper"
        complete = data[[lower, upper]].notna().all(axis=1)
        partial = data[[lower, upper]].notna().any(axis=1) & ~complete
        assert not partial.any()
        assert (data.loc[complete, lower] <= data.loc[complete, point]).all()
        assert (data.loc[complete, point] <= data.loc[complete, upper]).all()


def test_table5_values_match_frozen_robustness_summary():
    tex = (ROOT / "paper/revised/tables/table5_robustness.tex").read_text(encoding="utf-8")
    robust = pd.read_csv(ROOT / "outputs/phase3/tables/robustness_summary.csv")
    shown = robust.loc[
        ((robust["protocol"] == "Matched-support spatial") & (robust["population"] == "Global"))
        | ((robust["protocol"] == "Family-group holdout") & robust["population"].isin(["Global", "Ming"]))
    ]
    for row in shown.itertuples(index=False):
        assert f"{row.shift_roc_auc:.4f}" in tex
        assert f"{row.delta_roc_auc:+.4f}" in tex
    assert "SPLIT\\_ONLY\\_NO\\_LOCKED\\_PERFORMANCE" in tex
    assert "SOURCE\\_GROUP\\_CONFIRMATION\\_NOT\\_FEASIBLE" in tex
