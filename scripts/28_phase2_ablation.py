#!/usr/bin/env python3
"""Compute Phase 2 ablation deltas, bootstrap CIs, and Figures 1--3."""

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

from src.feature_builders import atomic_to_csv, load_yaml
from src.metrics import bootstrap_auc_intervals
from src.utils import setup_logging


POPULATIONS = ["Global", "Song", "Ming"]
SEQUENCE = ["M0", "M1", "M2", "M3", "M4"]
COMPARISONS = [("M0", "M1"), ("M1", "M2"), ("M2", "M3"), ("M3", "M4"), ("M4", "M6")]
COLORS = {"LogisticRegression": "#3264a8", "CatBoost": "#d56a32"}


def main_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    mask = frame["threshold_source"].eq("fixed_0.5")
    mask &= ~(
        frame["algorithm"].eq("LogisticRegression")
        & ~frame["model_variant"].eq("balanced")
    )
    selected = frame.loc[mask].copy()
    keys = ["algorithm", "population", "feature_set", "split_protocol"]
    if selected.duplicated(keys).any():
        raise RuntimeError("Main model metric selection is not unique")
    return selected


def atomic_savefig(figure: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.stem + ".tmp" + path.suffix)
    figure.savefig(temporary, dpi=300, bbox_inches="tight")
    os.replace(temporary, path)
    plt.close(figure)


def ablation_figure(metrics: pd.DataFrame, metric: str, ylabel: str, path: Path) -> None:
    figure, axes = plt.subplots(1, 3, figsize=(12, 3.8), sharey=True)
    for axis, population in zip(axes, POPULATIONS, strict=True):
        for algorithm in ["LogisticRegression", "CatBoost"]:
            values = (
                metrics.loc[
                    metrics["population"].eq(population)
                    & metrics["algorithm"].eq(algorithm)
                    & metrics["feature_set"].isin(SEQUENCE)
                ]
                .set_index("feature_set")
                .reindex(SEQUENCE)
            )
            axis.plot(SEQUENCE, values[metric], marker="o", linewidth=2, label=algorithm, color=COLORS[algorithm])
        axis.set_title(population)
        axis.set_xlabel("Feature set")
        axis.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel(ylabel)
    axes[-1].legend(frameon=False, fontsize=8)
    figure.suptitle(f"Phase 2 ablation: {ylabel} (frozen primary test)")
    figure.tight_layout()
    atomic_savefig(figure, path)


def documentation_figure(metrics: pd.DataFrame, path: Path) -> None:
    figure, axes = plt.subplots(1, 3, figsize=(12, 3.8), sharey=True)
    groups = ["M4", "M5", "M6"]
    labels = ["M4\nHistorical", "M5\nDocumentation", "M6\nCombined"]
    width = 0.36
    x = np.arange(len(groups))
    for axis, population in zip(axes, POPULATIONS, strict=True):
        for offset, algorithm in zip([-width / 2, width / 2], ["LogisticRegression", "CatBoost"], strict=True):
            values = (
                metrics.loc[
                    metrics["population"].eq(population)
                    & metrics["algorithm"].eq(algorithm)
                    & metrics["feature_set"].isin(groups)
                ]
                .set_index("feature_set")
                .reindex(groups)["roc_auc"]
            )
            axis.bar(x + offset, values, width, label=algorithm, color=COLORS[algorithm])
        axis.set_xticks(x, labels)
        axis.set_title(population)
        axis.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("ROC-AUC")
    axes[-1].legend(frameon=False, fontsize=8)
    figure.suptitle("Documentation-only versus historical features (frozen primary test)")
    figure.tight_layout()
    atomic_savefig(figure, path)


def bootstrap_core_predictions(config: dict) -> pd.DataFrame:
    predictions = pd.concat([
        pd.read_parquet(PROJECT_ROOT / "data/modeling/phase2_predictions_logistic.parquet"),
        pd.read_parquet(PROJECT_ROOT / "data/modeling/phase2_predictions_catboost.parquet"),
    ], ignore_index=True)
    # The prespecified first-round CI scope is the database-wide Global benchmark.
    selected = predictions.loc[
        predictions["population"].eq("Global")
        & predictions["feature_set"].isin(["M0", "M4", "M5", "M6"])
    ]
    rows = []
    for group_key, group in selected.groupby(["algorithm", "model_variant", "population", "feature_set"], sort=True):
        interval = bootstrap_auc_intervals(
            group["y_true"].to_numpy(),
            group["y_probability"].to_numpy(),
            n_resamples=int(config["bootstrap_resamples"]),
            seed=int(config["seed"]),
            confidence=float(config["bootstrap_confidence"]),
        )
        rows.append(dict(zip(["algorithm", "model_variant", "population", "feature_set"], group_key, strict=True)) | interval)
    return pd.DataFrame(rows)


def main() -> int:
    logger = setup_logging("phase2_ablation", PROJECT_ROOT / "outputs/logs/phase2_ablation.log")
    metrics = main_metrics(pd.read_csv(PROJECT_ROOT / "outputs/phase2/tables/model_metrics.csv"))
    metrics = metrics.loc[metrics["split_protocol"].eq("primary")]
    rows = []
    for algorithm in ["LogisticRegression", "CatBoost"]:
        for population in POPULATIONS:
            index = metrics.loc[
                metrics["algorithm"].eq(algorithm) & metrics["population"].eq(population)
            ].set_index("feature_set")
            for baseline, augmented in COMPARISONS:
                rows.append({
                    "algorithm": algorithm,
                    "population": population,
                    "split_protocol": "primary",
                    "baseline_feature_set": baseline,
                    "augmented_feature_set": augmented,
                    "comparison": f"{augmented} - {baseline}",
                    "delta_roc_auc": float(index.loc[augmented, "roc_auc"] - index.loc[baseline, "roc_auc"]),
                    "delta_pr_auc": float(index.loc[augmented, "pr_auc"] - index.loc[baseline, "pr_auc"]),
                    "delta_log_loss": float(index.loc[augmented, "log_loss"] - index.loc[baseline, "log_loss"]),
                })
    ablation = pd.DataFrame(rows)
    atomic_to_csv(ablation, PROJECT_ROOT / "outputs/phase2/tables/ablation_results.csv")

    config = load_yaml("configs/phase2_models.yaml")
    intervals = bootstrap_core_predictions(config)
    atomic_to_csv(intervals, PROJECT_ROOT / "outputs/phase2/tables/metric_bootstrap_ci.csv")
    figures = PROJECT_ROOT / "outputs/phase2/figures"
    ablation_figure(metrics, "roc_auc", "ROC-AUC", figures / "figure1_ablation_roc_auc.png")
    ablation_figure(metrics, "pr_auc", "PR-AUC", figures / "figure2_ablation_pr_auc.png")
    documentation_figure(metrics, figures / "figure3_documentation_comparison.png")
    logger.info("Ablation complete: %d deltas; %d Global bootstrap intervals", len(ablation), len(intervals))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
