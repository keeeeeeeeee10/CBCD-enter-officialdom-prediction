#!/usr/bin/env python3
"""Evaluate fixed Phase 2.5/2.6 model definitions across five predetermined seeds."""

from __future__ import annotations

import gc
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import atomic_to_csv, load_yaml
from src.phase26 import fit_phase26_model, load_phase26_dataset
from src.utils import setup_logging


MODELS = ["F2", "F3", "F4", "D5", "D6", "D6i", "H_STRUCT"]
COMPARISONS = [("F2", "F3"), ("F2", "F4"), ("D5", "D6"), ("D5", "D6i")]


def frozen_seed42_rows() -> pd.DataFrame:
    family = pd.read_csv(PROJECT_ROOT / "outputs/phase2_5/tables/family_decomposition_results.csv")
    docs = pd.read_csv(PROJECT_ROOT / "outputs/phase2_5/tables/documentation_controlled_ablation.csv")
    frame = pd.concat([
        family.loc[family["algorithm"].eq("CatBoost") & family["model_id"].isin(["F2", "F3", "F4"])],
        docs.loc[docs["algorithm"].eq("CatBoost") & docs["model_id"].isin(["D5", "D6", "D6i"])],
    ], ignore_index=True)
    frame["seed"] = 42
    frame["target"] = frame["target_name"]
    frame["source"] = "frozen_phase2_5_seed42"
    return frame


def delta_summary(metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for population in ["Global", "Song", "Ming"]:
        block = metrics.loc[metrics["population"].eq(population)]
        for left, right in COMPARISONS:
            paired = block.loc[block["model_id"].isin([left, right])]
            for metric in ["roc_auc", "pr_auc", "log_loss", "brier_score"]:
                wide = paired.pivot(index="seed", columns="model_id", values=metric).dropna()
                values = wide[right] - wide[left]
                rows.append({
                    "population": population,
                    "comparison": f"{right} - {left}",
                    "metric": metric,
                    "mean_delta": float(values.mean()),
                    "std_delta": float(values.std(ddof=1)),
                    "min_delta": float(values.min()),
                    "max_delta": float(values.max()),
                    "median_delta": float(values.median()),
                    "n_positive_seeds": int((values > 0).sum()),
                    "n_seeds": int(len(values)),
                    "practical_magnitude": "small" if metric == "roc_auc" and abs(values.mean()) < 0.002 else "not_flagged",
                })
    return pd.DataFrame(rows)


def main() -> int:
    logger = setup_logging("phase2_6_multiseed", PROJECT_ROOT / "outputs/phase2_6/logs/multiseed.log")
    config = load_yaml("configs/phase2_6_models.yaml")
    seeds = [int(value) for value in config["stability_seeds"]]
    if seeds != [42, 202, 2024, 2025, 2026]:
        raise RuntimeError(f"Unexpected fixed stability seeds: {seeds}")
    dataset = load_phase26_dataset()
    rows = frozen_seed42_rows().to_dict("records")
    for seed in seeds:
        for population in ["Global", "Song", "Ming"]:
            current_models = ["H_STRUCT"] if seed == 42 else MODELS
            for model_id in current_models:
                run = fit_phase26_model(dataset, population, model_id, seed=seed)
                row = dict(run.metric)
                row["source"] = "phase2_6_fixed_retrain"
                rows.append(row)
                logger.info("Seed=%d %s/%s AUC=%.6f", seed, population, model_id, row["roc_auc"])
                del run
                gc.collect()
    metrics = pd.DataFrame(rows)
    required = pd.MultiIndex.from_product(
        [["Global", "Song", "Ming"], MODELS, seeds], names=["population", "model_id", "seed"]
    )
    observed = pd.MultiIndex.from_frame(metrics[["population", "model_id", "seed"]])
    missing = required.difference(observed)
    if len(missing):
        raise RuntimeError(f"Incomplete five-seed matrix: {list(missing)[:10]}")
    tables = PROJECT_ROOT / "outputs/phase2_6/tables"
    atomic_to_csv(metrics, tables / "multiseed_model_metrics.csv")
    atomic_to_csv(delta_summary(metrics), tables / "multiseed_delta_summary.csv")
    logger.info("Five-seed stability complete: %d model runs", len(metrics))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
