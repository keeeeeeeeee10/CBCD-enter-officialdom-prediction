#!/usr/bin/env python3
"""Audit frozen metrics and create Phase 3.1 statistical correction artifacts.

This script does not train a model, select a split, or alter any Phase 1--3
artifact. It only reads frozen outputs, removes the invalid A3-A2 interval
borrowed from the older G3-G2 contrast, verifies retained intervals, and
exports reviewable final-model predictions.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/phase3_1/tables"
DATA_OUT = ROOT / "data/phase3_1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def expected_calibration_error(y: np.ndarray, probability: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0.0, 1.0, bins + 1)
    bucket = np.clip(np.digitize(probability, edges[1:-1], right=True), 0, bins - 1)
    value = 0.0
    for index in range(bins):
        mask = bucket == index
        if mask.any():
            value += float(mask.mean()) * abs(float(y[mask].mean()) - float(probability[mask].mean()))
    return float(value)


def close(left: float, right: float, tolerance: float = 5e-7) -> bool:
    return bool(np.isclose(float(left), float(right), atol=tolerance, rtol=0))


def verify_final_model_metrics() -> tuple[pd.DataFrame, list[dict[str, object]]]:
    source_path = ROOT / "data/phase2_6/predictions/final_model_predictions.parquet"
    predictions = pd.read_parquet(source_path)
    expected_models = {"H_STRUCT", "D5_MAIN", "D6_UPPER"}
    expected_populations = {"Global", "Song", "Ming"}
    assert set(predictions["model_id"]) == expected_models
    assert set(predictions["population"]) == expected_populations
    assert predictions["split"].eq("test").all()
    assert predictions["seed"].eq(42).all()
    assert not predictions[["person_id", "population", "model_id"]].duplicated().any()
    assert predictions["y_probability_calibrated_if_available"].notna().all()

    metrics = pd.read_csv(ROOT / "outputs/phase2_6/tables/final_model_metrics.csv")
    calibration = pd.read_csv(ROOT / "outputs/phase2_6/tables/final_model_calibration.csv")
    records: list[dict[str, object]] = []
    for (population, model_id), frame in predictions.groupby(["population", "model_id"], sort=True):
        y = frame["y_true"].to_numpy(dtype=np.int8)
        raw = frame["y_probability_raw"].to_numpy(dtype=float)
        calibrated = frame["y_probability_calibrated_if_available"].to_numpy(dtype=float)
        observed = {
            "roc_auc": roc_auc_score(y, raw),
            "pr_auc": average_precision_score(y, raw),
            "log_loss": log_loss(y, raw, labels=[0, 1]),
            "brier_score": brier_score_loss(y, raw),
            "raw_ece": expected_calibration_error(y, raw),
            "calibrated_ece": expected_calibration_error(y, calibrated),
            "calibrated_log_loss": log_loss(y, calibrated, labels=[0, 1]),
            "calibrated_brier": brier_score_loss(y, calibrated),
            "prevalence": float(y.mean()),
            "n_test": int(len(frame)),
        }
        metric_row = metrics.loc[
            metrics["population"].eq(population) & metrics["model_id"].eq(model_id)
        ].iloc[0]
        calibration_row = calibration.loc[
            calibration["population"].eq(population) & calibration["model_id"].eq(model_id)
        ].iloc[0]
        comparisons = {
            "roc_auc": metric_row["roc_auc"],
            "pr_auc": metric_row["pr_auc"],
            "log_loss": metric_row["log_loss"],
            "brier_score": metric_row["brier_score"],
            "raw_ece": metric_row["raw_ece"],
            "calibrated_ece": metric_row["calibrated_ece"],
            "calibrated_log_loss": calibration_row["calibrated_log_loss"],
            "calibrated_brier": calibration_row["calibrated_brier"],
            "prevalence": metric_row["test_positive_rate"],
            "n_test": metric_row["n_test"],
        }
        for name, reported in comparisons.items():
            if name == "n_test":
                passed = int(observed[name]) == int(reported)
            else:
                passed = close(observed[name], reported)
            if not passed:
                raise AssertionError(f"{population}/{model_id}/{name} mismatch: {observed[name]} vs {reported}")
            records.append({
                "population": population,
                "model_id": model_id,
                "quantity": name,
                "recomputed": observed[name],
                "reported": reported,
                "status": "PASS",
                "source": str(source_path.relative_to(ROOT)),
            })

    export = predictions.rename(columns={
        "y_probability_calibrated_if_available": "y_probability_calibrated"
    })[[
        "person_id", "population", "model_id", "y_true", "y_probability_raw",
        "y_probability_calibrated", "frozen_threshold", "split",
    ]].copy()
    export = export.sort_values(["population", "model_id", "person_id"]).reset_index(drop=True)
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    export_path = DATA_OUT / "final_model_test_predictions.parquet"
    export.to_parquet(export_path, index=False, compression="zstd")
    return pd.DataFrame(records), [{
        "item": "final_model_test_predictions",
        "status": "PASS",
        "evidence": str(export_path.relative_to(ROOT)),
        "detail": f"{len(export):,} de-identified person-model rows; zstd; SHA256 {sha256(export_path)}",
    }]


def correct_grouped_ablation() -> tuple[pd.DataFrame, list[dict[str, object]]]:
    source_path = ROOT / "outputs/phase3/tables/grouped_ablation_summary.csv"
    frame = pd.read_csv(source_path)
    physical = frame["feature_block"].eq("Physical geography")
    assert physical.sum() == 3
    assert frame.loc[physical, "comparison"].eq("A3 - A2").all()

    # Phase 2.6 retained only A2/A3 summary rows and prediction hashes. No
    # person-level A2/A3 probability artifact was retained. The old G2/G3
    # parquet is a different feature definition and must not supply this CI.
    address_metrics = pd.read_csv(ROOT / "outputs/phase2_6/tables/address_semantics_decomposition.csv")
    assert set(address_metrics.loc[address_metrics["model_id"].isin(["A2", "A3"]), "model_id"]) == {"A2", "A3"}
    old_predictions = pd.read_parquet(
        ROOT / "data/phase2_5/predictions/parts/geography_decomposition_predictions_test.parquet",
        columns=["model_id"],
    )
    assert not set(old_predictions["model_id"]).intersection({"A2", "A3"})
    final_predictions = pd.read_parquet(
        ROOT / "data/phase2_6/predictions/final_model_predictions.parquet",
        columns=["model_id"],
    )
    assert not set(final_predictions["model_id"]).intersection({"A2", "A3"})

    frame.loc[physical, ["roc_ci_lower", "roc_ci_upper", "pr_ci_lower", "pr_ci_upper"]] = np.nan
    frame.loc[physical, "ci_status"] = "EXACT_PAIRED_PREDICTIONS_NOT_RETAINED"

    checked = 0
    for row in frame.itertuples(index=False):
        for prefix, estimate in [("roc", row.delta_roc_auc), ("pr", row.delta_pr_auc)]:
            lower = getattr(row, f"{prefix}_ci_lower")
            upper = getattr(row, f"{prefix}_ci_upper")
            if pd.isna(lower) and pd.isna(upper):
                continue
            if pd.isna(lower) != pd.isna(upper):
                raise AssertionError(f"Partial interval for {row.population}/{row.comparison}/{prefix}")
            if not float(lower) <= float(estimate) <= float(upper):
                raise AssertionError(
                    f"Point estimate outside CI for {row.population}/{row.comparison}/{prefix}: "
                    f"{estimate} not in [{lower}, {upper}]"
                )
            checked += 1

    destination = OUT / "grouped_ablation_corrected.csv"
    frame.to_csv(destination, index=False)
    manifest = [
        {
            "item": "Table 4 Physical Geography CI",
            "status": "CORRECTED_TO_NOT_AVAILABLE",
            "evidence": str(destination.relative_to(ROOT)),
            "detail": "A3-A2 point estimates retained; old G3-G2 intervals removed; exact A2/A3 paired predictions were not retained.",
        },
        {
            "item": "retained_interval_point_containment",
            "status": "PASS",
            "evidence": str(destination.relative_to(ROOT)),
            "detail": f"{checked} metric intervals checked with lower <= point estimate <= upper.",
        },
    ]
    return frame, manifest


def verify_table_sources(corrected_ablation: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    headline = pd.read_csv(ROOT / "outputs/phase3/tables/main_model_performance.csv")
    final = pd.read_csv(ROOT / "outputs/phase2_6/tables/final_model_metrics.csv")
    final_keys = final.set_index(["population", "model_id"])
    for row in headline.loc[headline["model_id"].isin(["H_STRUCT", "D5_MAIN", "D6_UPPER"])].itertuples(index=False):
        source = final_keys.loc[(row.population, row.model_id)]
        for name, source_name in [
            ("roc_auc", "roc_auc"), ("pr_auc", "pr_auc"), ("log_loss", "log_loss"),
            ("brier_score", "brier_score"), ("calibrated_ece", "calibrated_ece"),
            ("test_positive_rate", "test_positive_rate"), ("n_test", "n_test"),
        ]:
            passed = close(getattr(row, name), source[source_name]) if name != "n_test" else int(getattr(row, name)) == int(source[source_name])
            if not passed:
                raise AssertionError(f"Table 3 mismatch for {row.population}/{row.model_id}/{name}")
            rows.append({"table": "Table 3", "population": row.population, "item": f"{row.model_id}/{name}", "status": "PASS"})

    robustness = pd.read_csv(ROOT / "outputs/phase3/tables/robustness_summary.csv")
    spatial = pd.read_csv(ROOT / "outputs/phase2_6/tables/matched_random_vs_spatial_results.csv")
    for row in robustness.loc[robustness["protocol"].eq("Matched-support spatial")].itertuples(index=False):
        source = spatial.loc[
            spatial["population"].eq(row.population) & spatial["model_id"].eq(row.model_id)
        ].iloc[0]
        mappings = [
            ("reference_roc_auc", "matched_random_roc_auc"),
            ("shift_roc_auc", "matched_spatial_roc_auc"),
            ("delta_roc_auc", "delta_spatial_minus_random_roc_auc"),
            ("reference_pr_auc", "matched_random_pr_auc"),
            ("shift_pr_auc", "matched_spatial_pr_auc"),
            ("delta_pr_auc", "delta_spatial_minus_random_pr_auc"),
        ]
        for target_name, source_name in mappings:
            if not close(getattr(row, target_name), source[source_name]):
                raise AssertionError(f"Table 5 mismatch for {row.population}/{row.model_id}/{target_name}")
            rows.append({"table": "Table 5", "population": row.population, "item": f"{row.model_id}/{target_name}", "status": "PASS"})

    assert (corrected_ablation.loc[corrected_ablation["feature_block"].eq("Physical geography"), "ci_status"] == "EXACT_PAIRED_PREDICTIONS_NOT_RETAINED").all()
    rows.append({"table": "Table 4", "population": "All", "item": "A3-A2 interval identity", "status": "PASS_AFTER_CORRECTION"})

    multiseed = pd.read_csv(ROOT / "outputs/phase2_6/tables/multiseed_model_metrics.csv")
    observed_seeds = sorted(int(value) for value in multiseed["seed"].dropna().unique())
    assert observed_seeds == [42, 202, 2024, 2025, 2026]
    summary = pd.read_csv(ROOT / "outputs/phase2_6/tables/multiseed_delta_summary.csv")
    for summary_row in summary.itertuples(index=False):
        model_b, _, model_a = summary_row.comparison.partition(" - ")
        subset = multiseed.loc[
            multiseed["population"].eq(summary_row.population)
            & multiseed["model_id"].isin([model_a, model_b]),
            ["seed", "model_id", summary_row.metric],
        ]
        wide = subset.pivot(index="seed", columns="model_id", values=summary_row.metric).dropna()
        if len(wide) != 5:
            raise AssertionError(f"Incomplete five-seed pair for {summary_row.population}/{summary_row.comparison}")
        delta = wide[model_b] - wide[model_a]
        checks = {
            "mean_delta": delta.mean(),
            "std_delta": delta.std(ddof=1),
            "min_delta": delta.min(),
            "max_delta": delta.max(),
            "median_delta": delta.median(),
            "n_positive_seeds": int((delta > 0).sum()),
            "n_seeds": int(len(delta)),
        }
        for name, value in checks.items():
            reported = getattr(summary_row, name)
            passed = int(value) == int(reported) if name.startswith("n_") else close(value, reported)
            if not passed:
                raise AssertionError(
                    f"Multi-seed mismatch for {summary_row.population}/{summary_row.comparison}/{summary_row.metric}/{name}"
                )
    rows.append({
        "table": "Appendix", "population": "All",
        "item": "five-seed summaries (48 rows)", "status": "PASS",
    })

    return pd.DataFrame(rows), [
        {
            "item": "Tables 3-5 and appendix source alignment",
            "status": "PASS_AFTER_CORRECTION",
            "evidence": "outputs/phase3_1/tables/statistics_verification.csv",
            "detail": "Headline metrics, matched-support shift values, ablation contrast identity, prevalence, and five-seed set verified.",
        }
    ]


def write_calibration_comparison() -> dict[str, object]:
    frame = pd.read_csv(ROOT / "outputs/phase2_6/tables/final_model_calibration.csv").rename(columns={
        "raw_ece": "Raw ECE",
        "calibrated_ece": "Validation-calibrated ECE",
        "raw_brier": "Raw Brier",
        "calibrated_brier": "Validation-calibrated Brier",
        "raw_log_loss": "Raw LogLoss",
        "calibrated_log_loss": "Validation-calibrated LogLoss",
    })
    destination = OUT / "raw_vs_validation_calibrated_metrics.csv"
    frame.to_csv(destination, index=False)
    return {
        "item": "raw_vs_calibrated_probability_metrics",
        "status": "PASS",
        "evidence": str(destination.relative_to(ROOT)),
        "detail": "Raw and validation-fitted sigmoid metrics are explicitly separated; no test-fitted calibration is used.",
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    recomputed, prediction_manifest = verify_final_model_metrics()
    recomputed.to_csv(OUT / "final_metric_recomputation.csv", index=False)
    corrected_ablation, ablation_manifest = correct_grouped_ablation()
    verification, table_manifest = verify_table_sources(corrected_ablation)
    verification.to_csv(OUT / "statistics_verification.csv", index=False)
    calibration_manifest = write_calibration_comparison()

    manifest = pd.DataFrame(
        prediction_manifest + ablation_manifest + table_manifest + [calibration_manifest]
    )
    manifest.to_csv(OUT / "statistical_correction_manifest.csv", index=False)
    payload = {
        "status": "PASS",
        "independent_unit": "person_id on the frozen test partition",
        "paired_bootstrap_rule": "same person IDs, same y_true, exact model pair",
        "bootstrap_seed": 42,
        "physical_geography_comparison": "A3 - A2",
        "physical_geography_exact_predictions_retained": False,
        "physical_geography_ci_action": "CI set to not available; old G3-G2 CI rejected",
        "point_inside_every_retained_ci": True,
        "final_predictions": {
            "path": "data/phase3_1/final_model_test_predictions.parquet",
            "sha256": sha256(DATA_OUT / "final_model_test_predictions.parquet"),
        },
    }
    (OUT / "statistics_audit_status.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
