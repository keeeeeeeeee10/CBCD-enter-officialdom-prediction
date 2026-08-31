#!/usr/bin/env python3
"""Bootstrap primary test-set ROC-AUC and PR-AUC confidence intervals."""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import atomic_to_csv, load_yaml
from src.metrics import bootstrap_auc_intervals
from src.utils import setup_logging


PREDICTION_FILES = {
    "LogisticRegression": PROJECT_ROOT / "data/modeling/phase2_predictions_logistic.parquet",
    "CatBoost": PROJECT_ROOT / "data/modeling/phase2_predictions_catboost.parquet",
}
POPULATIONS = ["Global", "Song", "Ming"]
FEATURE_SETS = ["M0", "M0b", "M1", "M2", "M3", "M4", "M5", "M6"]


def stable_seed(*parts: object) -> int:
    digest = hashlib.sha256("|".join(map(str, parts)).encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "little")


def main() -> int:
    logger = setup_logging("phase2_bootstrap", PROJECT_ROOT / "outputs/logs/phase2_bootstrap.log")
    model_config = load_yaml("configs/phase2_models.yaml")
    n_resamples = int(os.environ.get("PHASE2_BOOTSTRAP_RESAMPLES", model_config["bootstrap_resamples"]))
    confidence = float(model_config["bootstrap_confidence"])
    rows: list[dict[str, object]] = []
    for algorithm, path in PREDICTION_FILES.items():
        if not path.exists():
            raise RuntimeError(f"Missing prediction file: {path}")
        frame = pd.read_parquet(path)
        for population in POPULATIONS:
            for feature_set in FEATURE_SETS:
                subset = frame.loc[
                    frame["population"].eq(population) & frame["feature_set"].eq(feature_set)
                ].sort_values("person_id")
                if subset.empty or subset["person_id"].duplicated().any():
                    raise RuntimeError(f"Invalid predictions for {algorithm}/{population}/{feature_set}")
                y = subset["y_true"].astype(int).to_numpy()
                probability = subset["y_probability"].to_numpy(dtype=float)
                interval = bootstrap_auc_intervals(
                    y,
                    probability,
                    n_resamples=n_resamples,
                    seed=stable_seed(algorithm, population, feature_set),
                    confidence=confidence,
                )
                rows.append({
                    "analysis": "primary_model",
                    "algorithm": algorithm,
                    "population": population,
                    "feature_set": feature_set,
                    "split_protocol": "primary",
                    "evaluation_split": "test",
                    "n_test": len(subset),
                    "roc_auc": float(roc_auc_score(y, probability)),
                    "pr_auc": float(average_precision_score(y, probability)),
                    **interval,
                })
                logger.info(
                    "%s/%s/%s bootstrap interval complete", algorithm, population, feature_set
                )
    output = pd.DataFrame(rows).sort_values(["algorithm", "population", "feature_set"])
    atomic_to_csv(output, PROJECT_ROOT / "outputs/phase2/tables/bootstrap_intervals.csv")
    logger.info("Bootstrap complete: %d intervals; resamples=%d", len(output), n_resamples)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
