#!/usr/bin/env python3
"""Separate observability, administrative space, physical space, and address semantics."""

from __future__ import annotations

import gc
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import atomic_to_csv
from src.phase26 import fit_phase26_model, load_phase26_dataset
from src.utils import setup_logging


def sequential_deltas(metrics: pd.DataFrame, order: list[str]) -> pd.DataFrame:
    rows = []
    for population, group in metrics.groupby("population"):
        indexed = group.set_index("model_id")
        for left, right in zip(order[:-1], order[1:], strict=True):
            if left in indexed.index and right in indexed.index:
                rows.append({
                    "population": population,
                    "comparison": f"{right} - {left}",
                    "delta_roc_auc": indexed.loc[right, "roc_auc"] - indexed.loc[left, "roc_auc"],
                    "delta_pr_auc": indexed.loc[right, "pr_auc"] - indexed.loc[left, "pr_auc"],
                    "delta_log_loss": indexed.loc[right, "log_loss"] - indexed.loc[left, "log_loss"],
                })
    return pd.DataFrame(rows)


def main() -> int:
    logger = setup_logging("phase2_6_address", PROJECT_ROOT / "outputs/phase2_6/logs/address_semantics.log")
    dataset = load_phase26_dataset()
    metrics, subset_metrics = [], []
    models = ["A0", "A1", "A2", "A3", "A4", "A5", "A6_LOCAL_PRIOR_SENSITIVITY"]
    for population in ["Global", "Song", "Ming"]:
        for model_id in models:
            run = fit_phase26_model(dataset, population, model_id, seed=42)
            metrics.append(run.metric)
            logger.info("Address %s/%s AUC=%.6f", population, model_id, run.metric["roc_auc"])
            del run
            gc.collect()
        for model_id in ["A2", "A3", "A4"]:
            run = fit_phase26_model(dataset, population, model_id, seed=42, subset="address_observed")
            subset_metrics.append(run.metric)
            logger.info("Address-observed %s/%s AUC=%.6f", population, model_id, run.metric["roc_auc"])
            del run
            gc.collect()
    frame = pd.DataFrame(metrics)
    subset = pd.DataFrame(subset_metrics)
    tables = PROJECT_ROOT / "outputs/phase2_6/tables"
    atomic_to_csv(frame, tables / "address_semantics_decomposition.csv")
    atomic_to_csv(subset, tables / "address_observed_subset_results.csv")
    atomic_to_csv(
        sequential_deltas(frame, models),
        tables / "address_semantics_deltas.csv",
    )
    atomic_to_csv(
        sequential_deltas(subset, ["A2", "A3", "A4"]),
        tables / "address_observed_subset_deltas.csv",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
