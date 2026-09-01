#!/usr/bin/env python3
"""Train, export, and lock canonical seed-42 final models on the frozen primary split."""

from __future__ import annotations

import gc
import importlib.metadata
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import atomic_to_csv, atomic_to_parquet, load_yaml
from src.phase26 import (
    fit_phase26_model, json_dump, load_phase26_dataset, locked_manifest_payload,
    model_features, save_catboost_atomic, validate_locked_feature_sets,
)
from src.utils import atomic_write_text, setup_logging, sha256_file


MODELS = ["H_STRUCT", "D5_MAIN", "D6_UPPER"]


def main() -> int:
    logger = setup_logging("phase2_6_lock", PROJECT_ROOT / "outputs/phase2_6/logs/final_model_lock.log")
    resolved = validate_locked_feature_sets()
    config = load_yaml("configs/phase2_6_models.yaml")
    if int(config["canonical_seed"]) != 42 or bool(config["lock_policy"]["select_best_seed"]):
        raise RuntimeError("Canonical lock policy was changed")
    dataset = load_phase26_dataset()
    metric_rows, prediction_frames, validation_frames, calibration_rows, feature_rows = [], [], [], [], []
    for model_id in MODELS:
        categorical, numeric, _ = model_features(model_id)
        for feature in categorical:
            feature_rows.append({"model_id": model_id, "feature": feature, "role": "categorical"})
        for feature in numeric:
            feature_rows.append({"model_id": model_id, "feature": feature, "role": "numeric"})
    for population in ["Global", "Song", "Ming"]:
        for model_id in MODELS:
            run = fit_phase26_model(dataset, population, model_id, seed=42)
            model_path = PROJECT_ROOT / f"outputs/phase2_6/models/{population.lower()}/{model_id}.cbm"
            digest = save_catboost_atomic(run.model, model_path)
            row = dict(run.metric)
            row["model_sha256"] = digest
            row["model_path"] = str(model_path.relative_to(PROJECT_ROOT))
            row["feature_count"] = len(run.prepared.feature_names)
            metric_rows.append(row)
            prediction_frames.append(run.test_predictions)
            validation_frames.append(run.validation_predictions)
            calibration_rows.append({"population": population, "model_id": model_id, **run.calibration})
            logger.info("LOCK %s/%s AUC=%.6f SHA=%s", population, model_id, row["roc_auc"], digest[:12])
            if population == "Global":
                top_level = PROJECT_ROOT / f"outputs/phase2_6/models/{model_id}.cbm"
                top_level.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(model_path, top_level)
                if sha256_file(top_level) != digest:
                    raise RuntimeError(f"Global canonical model copy hash mismatch: {model_id}")
            del run
            gc.collect()
    metrics = pd.DataFrame(metric_rows)
    predictions = pd.concat(prediction_frames, ignore_index=True)
    validations = pd.concat(validation_frames, ignore_index=True)
    if predictions.duplicated(["person_id", "population", "model_id"]).any():
        raise RuntimeError("Canonical final predictions contain duplicate keys")
    tables = PROJECT_ROOT / "outputs/phase2_6/tables"
    atomic_to_csv(pd.DataFrame(feature_rows), tables / "final_model_feature_lists.csv")
    atomic_to_csv(metrics, tables / "final_model_metrics.csv")
    atomic_to_csv(pd.DataFrame(calibration_rows), tables / "final_model_calibration.csv")
    atomic_to_parquet(predictions, PROJECT_ROOT / "data/phase2_6/predictions/final_model_predictions.parquet")
    atomic_to_parquet(validations, PROJECT_ROOT / "data/phase2_6/predictions/final_model_validation_predictions.parquet")
    manifest = locked_manifest_payload(metrics)
    manifest["catboost_version"] = importlib.metadata.version("catboost")
    manifest["resolved_feature_lists"] = {
        model: resolved[model]["features"] for model in MODELS
    }
    manifest["exact_parameters"] = config["catboost"]
    manifest["reproduction_command"] = "python scripts/47_lock_final_models.py"
    atomic_write_text(tables / "final_model_lock_manifest.json", json_dump(manifest))
    atomic_write_text(
        PROJECT_ROOT / "outputs/phase2_6/models/canonical_model_metadata.json",
        json_dump({
            "status": "FINAL_MODELS_LOCKED",
            "canonical_seed": 42,
            "catboost_version": manifest["catboost_version"],
            "models": metric_rows,
            "parameters": config["catboost"],
        }),
    )
    logger.info("FINAL_MODELS_LOCKED: 9 canonical population-model runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
