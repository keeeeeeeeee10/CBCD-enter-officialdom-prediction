#!/usr/bin/env python3
"""Evaluate fixed feature stages for V1, V2a, V2b, and posting targets."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import atomic_to_csv, load_yaml, resolve_feature_set
from src.phase25 import TARGETS, load_phase25_dataset, run_fixed_model, save_analysis_outputs
from src.utils import setup_logging


CAT_MODELS = ["S0", "S1", "S2", "S2i", "SD"]
LOGISTIC_MODELS = ["S0", "S1", "S2", "SD"]


def feature_policy_table() -> pd.DataFrame:
    registry = load_yaml("configs/phase2_5_features.yaml")
    rows = []
    for target in TARGETS:
        model_ids = CAT_MODELS + (["S2p"] if target == "target_posting" else [])
        for model_id in model_ids:
            categorical, numeric = resolve_feature_set(registry, model_id)
            features = categorical + numeric
            forbidden_direct = [feature for feature in features if feature.startswith("target_")]
            focal_posting_predictors = [
                feature for feature in features
                if feature in {"has_posting_record", "n_posting_records", "posting_count", "target_posting"}
            ]
            rows.append({
                "target_name": target,
                "model_id": model_id,
                "n_predictors": len(features),
                "predictors": ";".join(features),
                "direct_target_predictors": ";".join(forbidden_direct),
                "focal_posting_predictors": ";".join(focal_posting_predictors),
                "relative_posting_included": any("ever_posting" in feature or "kin_ever_posting" in feature or "posting_ratio" in feature for feature in features),
                "posting_role": (
                    "separate_relative_posting_sensitivity" if target == "target_posting" and model_id == "S2p"
                    else "relative_ENTRY_capital_primary" if target == "target_posting" and model_id in {"S2", "S2i"}
                    else "not_applicable"
                ),
                "status": "PASS" if not forbidden_direct and not focal_posting_predictors else "FAIL",
            })
    frame = pd.DataFrame(rows)
    if not frame["status"].eq("PASS").all():
        raise RuntimeError("Target sensitivity feature policy failure")
    return frame


def atomic_savefig(figure: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.stem + ".tmp" + path.suffix)
    figure.savefig(temporary, dpi=300, bbox_inches="tight")
    os.replace(temporary, path)
    plt.close(figure)


def heatmap(metrics: pd.DataFrame, path: Path) -> None:
    cat = metrics.loc[
        metrics["algorithm"].eq("CatBoost")
        & metrics["model_id"].isin(CAT_MODELS)
    ].copy()
    rows = []
    labels = []
    for population in ["Global", "Song", "Ming"]:
        for target in TARGETS:
            values = cat.loc[
                cat["population"].eq(population) & cat["target_name"].eq(target)
            ].set_index("model_id").reindex(CAT_MODELS)["roc_auc"]
            rows.append(values.to_numpy())
            labels.append(f"{population} / {target.replace('target_', '')}")
    matrix = np.asarray(rows)
    figure, axis = plt.subplots(figsize=(8, 7))
    image = axis.imshow(matrix, aspect="auto", cmap="viridis", vmin=0.5, vmax=1.0)
    axis.set_xticks(np.arange(len(CAT_MODELS)), CAT_MODELS)
    axis.set_yticks(np.arange(len(labels)), labels)
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            axis.text(column, row, f"{matrix[row, column]:.3f}", ha="center", va="center", color="white" if matrix[row, column] < 0.72 else "black", fontsize=7)
    axis.set_title("CatBoost target-sensitivity ROC-AUC")
    figure.colorbar(image, ax=axis, label="ROC-AUC")
    figure.tight_layout()
    atomic_savefig(figure, path)


def main() -> int:
    logger = setup_logging("phase2_5_targets", PROJECT_ROOT / "outputs/phase2_5/logs/target_sensitivity.log")
    dataset = load_phase25_dataset()
    policy = feature_policy_table()
    atomic_to_csv(policy, PROJECT_ROOT / "outputs/phase2_5/tables/target_sensitivity_feature_policy.csv")
    metrics, tests, validations, metadata = [], [], [], []
    for target_name in TARGETS:
        for algorithm, model_ids in [("CatBoost", CAT_MODELS), ("LogisticRegression", LOGISTIC_MODELS)]:
            for population in ["Global", "Song", "Ming"]:
                for model_id in model_ids:
                    run = run_fixed_model(dataset, population, model_id, algorithm, target_name=target_name)
                    metrics.append(run.metric)
                    tests.append(run.test_predictions)
                    validations.append(run.validation_predictions)
                    metadata.append(run.feature_metadata)
                    logger.info("Target %s %s/%s/%s AUC=%.4f", target_name, algorithm, population, model_id, run.metric["roc_auc"])
    posting_rows = []
    for population in ["Global", "Song", "Ming"]:
        run = run_fixed_model(dataset, population, "S2p", "CatBoost", target_name="target_posting")
        posting_rows.append(run.metric)
        metrics.append(run.metric)
        tests.append(run.test_predictions)
        validations.append(run.validation_predictions)
        metadata.append(run.feature_metadata)
    frame = pd.DataFrame(metrics)
    atomic_to_csv(frame, PROJECT_ROOT / "outputs/phase2_5/tables/target_sensitivity_results.csv")
    atomic_to_csv(pd.DataFrame(posting_rows), PROJECT_ROOT / "outputs/phase2_5/tables/posting_relative_posting_sensitivity.csv")
    save_analysis_outputs("target_sensitivity_predictions", metrics, tests, validations, metadata)
    heatmap(frame, PROJECT_ROOT / "outputs/phase2_5/figures/target_sensitivity_heatmap.png")
    logger.info("Target sensitivity complete: %d models", len(frame))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
