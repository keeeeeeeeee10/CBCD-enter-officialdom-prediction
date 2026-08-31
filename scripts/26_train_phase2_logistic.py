#!/usr/bin/env python3
"""Train fixed Phase 2 logistic baselines on the frozen primary split."""

from __future__ import annotations

import gc
import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import atomic_to_csv, atomic_to_parquet, load_yaml
from src.metrics import binary_metrics, optimal_balanced_accuracy_threshold
from src.modeling import build_logistic_pipeline, predictor_frame, prepare_model_data
from src.utils import setup_logging


POPULATIONS = ["Global", "Song", "Ming"]
FEATURE_SETS = ["M0", "M0b", "M1", "M2", "M3", "M4", "M5", "M6"]
INTERPRETABLE_TERMS = (
    "father_ever_entry",
    "paternal_grandfather_ever_entry",
    "maternal_grandfather_ever_entry",
    "distance_to_dynasty_capital_km",
    "gender",
    "province_id",
    "prefecture_id",
    "county_id",
)


def metric_row(
    prepared,
    probability: np.ndarray,
    population: str,
    feature_set: str,
    variant: str,
    threshold_source: str,
    threshold: float,
) -> dict[str, object]:
    y_test = prepared.test["target_entry_v1"].astype(int).to_numpy()
    return {
        "algorithm": "LogisticRegression",
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
        "best_iteration": np.nan,
        **binary_metrics(y_test, probability, threshold),
    }


def coefficient_rows(model, population: str, feature_set: str) -> list[dict[str, object]]:
    names = np.asarray(model.named_steps["preprocess"].get_feature_names_out(), dtype=object)
    values = np.asarray(model.named_steps["model"].coef_[0], dtype=float)
    if len(names) != len(values):
        raise RuntimeError("Coefficient/name length mismatch")
    order_positive = np.argsort(values)[::-1][:20]
    order_negative = np.argsort(values)[:20]
    interpretable = np.array([
        index for index, name in enumerate(names)
        if any(term in str(name) for term in INTERPRETABLE_TERMS)
    ], dtype=int)
    selected = np.unique(np.concatenate([order_positive, order_negative, interpretable]))
    rows = []
    for index in selected:
        rank = int(np.count_nonzero(np.abs(values) > abs(values[index])) + 1)
        rows.append({
            "algorithm": "LogisticRegression",
            "model_variant": "balanced",
            "population": population,
            "feature_set": feature_set,
            "transformed_feature": str(names[index]),
            "coefficient": float(values[index]),
            "absolute_coefficient_rank": rank,
            "selection_reason": (
                "interpretable_term" if any(term in str(names[index]) for term in INTERPRETABLE_TERMS)
                else "top_positive" if values[index] >= 0 else "top_negative"
            ),
        })
    return rows


def atomic_joblib_dump(value: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    joblib.dump(value, temporary, compress=3)
    os.replace(temporary, path)


def main() -> int:
    logger = setup_logging("phase2_logistic", PROJECT_ROOT / "outputs/logs/phase2_logistic.log")
    dataset = pd.read_parquet(PROJECT_ROOT / "data/modeling/person_phase2_features.parquet")
    model_config = load_yaml("configs/phase2_models.yaml")
    logistic_config = model_config["logistic"]
    seed = int(model_config["seed"])
    metric_rows: list[dict[str, object]] = []
    prediction_frames: list[pd.DataFrame] = []
    coefficients: list[dict[str, object]] = []

    for population in POPULATIONS:
        for feature_set in FEATURE_SETS:
            prepared = prepare_model_data(dataset, population, feature_set, seed=seed)
            train_x = predictor_frame(prepared.train, prepared)
            validation_x = predictor_frame(prepared.validation, prepared)
            test_x = predictor_frame(prepared.test, prepared)
            train_y = prepared.train["target_entry_v1"].astype(int).to_numpy()
            validation_y = prepared.validation["target_entry_v1"].astype(int).to_numpy()

            balanced = build_logistic_pipeline(
                prepared.categorical,
                prepared.numeric,
                logistic_config,
                class_weight=str(logistic_config["class_weight"]),
            )
            balanced.fit(train_x, train_y)
            validation_probability = balanced.predict_proba(validation_x)[:, 1]
            test_probability = balanced.predict_proba(test_x)[:, 1]
            optimal_threshold = optimal_balanced_accuracy_threshold(validation_y, validation_probability)
            metric_rows.append(metric_row(
                prepared, test_probability, population, feature_set,
                "balanced", "fixed_0.5", 0.5,
            ))
            metric_rows.append(metric_row(
                prepared, test_probability, population, feature_set,
                "balanced", "validation_balanced_accuracy", optimal_threshold,
            ))
            prediction_frames.append(pd.DataFrame({
                "algorithm": "LogisticRegression",
                "model_variant": "balanced",
                "population": population,
                "feature_set": feature_set,
                "split_protocol": "primary",
                "person_id": prepared.test["person_id"].to_numpy(),
                "y_true": prepared.test["target_entry_v1"].astype(np.int8).to_numpy(),
                "y_probability": test_probability,
            }))
            coefficients.extend(coefficient_rows(balanced, population, feature_set))
            atomic_joblib_dump(
                balanced,
                PROJECT_ROOT / f"outputs/phase2/models/logistic_{population.lower()}_{feature_set.lower()}_balanced.joblib",
            )

            diagnostic = build_logistic_pipeline(
                prepared.categorical,
                prepared.numeric,
                logistic_config,
                class_weight=None,
            )
            diagnostic.fit(train_x, train_y)
            diagnostic_probability = diagnostic.predict_proba(test_x)[:, 1]
            metric_rows.append(metric_row(
                prepared, diagnostic_probability, population, feature_set,
                "unweighted_diagnostic", "fixed_0.5", 0.5,
            ))
            logger.info(
                "%s/%s complete: balanced test AUC=%.4f, diagnostic AUC=%.4f, validation threshold=%.2f",
                population,
                feature_set,
                metric_rows[-3]["roc_auc"],
                metric_rows[-1]["roc_auc"],
                optimal_threshold,
            )
            del prepared, train_x, validation_x, test_x, balanced, diagnostic
            gc.collect()

    metrics = pd.DataFrame(metric_rows)
    atomic_to_csv(metrics, PROJECT_ROOT / "outputs/phase2/tables/model_metrics.csv")
    atomic_to_csv(pd.DataFrame(coefficients), PROJECT_ROOT / "outputs/phase2/tables/logistic_coefficients.csv")
    atomic_to_parquet(
        pd.concat(prediction_frames, ignore_index=True),
        PROJECT_ROOT / "data/modeling/phase2_predictions_logistic.parquet",
    )
    logger.info("Logistic Phase 2 complete: %d test metric rows", len(metrics))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
