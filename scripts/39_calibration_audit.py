#!/usr/bin/env python3
"""Audit raw CatBoost probabilities and validation-fitted sigmoid diagnostics."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import atomic_to_csv, load_yaml
from src.utils import setup_logging


MODELS = ["G5", "F2", "F3", "D0", "D6", "D6i"]


def source_predictions(evaluation_split: str) -> pd.DataFrame:
    suffix = f"_{evaluation_split}.parquet"
    parts = PROJECT_ROOT / "data/phase2_5/predictions/parts"
    files = {
        "geography": parts / f"geography_decomposition_predictions{suffix}",
        "family": parts / f"family_decomposition_predictions{suffix}",
        "documentation": parts / f"documentation_controlled_predictions{suffix}",
    }
    frames = [pd.read_parquet(path) for path in files.values()]
    frame = pd.concat(frames, ignore_index=True)
    frame = frame.loc[
        frame["algorithm"].eq("CatBoost")
        & frame["model_id"].isin(MODELS)
        & frame["subset"].eq("all")
    ]
    return frame.sort_values("model_id").drop_duplicates(["person_id", "population", "model_id"], keep="first")


def expected_calibration_error(y: np.ndarray, probability: np.ndarray, bins: int) -> float:
    edges = np.linspace(0.0, 1.0, bins + 1)
    bucket = np.clip(np.digitize(probability, edges[1:-1], right=True), 0, bins - 1)
    value = 0.0
    for index in range(bins):
        mask = bucket == index
        if mask.any():
            value += mask.mean() * abs(float(y[mask].mean()) - float(probability[mask].mean()))
    return float(value)


def reliability_rows(y: np.ndarray, probability: np.ndarray, bins: int, **keys) -> list[dict[str, object]]:
    edges = np.linspace(0.0, 1.0, bins + 1)
    bucket = np.clip(np.digitize(probability, edges[1:-1], right=True), 0, bins - 1)
    rows = []
    for index in range(bins):
        mask = bucket == index
        rows.append(keys | {
            "bin": index + 1,
            "bin_lower": edges[index],
            "bin_upper": edges[index + 1],
            "n_people": int(mask.sum()),
            "mean_predicted": float(probability[mask].mean()) if mask.any() else np.nan,
            "observed_rate": float(y[mask].mean()) if mask.any() else np.nan,
        })
    return rows


def atomic_savefig(figure: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.stem + ".tmp" + path.suffix)
    figure.savefig(temporary, dpi=300, bbox_inches="tight")
    os.replace(temporary, path)
    plt.close(figure)


def plot_population(reliability: pd.DataFrame, population: str, path: Path) -> None:
    figure, axes = plt.subplots(2, 3, figsize=(11, 7.5), sharex=True, sharey=True)
    for axis, model_id in zip(axes.flat, MODELS, strict=True):
        block = reliability.loc[
            reliability["population"].eq(population) & reliability["model_id"].eq(model_id)
        ]
        for calibration, color in [("raw", "#4c78a8"), ("validation_sigmoid", "#f58518")]:
            curve = block.loc[block["calibration"].eq(calibration) & block["n_people"].gt(0)]
            axis.plot(curve["mean_predicted"], curve["observed_rate"], marker="o", label=calibration, color=color)
        axis.plot([0, 1], [0, 1], linestyle="--", color="black", linewidth=0.8)
        axis.set_title(model_id)
        axis.grid(alpha=0.2)
    axes[0, 0].legend(frameon=False, fontsize=8)
    figure.supxlabel("Mean predicted probability")
    figure.supylabel("Observed target rate")
    figure.suptitle(f"Calibration audit — {population}")
    figure.tight_layout()
    atomic_savefig(figure, path)


def main() -> int:
    logger = setup_logging("phase2_5_calibration", PROJECT_ROOT / "outputs/phase2_5/logs/calibration.log")
    config = load_yaml("configs/phase2_5_models.yaml")
    bins = int(config["calibration_bins"])
    validation = source_predictions("validation")
    test = source_predictions("test")
    metric_rows, curve_rows = [], []
    for population in ["Global", "Song", "Ming"]:
        for model_id in MODELS:
            val = validation.loc[validation["population"].eq(population) & validation["model_id"].eq(model_id)]
            tst = test.loc[test["population"].eq(population) & test["model_id"].eq(model_id)]
            y_val = val["y_true"].to_numpy(int)
            p_val = np.clip(val["y_probability"].to_numpy(float), 1e-6, 1 - 1e-6)
            y_test = tst["y_true"].to_numpy(int)
            p_test = np.clip(tst["y_probability"].to_numpy(float), 1e-6, 1 - 1e-6)
            calibrator = LogisticRegression(solver="lbfgs", random_state=42)
            calibrator.fit(np.log(p_val / (1 - p_val)).reshape(-1, 1), y_val)
            p_sigmoid = calibrator.predict_proba(np.log(p_test / (1 - p_test)).reshape(-1, 1))[:, 1]
            variant = str(tst["model_variant"].iloc[0])
            for calibration, probability in [("raw", p_test), ("validation_sigmoid", p_sigmoid)]:
                metric_rows.append({
                    "population": population,
                    "model_id": model_id,
                    "model_variant": variant,
                    "calibration": calibration,
                    "n_test": len(tst),
                    "positive_rate": float(y_test.mean()),
                    "mean_probability": float(probability.mean()),
                    "probability_bias": float(probability.mean() - y_test.mean()),
                    "brier_score": float(brier_score_loss(y_test, probability)),
                    "log_loss": float(log_loss(y_test, probability, labels=[0, 1])),
                    "ece": expected_calibration_error(y_test, probability, bins),
                    "calibrator_fit_partition": "none" if calibration == "raw" else "validation",
                    "balanced_weight_probability_shift_risk": variant == "balanced",
                })
                curve_rows.extend(reliability_rows(
                    y_test, probability, bins,
                    population=population, model_id=model_id, calibration=calibration,
                ))
    metrics = pd.DataFrame(metric_rows)
    reliability = pd.DataFrame(curve_rows)
    atomic_to_csv(metrics, PROJECT_ROOT / "outputs/phase2_5/tables/calibration_audit.csv")
    atomic_to_csv(reliability, PROJECT_ROOT / "outputs/phase2_5/tables/calibration_reliability.csv")
    for population in ["Global", "Song", "Ming"]:
        plot_population(
            reliability, population,
            PROJECT_ROOT / f"outputs/phase2_5/figures/calibration_{population.lower()}.png",
        )
    logger.info("Calibration audit complete: %d raw/calibrated rows", len(metrics))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
