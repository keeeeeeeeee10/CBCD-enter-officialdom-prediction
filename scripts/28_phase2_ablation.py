#!/usr/bin/env python3
"""Compute primary-split feature ablations with paired uncertainty intervals."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import atomic_to_csv, load_yaml
from src.metrics import binary_metrics, paired_bootstrap_metric_deltas
from src.utils import setup_logging


PREDICTION_FILES = {
    "LogisticRegression": PROJECT_ROOT / "data/modeling/phase2_predictions_logistic.parquet",
    "CatBoost": PROJECT_ROOT / "data/modeling/phase2_predictions_catboost.parquet",
}
POPULATIONS = ["Global", "Song", "Ming"]
ABLATION_STEPS = [
    ("M0", "M0b", "safe_birth_cohort", "nested"),
    ("M0b", "M1", "personal", "nested"),
    ("M1", "M2", "geography", "nested"),
    ("M2", "M3", "family_structure", "nested"),
    ("M3", "M4", "family_capital", "nested"),
    ("M4", "M6", "documentation_addition", "nested"),
    ("M0", "M5", "documentation_only", "benchmark"),
]


def ordered_prediction(frame: pd.DataFrame, population: str, feature_set: str) -> pd.DataFrame:
    subset = frame.loc[
        frame["population"].eq(population) & frame["feature_set"].eq(feature_set)
    ].sort_values("person_id")
    if subset.empty:
        raise RuntimeError(f"Missing primary predictions for {population}/{feature_set}")
    if subset["person_id"].duplicated().any():
        raise RuntimeError(f"Duplicate primary predictions for {population}/{feature_set}")
    return subset.reset_index(drop=True)


def main() -> int:
    logger = setup_logging("phase2_ablation", PROJECT_ROOT / "outputs/logs/phase2_ablation.log")
    model_config = load_yaml("configs/phase2_models.yaml")
    n_resamples = int(os.environ.get("PHASE2_BOOTSTRAP_RESAMPLES", model_config["bootstrap_resamples"]))
    confidence = float(model_config["bootstrap_confidence"])
    predictions = {}
    for algorithm, path in PREDICTION_FILES.items():
        if not path.exists():
            raise RuntimeError(f"Missing primary prediction file: {path}")
        predictions[algorithm] = pd.read_parquet(path)

    rows: list[dict[str, object]] = []
    documentation_rows: list[dict[str, object]] = []
    for algorithm, frame in predictions.items():
        for population in POPULATIONS:
            for baseline_feature, extension_feature, block, comparison_type in ABLATION_STEPS:
                baseline = ordered_prediction(frame, population, baseline_feature)
                extension = ordered_prediction(frame, population, extension_feature)
                if not np.array_equal(baseline["person_id"].to_numpy(), extension["person_id"].to_numpy()):
                    raise RuntimeError(
                        f"Ablation rows are not paired for {algorithm}/{population}/{baseline_feature}->{extension_feature}"
                    )
                y = baseline["y_true"].astype(int).to_numpy()
                baseline_probability = baseline["y_probability"].to_numpy(dtype=float)
                extension_probability = extension["y_probability"].to_numpy(dtype=float)
                baseline_metrics = binary_metrics(y, baseline_probability, 0.5)
                extension_metrics = binary_metrics(y, extension_probability, 0.5)
                interval = paired_bootstrap_metric_deltas(
                    y,
                    baseline_probability,
                    extension_probability,
                    n_resamples=n_resamples,
                    seed=42,
                    confidence=confidence,
                )
                row = {
                    "algorithm": algorithm,
                    "population": population,
                    "baseline_feature_set": baseline_feature,
                    "extension_feature_set": extension_feature,
                    "feature_block": block,
                    "comparison_type": comparison_type,
                    "split_protocol": "primary",
                    "evaluation_split": "test",
                    "n_test": len(baseline),
                    "baseline_roc_auc": baseline_metrics["roc_auc"],
                    "extension_roc_auc": extension_metrics["roc_auc"],
                    "delta_roc_auc": extension_metrics["roc_auc"] - baseline_metrics["roc_auc"],
                    "baseline_pr_auc": baseline_metrics["pr_auc"],
                    "extension_pr_auc": extension_metrics["pr_auc"],
                    "delta_pr_auc": extension_metrics["pr_auc"] - baseline_metrics["pr_auc"],
                    "baseline_log_loss": baseline_metrics["log_loss"],
                    "extension_log_loss": extension_metrics["log_loss"],
                    "delta_log_loss": extension_metrics["log_loss"] - baseline_metrics["log_loss"],
                    **interval,
                }
                rows.append(row)
                if extension_feature in {"M5", "M6"} or baseline_feature in {"M5", "M6"}:
                    documentation_rows.append(row.copy())
                logger.info(
                    "%s/%s %s->%s: delta ROC-AUC=%.4f",
                    algorithm,
                    population,
                    baseline_feature,
                    extension_feature,
                    row["delta_roc_auc"],
                )

    output = pd.DataFrame(rows).sort_values(
        ["algorithm", "population", "baseline_feature_set", "extension_feature_set"]
    )
    atomic_to_csv(output, PROJECT_ROOT / "outputs/phase2/tables/ablation_results.csv")
    documentation = pd.DataFrame(documentation_rows).sort_values(
        ["algorithm", "population", "baseline_feature_set", "extension_feature_set"]
    )
    atomic_to_csv(documentation, PROJECT_ROOT / "outputs/phase2/tables/documentation_bias_results.csv")
    logger.info("Ablation complete: %d comparisons; bootstrap=%d", len(output), n_resamples)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
