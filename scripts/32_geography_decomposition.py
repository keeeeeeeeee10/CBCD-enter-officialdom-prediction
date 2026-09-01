#!/usr/bin/env python3
"""Decompose geography observability, raw space, density, and supervised prior."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import atomic_to_csv
from src.phase25 import load_phase25_dataset, metric_deltas, run_fixed_model, save_analysis_outputs
from src.utils import setup_logging


MODELS = ["G0", "G1", "G2", "G3", "G4", "G5"]


def atomic_savefig(figure: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.stem + ".tmp" + path.suffix)
    figure.savefig(temporary, dpi=300, bbox_inches="tight")
    os.replace(temporary, path)
    plt.close(figure)


def plot_metric(metrics: pd.DataFrame, metric: str, ylabel: str, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 4.5))
    for population, color in zip(["Global", "Song", "Ming"], ["#4c78a8", "#f58518", "#54a24b"], strict=True):
        values = metrics.loc[metrics["population"].eq(population)].set_index("model_id").reindex(MODELS)
        axis.plot(MODELS, values[metric], marker="o", linewidth=2, label=population, color=color)
    axis.set_xlabel("Geography feature set")
    axis.set_ylabel(ylabel)
    axis.set_title(f"Geography signal decomposition: {ylabel}")
    axis.grid(axis="y", alpha=0.25)
    axis.legend(frameon=False)
    figure.tight_layout()
    atomic_savefig(figure, path)


def main() -> int:
    logger = setup_logging("phase2_5_geography", PROJECT_ROOT / "outputs/phase2_5/logs/geography_decomposition.log")
    dataset = load_phase25_dataset()
    metrics, tests, validations, metadata = [], [], [], []
    for population in ["Global", "Song", "Ming"]:
        for model_id in MODELS:
            run = run_fixed_model(dataset, population, model_id, "CatBoost")
            metrics.append(run.metric)
            tests.append(run.test_predictions)
            validations.append(run.validation_predictions)
            metadata.append(run.feature_metadata)
            logger.info("Geography %s/%s AUC=%.4f PR=%.4f", population, model_id, run.metric["roc_auc"], run.metric["pr_auc"])
    full = pd.DataFrame(metrics)
    atomic_to_csv(full, PROJECT_ROOT / "outputs/phase2_5/tables/geography_decomposition_results.csv")
    deltas = metric_deltas(full, MODELS, ["algorithm", "population", "target_name", "split_protocol", "subset"])
    atomic_to_csv(deltas, PROJECT_ROOT / "outputs/phase2_5/tables/geography_decomposition_deltas.csv")
    save_analysis_outputs("geography_decomposition_predictions", metrics, tests, validations, metadata)

    covered_metrics, covered_tests, covered_validations, covered_metadata = [], [], [], []
    for population in ["Song", "Ming"]:
        for model_id in ["G2", "G3", "G4", "G5"]:
            run = run_fixed_model(dataset, population, model_id, "CatBoost", subset="geography_covered")
            covered_metrics.append(run.metric)
            covered_tests.append(run.test_predictions)
            covered_validations.append(run.validation_predictions)
            covered_metadata.append(run.feature_metadata)
    covered = pd.DataFrame(covered_metrics)
    atomic_to_csv(covered, PROJECT_ROOT / "outputs/phase2_5/tables/geography_covered_subset_results.csv")
    atomic_to_csv(
        metric_deltas(covered, ["G2", "G3", "G4", "G5"], ["algorithm", "population", "target_name", "split_protocol", "subset"]),
        PROJECT_ROOT / "outputs/phase2_5/tables/geography_covered_subset_deltas.csv",
    )
    save_analysis_outputs("geography_covered_subset_predictions", covered_metrics, covered_tests, covered_validations, covered_metadata)
    figures = PROJECT_ROOT / "outputs/phase2_5/figures"
    plot_metric(full, "roc_auc", "ROC-AUC", figures / "geography_decomposition_auc.png")
    plot_metric(full, "pr_auc", "PR-AUC", figures / "geography_decomposition_prauc.png")
    logger.info("Geography decomposition complete: %d full and %d covered-subset models", len(full), len(covered))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
