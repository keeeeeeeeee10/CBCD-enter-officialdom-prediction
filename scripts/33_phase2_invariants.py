#!/usr/bin/env python3
"""Validate the complete Phase 2 delivery and print the final PASS banner."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import atomic_to_csv
from src.utils import atomic_write_text, sha256_file, setup_logging


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    logger = setup_logging("phase2_invariants", PROJECT_ROOT / "outputs/logs/phase2_invariants.log")
    errors: list[str] = []
    tables = PROJECT_ROOT / "outputs/phase2/tables"
    data = PROJECT_ROOT / "data/modeling"

    freeze = json.loads((PROJECT_ROOT / "outputs/tables/data_foundation_freeze_manifest.json").read_text(encoding="utf-8"))
    require(freeze.get("status") == "DATA_FOUNDATION_FROZEN_FOR_PHASE2", "Frozen foundation status is invalid", errors)
    feature_validation = json.loads((tables / "feature_validation.json").read_text(encoding="utf-8"))
    require(feature_validation.get("status") == "PASS", "Feature validation is not PASS", errors)
    require(feature_validation.get("n_people") == 661_124, "Feature validation person count changed", errors)
    require(feature_validation.get("v1_positive") == 220_627, "Feature validation V1 count changed", errors)
    require(feature_validation.get("forbidden_predictor_overlap") == [], "Forbidden predictors entered the registry", errors)

    feature_frame = pd.read_parquet(data / "person_phase2_features.parquet", columns=["person_id", "target_entry_v1"])
    require(len(feature_frame) == 661_124, "Phase 2 feature table person count changed", errors)
    require(not feature_frame["person_id"].duplicated().any(), "Phase 2 feature table has duplicate people", errors)
    require(int(feature_frame["target_entry_v1"].sum()) == 220_627, "Phase 2 feature table target changed", errors)

    split_hashes = {
        "primary_split_sha256": sha256_file(PROJECT_ROOT / "data/splits/split_primary_dynasty_target.parquet"),
        "family_split_sha256": sha256_file(PROJECT_ROOT / "data/splits/split_family_group_robustness.parquet"),
        "temporal_split_sha256": sha256_file(PROJECT_ROOT / "data/splits/split_safe_temporal.parquet"),
    }
    for key, observed in split_hashes.items():
        require(observed == freeze.get(key), f"Frozen {key} changed", errors)

    metrics = pd.read_csv(tables / "model_metrics.csv")
    require(len(metrics) == 120, "Primary model metric row count is not 120", errors)
    require(metrics["algorithm"].value_counts().to_dict() == {"LogisticRegression": 72, "CatBoost": 48}, "Primary algorithm counts are incomplete", errors)
    grouped_primary = metrics.groupby(["algorithm", "population", "feature_set"]).size()
    require(
        grouped_primary.loc["LogisticRegression"].eq(3).all()
        and grouped_primary.loc["CatBoost"].eq(2).all(),
        "Primary metrics do not contain the expected threshold/diagnostic rows",
        errors,
    )

    for algorithm, filename in {
        "LogisticRegression": "phase2_predictions_logistic.parquet",
        "CatBoost": "phase2_predictions_catboost.parquet",
    }.items():
        predictions = pd.read_parquet(data / filename)
        require(not predictions.duplicated(["algorithm", "population", "feature_set", "person_id"]).any(), f"Duplicate {algorithm} predictions", errors)
        require(predictions.groupby(["algorithm", "population", "feature_set"]).size().size == 24, f"Incomplete {algorithm} prediction groups", errors)

    ablation = pd.read_csv(tables / "ablation_results.csv")
    require(len(ablation) == 42, "Ablation comparison count is not 42", errors)
    require(ablation["bootstrap_resamples"].eq(500).all(), "Ablation bootstrap count is not 500", errors)
    require((tables / "documentation_bias_results.csv").exists(), "Documentation bias table missing", errors)

    robustness_status = json.loads((tables / "robustness_status.json").read_text(encoding="utf-8"))
    require(robustness_status.get("status") == "PASS", "Robustness status is not PASS", errors)
    require(robustness_status.get("family_rows") == 48, "Family robustness rows are incomplete", errors)
    require(robustness_status.get("temporal_rows") == 32, "Temporal sensitivity rows are incomplete", errors)
    require(robustness_status.get("temporal_supported_populations") == ["Global", "Qing"], "Temporal support audit is inconsistent", errors)
    require(robustness_status.get("temporal_skipped_for_insufficient_partition_support") == ["Song", "Ming"], "Temporal skip audit is inconsistent", errors)
    require((tables / "temporal_support_audit.csv").exists(), "Temporal support audit is missing", errors)
    require(robustness_status.get("prebirth_rows") == 16, "Pre-birth rows are incomplete", errors)
    require(robustness_status.get("qing_holdout_rows") == 16, "Qing holdout rows are incomplete", errors)
    robustness_predictions = pd.read_parquet(data / "phase2_predictions_robustness.parquet")
    require(len(robustness_predictions) > 0, "Robustness predictions are empty", errors)
    require(not robustness_predictions.duplicated(["analysis", "population", "feature_set", "person_id"]).any(), "Duplicate robustness predictions", errors)

    bootstrap = pd.read_csv(tables / "bootstrap_intervals.csv")
    require(len(bootstrap) == 48, "Bootstrap interval count is not 48", errors)
    require(bootstrap["bootstrap_resamples"].eq(500).all(), "Primary bootstrap count is not 500", errors)

    figure_dir = PROJECT_ROOT / "outputs/phase2/figures"
    expected_figures = {
        "phase2_primary_auc.png",
        "phase2_ablation_delta.png",
        "phase2_robustness_auc.png",
        "phase2_feature_importance.png",
        "phase2_population_context.png",
        "phase2_bootstrap_ci.png",
    }
    actual_figures = {path.name for path in figure_dir.glob("*.png")}
    require(expected_figures.issubset(actual_figures), "One or more Phase 2 figures are missing", errors)

    report_path = PROJECT_ROOT / "docs/phase2/phase2_report.md"
    require(report_path.exists(), "Final Phase 2 report is missing", errors)
    if report_path.exists():
        report = report_path.read_text(encoding="utf-8")
        for section in ["## Dataset", "## Feature Coverage", "## Primary Model Results", "## Feature Ablation", "## Documentation Bias", "## Robustness", "## Uncertainty", "## Top Features", "## Scientific Conclusions"]:
            require(section in report, f"Report section missing: {section}", errors)

    readme_path = PROJECT_ROOT / "README.md"
    require(readme_path.exists(), "Root README is missing", errors)
    if readme_path.exists():
        readme = readme_path.read_text(encoding="utf-8")
        for section in ["## Dataset", "## Primary Model Results", "## Robustness", "## Scientific Conclusions"]:
            require(section in readme, f"README report section missing: {section}", errors)
        require("outputs/phase2/figures/phase2_primary_auc.png" in readme, "README figure links are missing", errors)

    status = "PASS" if not errors else "FAIL"
    manifest = {
        "status": status,
        "foundation_status": freeze.get("status"),
        "primary_metric_rows": int(len(metrics)),
        "ablation_rows": int(len(ablation)),
        "robustness_metric_rows": int(robustness_status.get("family_rows", 0) + robustness_status.get("temporal_rows", 0) + robustness_status.get("prebirth_rows", 0) + robustness_status.get("qing_holdout_rows", 0)),
        "bootstrap_interval_rows": int(len(bootstrap)),
        "figure_count": int(len(expected_figures.intersection(actual_figures))),
        "errors": errors,
    }
    atomic_write_text(
        tables / "phase2_run_manifest.json",
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    )
    if errors:
        logger.error("Phase 2 invariants FAIL: %s", errors)
        raise RuntimeError("Phase 2 invariants failed: " + "; ".join(errors))
    logger.info("Phase 2 invariants PASS")
    print("===========================================")
    print("PHASE 2 FEATURE ENGINEERING & MODELING PASS")
    print("===========================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
