#!/usr/bin/env python3
"""Separate SAFE-birth availability, value, and explicit-indicator signals."""

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


def delta_rows(metrics: pd.DataFrame, comparisons: list[tuple[str, str]]) -> pd.DataFrame:
    rows = []
    for population, group in metrics.groupby("population"):
        indexed = group.set_index("model_id")
        for left, right in comparisons:
            if left not in indexed.index or right not in indexed.index:
                continue
            rows.append({
                "population": population,
                "comparison": f"{right} - {left}",
                "delta_roc_auc": indexed.loc[right, "roc_auc"] - indexed.loc[left, "roc_auc"],
                "delta_pr_auc": indexed.loc[right, "pr_auc"] - indexed.loc[left, "pr_auc"],
                "delta_log_loss": indexed.loc[right, "log_loss"] - indexed.loc[left, "log_loss"],
            })
    return pd.DataFrame(rows)


def main() -> int:
    logger = setup_logging("phase2_6_birth", PROJECT_ROOT / "outputs/phase2_6/logs/birth_missingness.log")
    dataset = load_phase26_dataset()
    all_rows, observed_rows = [], []
    for population in ["Global", "Song", "Ming"]:
        for model_id in ["B0", "B1", "B2", "B3"]:
            run = fit_phase26_model(dataset, population, model_id, seed=42)
            all_rows.append(run.metric)
            logger.info("Birth %s/%s AUC=%.6f", population, model_id, run.metric["roc_auc"])
            del run
            gc.collect()
        for model_id in ["B_OBSERVED_0", "B_OBSERVED_1"]:
            run = fit_phase26_model(dataset, population, model_id, seed=42, subset="birth_observed")
            observed_rows.append(run.metric)
            logger.info("Birth observed %s/%s AUC=%.6f", population, model_id, run.metric["roc_auc"])
            del run
            gc.collect()
    all_metrics = pd.DataFrame(all_rows)
    observed = pd.DataFrame(observed_rows)
    tables = PROJECT_ROOT / "outputs/phase2_6/tables"
    atomic_to_csv(all_metrics, tables / "birth_missingness_results.csv")
    atomic_to_csv(observed, tables / "birth_observed_subset_results.csv")
    deltas = pd.concat([
        delta_rows(all_metrics, [("B0", "B1"), ("B0", "B2"), ("B2", "B3")]),
        delta_rows(observed, [("B_OBSERVED_0", "B_OBSERVED_1")]),
    ], ignore_index=True)
    atomic_to_csv(deltas, tables / "birth_missingness_deltas.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
