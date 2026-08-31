#!/usr/bin/env python3
"""Create compact Phase 2 figures from locked result tables."""

from __future__ import annotations

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
from src.utils import setup_logging


POPULATIONS = ["Global", "Song", "Ming"]
FEATURE_ORDER = ["M0", "M0b", "M1", "M2", "M3", "M4", "M5", "M6"]
ALGORITHMS = ["LogisticRegression", "CatBoost"]
COLORS = {"LogisticRegression": "#2f6690", "CatBoost": "#d97706"}
POP_COLORS = {"Global": "#2f6690", "Song": "#d97706", "Ming": "#4d7c0f", "Qing": "#9f1239"}


def output_path(name: str) -> Path:
    path = PROJECT_ROOT / "outputs/phase2/figures" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def fixed_primary_metrics() -> pd.DataFrame:
    metrics = pd.read_csv(PROJECT_ROOT / "outputs/phase2/tables/model_metrics.csv")
    return metrics.loc[
        metrics["evaluation_split"].eq("test") & metrics["threshold_source"].eq("fixed_0.5")
        & ((metrics["algorithm"] != "LogisticRegression") | metrics["model_variant"].eq("balanced"))
    ].copy()


def plot_primary_auc(metrics: pd.DataFrame) -> Path:
    figure, axes = plt.subplots(1, 3, figsize=(15, 4.8), sharey=True)
    x = np.arange(len(FEATURE_ORDER))
    for axis, population in zip(axes, POPULATIONS):
        subset = metrics.loc[metrics["population"].eq(population)]
        for algorithm in ALGORITHMS:
            values = subset.loc[subset["algorithm"].eq(algorithm)].set_index("feature_set")["roc_auc"]
            axis.plot(
                x,
                [values.get(feature, np.nan) for feature in FEATURE_ORDER],
                marker="o",
                linewidth=2,
                label="Logistic" if algorithm == "LogisticRegression" else "CatBoost",
                color=COLORS[algorithm],
            )
        axis.set_title(population)
        axis.set_xticks(x, FEATURE_ORDER)
        axis.set_ylim(0.45, 1.0)
        axis.set_xlabel("Feature set")
        axis.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("Test ROC-AUC")
    axes[-1].legend(frameon=False, loc="lower right")
    figure.suptitle("Primary-split model performance")
    figure.tight_layout()
    path = output_path("phase2_primary_auc.png")
    figure.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(figure)
    return path


def plot_ablation(ablation: pd.DataFrame) -> Path:
    labels = ["M2-M1", "M3-M2", "M4-M3", "M6-M4"]
    lookup = {
        ("M1", "M2"): "M2-M1",
        ("M2", "M3"): "M3-M2",
        ("M3", "M4"): "M4-M3",
        ("M4", "M6"): "M6-M4",
    }
    figure, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    for axis, algorithm in zip(axes, ALGORITHMS):
        subset = ablation.loc[
            ablation["algorithm"].eq(algorithm)
            & ablation["baseline_feature_set"].isin(["M1", "M2", "M3", "M4"])
            & ablation["extension_feature_set"].isin(["M2", "M3", "M4", "M6"])
        ].copy()
        subset["step"] = [lookup.get((a, b), "") for a, b in zip(subset["baseline_feature_set"], subset["extension_feature_set"])]
        subset = subset.loc[subset["step"].isin(labels)]
        width = 0.23
        x = np.arange(len(labels))
        for offset, population in enumerate(POPULATIONS):
            values = subset.loc[subset["population"].eq(population)].set_index("step")["delta_roc_auc"]
            axis.bar(
                x + (offset - 1) * width,
                [values.get(label, np.nan) for label in labels],
                width=width,
                label=population,
                color=POP_COLORS[population],
            )
        axis.axhline(0, color="#444444", linewidth=0.8)
        axis.set_title("Logistic" if algorithm == "LogisticRegression" else "CatBoost")
        axis.set_xticks(x, labels)
        axis.set_xlabel("Added feature block")
        axis.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("Delta test ROC-AUC")
    axes[-1].legend(frameon=False)
    figure.suptitle("Incremental predictive contribution")
    figure.tight_layout()
    path = output_path("phase2_ablation_delta.png")
    figure.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(figure)
    return path


def plot_robustness(metrics: pd.DataFrame, primary: pd.DataFrame) -> Path:
    family = metrics.loc[
        metrics["analysis"].eq("family_group_robustness")
        & metrics["threshold_source"].eq("fixed_0.5")
        & metrics["feature_set"].isin(["M4", "M6"])
    ].copy()
    temporal = metrics.loc[
        metrics["analysis"].eq("temporal_sensitivity")
        & metrics["threshold_source"].eq("fixed_0.5")
        & metrics["feature_set"].isin(["M4", "M6"])
    ].copy()
    figure, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    temporal_populations = [population for population in ["Global", "Song", "Ming", "Qing"] if population in set(temporal["population"])]
    for axis, subset, title, populations in [
        (axes[0], family, "Family-group split", ["Global", "Song", "Ming"]),
        (axes[1], temporal, "SAFE temporal split", temporal_populations),
    ]:
        x = np.arange(len(populations))
        width = 0.25
        for offset, feature_set in enumerate(["M4", "M6"]):
            values = subset.loc[subset["feature_set"].eq(feature_set)].set_index("population")["roc_auc"]
            axis.bar(
                x + (offset - 0.5) * width,
                [values.get(population, np.nan) for population in populations],
                width=width,
                label=feature_set,
                color="#2f6690" if feature_set == "M4" else "#d97706",
            )
        axis.set_title(title)
        axis.set_xticks(x, populations)
        axis.set_xlabel("Population")
        axis.set_ylim(0.45, 1.0)
        axis.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("Test ROC-AUC")
    axes[-1].legend(frameon=False)
    figure.suptitle("Robustness checks: LogisticRegression")
    figure.tight_layout()
    path = output_path("phase2_robustness_auc.png")
    figure.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(figure)
    return path


