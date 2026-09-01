#!/usr/bin/env python3
"""Evaluate fixed CatBoost models on unseen dynasty-prefecture groups."""

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

from src.feature_builders import atomic_to_csv
from src.phase25 import load_phase25_dataset, prepare_phase25_data, run_fixed_model, save_analysis_outputs
from src.utils import setup_logging


MODELS = ["G0", "G4", "G5", "F2", "F3", "D0", "D6"]


def primary_metrics() -> pd.DataFrame:
    files = [
        "geography_decomposition_results.csv",
        "family_decomposition_results.csv",
        "documentation_controlled_ablation.csv",
    ]
    frame = pd.concat([
        pd.read_csv(PROJECT_ROOT / "outputs/phase2_5/tables" / name) for name in files
    ], ignore_index=True)
    frame = frame.loc[frame["algorithm"].eq("CatBoost") & frame["model_id"].isin(MODELS)]
    return frame.sort_values("model_id").drop_duplicates(["population", "model_id"], keep="first")


def compare(primary: pd.DataFrame, spatial: pd.DataFrame) -> pd.DataFrame:
    merged = primary.merge(
        spatial,
        on=["algorithm", "population", "model_id", "target_name", "subset"],
        suffixes=("_primary", "_spatial"),
        validate="one_to_one",
    )
    output = merged[["algorithm", "population", "model_id", "target_name", "subset"]].copy()
    for metric in ["roc_auc", "pr_auc", "log_loss", "brier_score"]:
        output[f"primary_{metric}"] = merged[f"{metric}_primary"]
        output[f"spatial_{metric}"] = merged[f"{metric}_spatial"]
        output[f"delta_{metric}"] = merged[f"{metric}_spatial"] - merged[f"{metric}_primary"]
    output["primary_n_test"] = merged["n_test_primary"]
    output["spatial_n_test"] = merged["n_test_spatial"]
    return output


def atomic_savefig(figure: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.stem + ".tmp" + path.suffix)
    figure.savefig(temporary, dpi=300, bbox_inches="tight")
    os.replace(temporary, path)
    plt.close(figure)


def plot_comparison(comparison: pd.DataFrame, path: Path) -> None:
    figure, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=True)
    x = np.arange(len(MODELS))
    width = 0.36
    for axis, population in zip(axes, ["Global", "Song", "Ming"], strict=True):
        block = comparison.loc[comparison["population"].eq(population)].set_index("model_id").reindex(MODELS)
        axis.bar(x - width / 2, block["primary_roc_auc"], width, label="Primary", color="#4c78a8")
        axis.bar(x + width / 2, block["spatial_roc_auc"], width, label="Spatial holdout", color="#f58518")
        axis.set_xticks(x, MODELS, rotation=35)
        axis.set_title(population)
        axis.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("ROC-AUC")
    axes[-1].legend(frameon=False)
    figure.suptitle("Primary versus unseen historical-prefecture holdout")
    figure.tight_layout()
    atomic_savefig(figure, path)


def main() -> int:
    logger = setup_logging("phase2_5_spatial_models", PROJECT_ROOT / "outputs/phase2_5/logs/spatial_robustness.log")
    dataset = load_phase25_dataset()
    metrics, tests, validations, metadata, fallback_rows = [], [], [], [], []
    for population in ["Global", "Song", "Ming"]:
        for model_id in MODELS:
            run = run_fixed_model(dataset, population, model_id, "CatBoost", split_protocol="spatial")
            metrics.append(run.metric)
            tests.append(run.test_predictions)
            validations.append(run.validation_predictions)
            metadata.append(run.feature_metadata)
            logger.info("Spatial %s/%s AUC=%.4f", population, model_id, run.metric["roc_auc"])
        prepared = prepare_phase25_data(dataset, population, "G5", split_protocol="spatial")
        train_regions = set(prepared.train["addr_id"].astype("string").fillna("__MISSING__"))
        for partition, part in [("validation", prepared.validation), ("test", prepared.test)]:
            region = part["addr_id"].astype("string").fillna("__MISSING__")
            fallback_rows.append({
                "population": population,
                "partition": partition,
                "n_people": len(part),
                "n_unseen_region": int((~region.isin(train_regions)).sum()),
                "unseen_region_rate": float((~region.isin(train_regions)).mean()),
                "fallback": "training global target prior",
            })
    spatial = pd.DataFrame(metrics)
    comparison = compare(primary_metrics(), spatial)
    atomic_to_csv(comparison, PROJECT_ROOT / "outputs/phase2_5/tables/spatial_robustness_results.csv")
    atomic_to_csv(spatial, PROJECT_ROOT / "outputs/phase2_5/tables/spatial_model_metrics.csv")
    atomic_to_csv(pd.DataFrame(fallback_rows), PROJECT_ROOT / "outputs/phase2_5/tables/spatial_prior_fallback_audit.csv")
    save_analysis_outputs("spatial_robustness_predictions", metrics, tests, validations, metadata)
    plot_comparison(comparison, PROJECT_ROOT / "outputs/phase2_5/figures/primary_vs_spatial_holdout.png")
    logger.info("Spatial robustness complete: %d models", len(spatial))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
