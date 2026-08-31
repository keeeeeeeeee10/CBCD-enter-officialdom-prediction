#!/usr/bin/env python3
"""Train fixed CatBoost baselines and select class weighting on validation only."""

from __future__ import annotations

import gc
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import atomic_to_csv, atomic_to_parquet, load_yaml
from src.metrics import binary_metrics, optimal_balanced_accuracy_threshold
from src.modeling import fit_catboost_candidates, prepare_model_data
from src.utils import atomic_write_text, setup_logging


POPULATIONS = ["Global", "Song", "Ming"]
FEATURE_SETS = ["M0", "M0b", "M1", "M2", "M3", "M4", "M5", "M6"]


def metric_row(
    prepared,
    probability: np.ndarray,
    population: str,
    feature_set: str,
    variant: str,
    threshold_source: str,
    threshold: float,
    best_iteration: int | None,
    validation_metrics: dict[str, float],
) -> dict[str, object]:
    y_test = prepared.test["target_entry_v1"].astype(int).to_numpy()
    return {
        "algorithm": "CatBoost",
        "model_variant": variant,
        "population": population,
        "feature_set": feature_set,
        "split_protocol": "primary",
        "evaluation_split": "test",
        "threshold_source": threshold_source,
        "threshold": threshold,
        "n_train": len(prepared.train),
        "n_validation": len(prepared.validation),
        "n_test": len(prepared.test),
        "train_positive_rate": float(prepared.train["target_entry_v1"].mean()),
        "validation_positive_rate": float(prepared.validation["target_entry_v1"].mean()),
        "test_positive_rate": float(prepared.test["target_entry_v1"].mean()),
        "best_iteration": best_iteration,
        "selection_validation_roc_auc": validation_metrics["roc_auc"],
        "selection_validation_log_loss": validation_metrics["log_loss"],
        **binary_metrics(y_test, probability, threshold),
    }


def save_model(model, population: str, feature_set: str, constant_probability: float | None) -> None:
    output = PROJECT_ROOT / f"outputs/phase2/models/catboost_{population.lower()}_{feature_set.lower()}.cbm"
    output.parent.mkdir(parents=True, exist_ok=True)
    if model is None:
        atomic_write_text(
            output.with_suffix(".constant.json"),
            json.dumps({"constant_probability": constant_probability}, indent=2) + "\n",
        )
        return
    temporary = output.with_suffix(output.suffix + ".tmp")
    model.save_model(str(temporary), format="cbm")
    os.replace(temporary, output)


def main() -> int:
    logger = setup_logging("phase2_catboost", PROJECT_ROOT / "outputs/logs/phase2_catboost.log")
    dataset = pd.read_parquet(PROJECT_ROOT / "data/modeling/person_phase2_features.parquet")
    model_config = load_yaml("configs/phase2_models.yaml")
    catboost_config = model_config["catboost"]
    seed = int(model_config["seed"])
    existing_metrics_path = PROJECT_ROOT / "outputs/phase2/tables/model_metrics.csv"
    if not existing_metrics_path.exists():
        raise RuntimeError("Run scripts/26_train_phase2_logistic.py before CatBoost")
    metric_rows: list[dict[str, object]] = []
    prediction_frames: list[pd.DataFrame] = []
    importance_rows: list[dict[str, object]] = []

    for population in POPULATIONS:
        for feature_set in FEATURE_SETS:
            prepared = prepare_model_data(dataset, population, feature_set, seed=seed)
            model, selected_mode, validation_metrics, validation_probability, test_probability, best_iteration = (
                fit_catboost_candidates(prepared, catboost_config, seed)
            )
            validation_y = prepared.validation["target_entry_v1"].astype(int).to_numpy()
            threshold = optimal_balanced_accuracy_threshold(validation_y, validation_probability)
            metric_rows.append(metric_row(
                prepared, test_probability, population, feature_set, selected_mode,
                "fixed_0.5", 0.5, best_iteration, validation_metrics,
            ))
            metric_rows.append(metric_row(
                prepared, test_probability, population, feature_set, selected_mode,
                "validation_balanced_accuracy", threshold, best_iteration, validation_metrics,
            ))
            prediction_frames.append(pd.DataFrame({
                "algorithm": "CatBoost",
                "model_variant": selected_mode,
                "population": population,
                "feature_set": feature_set,
                "split_protocol": "primary",
                "person_id": prepared.test["person_id"].to_numpy(),
                "y_true": prepared.test["target_entry_v1"].astype(np.int8).to_numpy(),
                "y_probability": test_probability,
            }))
            if model is None:
                importances = np.zeros(len(prepared.feature_names), dtype=float)
                constant_probability = float(prepared.train["target_entry_v1"].mean())
            else:
                importances = model.get_feature_importance()
                constant_probability = None
            for rank, index in enumerate(np.argsort(importances)[::-1], start=1):
                importance_rows.append({
                    "algorithm": "CatBoost",
                    "model_variant": selected_mode,
                    "population": population,
                    "feature_set": feature_set,
                    "feature": prepared.feature_names[index],
                    "importance": float(importances[index]),
                    "importance_rank": rank,
                })
            save_model(model, population, feature_set, constant_probability)
            logger.info(
                "%s/%s complete: selected=%s, best_iteration=%s, validation AUC=%.4f, test AUC=%.4f",
                population,
                feature_set,
                selected_mode,
                best_iteration,
                validation_metrics["roc_auc"],
                metric_rows[-2]["roc_auc"],
            )
            del prepared, model, validation_probability, test_probability
            gc.collect()

    logistic_metrics = pd.read_csv(existing_metrics_path)
    combined_metrics = pd.concat([logistic_metrics, pd.DataFrame(metric_rows)], ignore_index=True, sort=False)
    atomic_to_csv(combined_metrics, existing_metrics_path)
    atomic_to_csv(
        pd.DataFrame(importance_rows),
        PROJECT_ROOT / "outputs/phase2/tables/catboost_feature_importance.csv",
    )
    atomic_to_parquet(
        pd.concat(prediction_frames, ignore_index=True),
        PROJECT_ROOT / "data/modeling/phase2_predictions_catboost.parquet",
    )
    logger.info("CatBoost Phase 2 complete: %d selected test metric rows", len(metric_rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