def plot_feature_importance(importance: pd.DataFrame) -> Path:
    subset = importance.loc[
        importance["algorithm"].eq("CatBoost")
        & importance["population"].eq("Global")
        & importance["feature_set"].eq("M6")
    ].sort_values("importance", ascending=False).head(15).sort_values("importance")
    figure, axis = plt.subplots(figsize=(9, 6))
    axis.barh(subset["feature"].astype(str), subset["importance"], color="#d97706")
    axis.set_xlabel("CatBoost feature importance")
    axis.set_ylabel("Feature")
    axis.set_title("Global/M6 top CatBoost features")
    axis.grid(axis="x", alpha=0.25)
    figure.tight_layout()
    path = output_path("phase2_feature_importance.png")
    figure.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(figure)
    return path


def plot_population_context() -> Path:
    population = pd.read_csv(PROJECT_ROOT / "outputs/tables/modeling_population_summary.csv")
    population = population.loc[population["population"].isin(["Global", "Song", "Ming", "Qing"])].copy()
    figure, axis = plt.subplots(figsize=(10, 5))
    x = np.arange(len(population))
    width = 0.2
    for offset, column, label in [
        (0, "entry_v1_rate", "ENTRY-record presence"),
        (1, "kin_coverage", "Kin coverage"),
        (2, "address_coverage", "Address coverage"),
        (3, "safe_time_anchor_coverage", "SAFE birth-year coverage"),
    ]:
        axis.bar(
            x + (offset - 1.5) * width,
            population[column],
            width=width,
            label=label,
            color=["#2f6690", "#4d7c0f", "#d97706", "#9f1239"][offset],
        )
    axis.set_xticks(x, population["population"])
    axis.set_ylim(0, 0.85)
    axis.set_ylabel("Rate / coverage")
    axis.set_title("Population composition and recording coverage")
    axis.legend(frameon=False, ncol=2)
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    path = output_path("phase2_population_context.png")
    figure.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(figure)
    return path


def plot_bootstrap(bootstrap: pd.DataFrame) -> Path:
    subset = bootstrap.loc[
        bootstrap["algorithm"].eq("CatBoost") & bootstrap["feature_set"].eq("M6")
    ].copy()
    figure, axis = plt.subplots(figsize=(9, 5))
    x = np.arange(len(subset))
    axis.errorbar(
        x,
        subset["roc_auc"],
        yerr=[subset["roc_auc"] - subset["roc_auc_ci_low"], subset["roc_auc_ci_high"] - subset["roc_auc"]],
        fmt="o",
        capsize=4,
        color="#2f6690",
    )
    axis.set_xticks(x, subset["population"])
    axis.set_ylim(0.85, 1.0)
    axis.set_ylabel("Test ROC-AUC with 95% bootstrap CI")
    axis.set_title("CatBoost/M6 uncertainty")
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    path = output_path("phase2_bootstrap_ci.png")
    figure.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(figure)
    return path


def main() -> int:
    logger = setup_logging("phase2_figures", PROJECT_ROOT / "outputs/logs/phase2_figures.log")
    primary = fixed_primary_metrics()
    ablation = pd.read_csv(PROJECT_ROOT / "outputs/phase2/tables/ablation_results.csv")
    robustness = pd.read_csv(PROJECT_ROOT / "outputs/phase2/tables/robustness_metrics.csv")
    importance = pd.read_csv(PROJECT_ROOT / "outputs/phase2/tables/catboost_feature_importance.csv")
    bootstrap = pd.read_csv(PROJECT_ROOT / "outputs/phase2/tables/bootstrap_intervals.csv")
    paths = [
        plot_primary_auc(primary),
        plot_ablation(ablation),
        plot_robustness(robustness, primary),
        plot_feature_importance(importance),
        plot_population_context(),
        plot_bootstrap(bootstrap),
    ]
    manifest = pd.DataFrame({
        "figure": [path.stem for path in paths],
        "path": [str(path.relative_to(PROJECT_ROOT)) for path in paths],
        "format": [path.suffix.lstrip(".") for path in paths],
    })
    atomic_to_csv(manifest, PROJECT_ROOT / "outputs/phase2/tables/figure_manifest.csv")
    logger.info("Figures complete: %d PNG files", len(paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
