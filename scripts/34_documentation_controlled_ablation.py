#!/usr/bin/env python3
"""Run documentation-controlled CatBoost and Logistic ablations."""

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


CAT_MODELS = ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D6i"]
LOGISTIC_MODELS = ["D0", "D1", "D2", "D3", "D5", "D6", "D6i"]


def atomic_savefig(figure: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.stem + ".tmp" + path.suffix)
    figure.savefig(temporary, dpi=300, bbox_inches="tight")
    os.replace(temporary, path)
    plt.close(figure)


def deltas(metrics: pd.DataFrame) -> pd.DataFrame:
    groups = ["algorithm", "population", "target_name", "split_protocol", "subset"]
    rows = [metric_deltas(metrics, ["D0", "D1", "D2", "D3", "D4", "D5", "D6"], groups)]
    rows.append(metric_deltas(metrics, ["D5", "D6i"], groups))
    # Logistic intentionally omits D4; record its permitted D3 -> D5 jump separately.
    rows.append(metric_deltas(metrics, ["D3", "D5"], groups))
    return pd.concat(rows, ignore_index=True).drop_duplicates(groups + ["model_a", "model_b"])


def plot_documentation(metrics: pd.DataFrame, path: Path) -> None:
    cat = metrics.loc[metrics["algorithm"].eq("CatBoost")]
    figure, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=True)
    for axis, population in zip(axes, ["Global", "Song", "Ming"], strict=True):
        values = cat.loc[cat["population"].eq(population)].set_index("model_id").reindex(CAT_MODELS)
        axis.plot(CAT_MODELS, values["roc_auc"], marker="o", color="#4c78a8", linewidth=2)
        axis.set_title(population)
        axis.set_xlabel("Documentation-controlled set")
        axis.tick_params(axis="x", rotation=35)
        axis.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("ROC-AUC")
    figure.suptitle("Documentation-controlled signal decomposition")
    figure.tight_layout()
    atomic_savefig(figure, path)


def main() -> int:
    logger = setup_logging("phase2_5_documentation", PROJECT_ROOT / "outputs/phase2_5/logs/documentation_ablation.log")
    dataset = load_phase25_dataset()
    metrics, tests, validations, metadata = [], [], [], []
    for algorithm, model_ids in [("CatBoost", CAT_MODELS), ("LogisticRegression", LOGISTIC_MODELS)]:
        for population in ["Global", "Song", "Ming"]:
            for model_id in model_ids:
                run = run_fixed_model(dataset, population, model_id, algorithm)
                metrics.append(run.metric)
                tests.append(run.test_predictions)
                validations.append(run.validation_predictions)
                metadata.append(run.feature_metadata)
                logger.info("Documentation %s/%s/%s AUC=%.4f", algorithm, population, model_id, run.metric["roc_auc"])
    frame = pd.DataFrame(metrics)
    atomic_to_csv(frame, PROJECT_ROOT / "outputs/phase2_5/tables/documentation_controlled_ablation.csv")
    atomic_to_csv(deltas(frame), PROJECT_ROOT / "outputs/phase2_5/tables/documentation_controlled_deltas.csv")
    save_analysis_outputs("documentation_controlled_predictions", metrics, tests, validations, metadata)
    plot_documentation(frame, PROJECT_ROOT / "outputs/phase2_5/figures/documentation_controlled_ablation.png")
    logger.info("Documentation-controlled ablation complete: %d models", len(frame))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
