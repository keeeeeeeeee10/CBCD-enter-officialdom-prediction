#!/usr/bin/env python3
"""Separate family observability, topology, full-record, and inductive capital."""

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

from src.family import INDUCTIVE_FEATURES
from src.feature_builders import atomic_to_csv
from src.phase25 import load_phase25_dataset, metric_deltas, prepare_phase25_data, run_fixed_model, save_analysis_outputs
from src.utils import setup_logging


MODELS = ["F0", "F1", "F2", "F3", "F4"]


def atomic_savefig(figure: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.stem + ".tmp" + path.suffix)
    figure.savefig(temporary, dpi=300, bbox_inches="tight")
    os.replace(temporary, path)
    plt.close(figure)


def plot_family(metrics: pd.DataFrame, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8, 4.5))
    for population, color in zip(["Global", "Song", "Ming"], ["#4c78a8", "#f58518", "#54a24b"], strict=True):
        values = metrics.loc[metrics["population"].eq(population)].set_index("model_id").reindex(MODELS)
        axis.plot(MODELS, values["roc_auc"], marker="o", linewidth=2, label=population, color=color)
    axis.set_xlabel("Family feature set")
    axis.set_ylabel("ROC-AUC")
    axis.set_title("Family observability, topology, and political capital")
    axis.grid(axis="y", alpha=0.25)
    axis.legend(frameon=False)
    figure.tight_layout()
    atomic_savefig(figure, path)


def plot_family_holdout(primary: pd.DataFrame, family: pd.DataFrame, path: Path) -> None:
    models = ["F1", "F2", "F3", "F4"]
    figure, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
    for axis, population in zip(axes, ["Global", "Ming"], strict=True):
        p = primary.loc[primary["population"].eq(population)].set_index("model_id").reindex(models)
        f = family.loc[family["population"].eq(population)].set_index("model_id").reindex(models)
        axis.plot(models, p["roc_auc"], marker="o", label="Primary", color="#4c78a8")
        axis.plot(models, f["roc_auc"], marker="o", label="Family holdout", color="#f58518")
        axis.set_title(population)
        axis.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("ROC-AUC")
    axes[-1].legend(frameon=False)
    figure.suptitle("Primary versus family-group holdout")
    figure.tight_layout()
    atomic_savefig(figure, path)


def inductive_coverage(dataset: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split_protocol in ["primary", "family"]:
        for population in ["Global", "Song", "Ming"]:
            prepared = prepare_phase25_data(dataset, population, "F4", split_protocol=split_protocol)
            for partition, frame in [("train", prepared.train), ("validation", prepared.validation), ("test", prepared.test)]:
                for feature in INDUCTIVE_FEATURES:
                    rows.append({
                        "split_protocol": split_protocol,
                        "population": population,
                        "partition": partition,
                        "feature": feature,
                        "n_people": len(frame),
                        "n_non_missing": int(frame[feature].notna().sum()),
                        "coverage": float(frame[feature].notna().mean()),
                    })
    return pd.DataFrame(rows)


def main() -> int:
    logger = setup_logging("phase2_5_family", PROJECT_ROOT / "outputs/phase2_5/logs/family_decomposition.log")
    dataset = load_phase25_dataset()
    metrics, tests, validations, metadata = [], [], [], []
    for population in ["Global", "Song", "Ming"]:
        for model_id in MODELS:
            run = run_fixed_model(dataset, population, model_id, "CatBoost")
            metrics.append(run.metric)
            tests.append(run.test_predictions)
            validations.append(run.validation_predictions)
            metadata.append(run.feature_metadata)
            logger.info("Family %s/%s AUC=%.4f", population, model_id, run.metric["roc_auc"])
    full = pd.DataFrame(metrics)
    atomic_to_csv(full, PROJECT_ROOT / "outputs/phase2_5/tables/family_decomposition_results.csv")
    # F4 is an alternative to F3, so retain both F3-F2 and F4-F2 explicitly.
    sequential = metric_deltas(full, ["F0", "F1", "F2", "F3"], ["algorithm", "population", "target_name", "split_protocol", "subset"])
    alternative = metric_deltas(full, ["F2", "F4"], ["algorithm", "population", "target_name", "split_protocol", "subset"])
    atomic_to_csv(pd.concat([sequential, alternative], ignore_index=True), PROJECT_ROOT / "outputs/phase2_5/tables/family_decomposition_deltas.csv")
    save_analysis_outputs("family_decomposition_predictions", metrics, tests, validations, metadata)

    subset_metrics, subset_tests, subset_validations, subset_metadata = [], [], [], []
    for subset in ["family_observed", "eligible_older_kin"]:
        for population in ["Song", "Ming"]:
            for model_id in ["F1", "F2", "F3", "F4"]:
                run = run_fixed_model(dataset, population, model_id, "CatBoost", subset=subset)
                subset_metrics.append(run.metric)
                subset_tests.append(run.test_predictions)
                subset_validations.append(run.validation_predictions)
                subset_metadata.append(run.feature_metadata)
    subset_frame = pd.DataFrame(subset_metrics)
    atomic_to_csv(subset_frame, PROJECT_ROOT / "outputs/phase2_5/tables/family_observed_subset_results.csv")
    subset_deltas = pd.concat([
        metric_deltas(subset_frame, ["F1", "F2", "F3"], ["algorithm", "population", "target_name", "split_protocol", "subset"]),
        metric_deltas(subset_frame, ["F2", "F4"], ["algorithm", "population", "target_name", "split_protocol", "subset"]),
    ], ignore_index=True)
    atomic_to_csv(subset_deltas, PROJECT_ROOT / "outputs/phase2_5/tables/family_observed_subset_deltas.csv")
    save_analysis_outputs("family_observed_subset_predictions", subset_metrics, subset_tests, subset_validations, subset_metadata)
    atomic_to_csv(inductive_coverage(dataset), PROJECT_ROOT / "outputs/phase2_5/tables/family_inductive_coverage.csv")
    plot_family(full, PROJECT_ROOT / "outputs/phase2_5/figures/family_observability_topology_capital.png")

    family_metrics, family_tests, family_validations, family_metadata = [], [], [], []
    for population in ["Global", "Ming"]:
        for model_id in ["F1", "F2", "F3", "F4"]:
            run = run_fixed_model(dataset, population, model_id, "CatBoost", split_protocol="family")
            family_metrics.append(run.metric)
            family_tests.append(run.test_predictions)
            family_validations.append(run.validation_predictions)
            family_metadata.append(run.feature_metadata)
    family_frame = pd.DataFrame(family_metrics)
    atomic_to_csv(family_frame, PROJECT_ROOT / "outputs/phase2_5/tables/family_holdout_decomposition_results.csv")
    save_analysis_outputs("family_holdout_predictions", family_metrics, family_tests, family_validations, family_metadata)
    plot_family_holdout(full, family_frame, PROJECT_ROOT / "outputs/phase2_5/figures/primary_vs_family_holdout.png")
    logger.info("Family decomposition complete: %d full and %d subset models", len(full), len(subset_frame))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
