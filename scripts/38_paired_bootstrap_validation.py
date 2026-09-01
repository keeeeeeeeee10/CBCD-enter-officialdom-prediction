#!/usr/bin/env python3
"""Consolidate core predictions and compute paired/cluster bootstrap deltas."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, log_loss, roc_auc_score

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import atomic_to_csv, atomic_to_parquet, load_yaml
from src.phase25 import load_phase25_dataset
from src.utils import setup_logging


PREDICTION_COLUMNS = [
    "person_id", "population", "split_protocol", "target_name", "algorithm",
    "model_id", "subset", "model_variant", "evaluation_split", "y_true",
    "y_probability", "validation_frozen_threshold", "y_pred",
    "family_group_id", "spatial_group_id",
]


def phase2_original_predictions(dataset: pd.DataFrame, split_protocol: str) -> pd.DataFrame:
    if split_protocol == "primary":
        raw = pd.concat([
            pd.read_parquet(PROJECT_ROOT / "data/modeling/phase2_predictions_logistic.parquet"),
            pd.read_parquet(PROJECT_ROOT / "data/modeling/phase2_predictions_catboost.parquet"),
        ], ignore_index=True)
        raw = raw.loc[raw["feature_set"].isin(["M3", "M4", "M5", "M6"])]
    else:
        raw = pd.read_parquet(PROJECT_ROOT / "data/modeling/phase2_predictions_robustness.parquet")
        raw = raw.loc[raw["split_protocol"].eq("family") & raw["feature_set"].isin(["M0", "M4"])]
    metrics = pd.read_csv(PROJECT_ROOT / "outputs/phase2/tables/model_metrics.csv")
    thresholds = metrics.loc[
        metrics["split_protocol"].eq(split_protocol)
        & metrics["threshold_source"].eq("validation_balanced_accuracy")
    ][["algorithm", "model_variant", "population", "feature_set", "threshold"]]
    merged = raw.merge(
        thresholds,
        on=["algorithm", "model_variant", "population", "feature_set"],
        how="left",
        validate="many_to_one",
    ).merge(
        dataset[["person_id", "family_group_id", "spatial_group_id"]],
        on="person_id", how="left", validate="many_to_one",
    )
    if merged["threshold"].isna().any():
        raise RuntimeError(f"Missing Phase 2 frozen validation threshold for {split_protocol}")
    return pd.DataFrame({
        "person_id": merged["person_id"].astype("int64"),
        "population": merged["population"],
        "split_protocol": split_protocol,
        "target_name": "target_entry_v1",
        "algorithm": merged["algorithm"],
        "model_id": merged["feature_set"],
        "subset": "all",
        "model_variant": merged["model_variant"],
        "evaluation_split": "test",
        "y_true": merged["y_true"].astype("int8"),
        "y_probability": merged["y_probability"].astype(float),
        "validation_frozen_threshold": merged["threshold"].astype(float),
        "y_pred": merged["y_probability"].ge(merged["threshold"]).astype("int8"),
        "family_group_id": merged["family_group_id"].astype("int64"),
        "spatial_group_id": merged["spatial_group_id"].astype("string"),
    })


def read_part(name: str) -> pd.DataFrame:
    return pd.read_parquet(PROJECT_ROOT / f"data/phase2_5/predictions/parts/{name}_test.parquet")[PREDICTION_COLUMNS]


def consolidate_predictions(dataset: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    primary = pd.concat([
        read_part("personal_decomposition_results"),
        read_part("geography_decomposition_predictions"),
        read_part("family_decomposition_predictions"),
        read_part("documentation_controlled_predictions"),
        phase2_original_predictions(dataset, "primary"),
    ], ignore_index=True)
    family = pd.concat([
        read_part("family_holdout_predictions"),
        phase2_original_predictions(dataset, "family"),
    ], ignore_index=True)
    spatial = read_part("spatial_robustness_predictions")
    targets = read_part("target_sensitivity_predictions")
    output_dir = PROJECT_ROOT / "data/phase2_5/predictions"
    atomic_to_parquet(primary, output_dir / "predictions_primary_core.parquet")
    atomic_to_parquet(family, output_dir / "predictions_family_robustness.parquet")
    atomic_to_parquet(spatial, output_dir / "predictions_spatial_robustness.parquet")
    atomic_to_parquet(targets, output_dir / "predictions_target_sensitivity.parquet")
    return primary, family, spatial, targets


def paired_frames(predictions: pd.DataFrame, population: str, algorithm: str, target: str, split_protocol: str, model_a: str, model_b: str) -> pd.DataFrame:
    key = (
        predictions["population"].eq(population)
        & predictions["algorithm"].eq(algorithm)
        & predictions["target_name"].eq(target)
        & predictions["split_protocol"].eq(split_protocol)
        & predictions["subset"].eq("all")
        & predictions["evaluation_split"].eq("test")
    )
    a = predictions.loc[key & predictions["model_id"].eq(model_a), [
        "person_id", "y_true", "y_probability", "family_group_id", "spatial_group_id"
    ]].rename(columns={"y_probability": "probability_a"})
    b = predictions.loc[key & predictions["model_id"].eq(model_b), [
        "person_id", "y_true", "y_probability"
    ]].rename(columns={"y_true": "y_true_b", "y_probability": "probability_b"})
    if a["person_id"].duplicated().any() or b["person_id"].duplicated().any():
        raise RuntimeError(f"Duplicate prediction rows for {model_a}/{model_b}")
    if set(a["person_id"]) != set(b["person_id"]):
        raise RuntimeError(f"Paired prediction IDs differ: {population}/{algorithm}/{model_a}/{model_b}")
    merged = a.merge(b, on="person_id", validate="one_to_one")
    if not merged["y_true"].eq(merged["y_true_b"]).all():
        raise RuntimeError("Paired prediction targets differ")
    return merged.drop(columns="y_true_b")


def metric_triplet(y: np.ndarray, probability: np.ndarray) -> np.ndarray:
    p = np.clip(probability, 1e-8, 1 - 1e-8)
    return np.array([
        roc_auc_score(y, p),
        average_precision_score(y, p),
        log_loss(y, p, labels=[0, 1]),
    ])


def paired_bootstrap(
    frame: pd.DataFrame,
    n_bootstrap: int,
    seed: int,
    unit: str,
    cluster_column: str | None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    y = frame["y_true"].to_numpy(dtype=np.int8)
    pa = frame["probability_a"].to_numpy(float)
    pb = frame["probability_b"].to_numpy(float)
    observed = metric_triplet(y, pb) - metric_triplet(y, pa)
    rng = np.random.default_rng(seed)
    deltas = np.empty((n_bootstrap, 3), dtype=float)
    positive = np.flatnonzero(y == 1)
    negative = np.flatnonzero(y == 0)
    if cluster_column:
        codes, uniques = pd.factorize(frame[cluster_column].astype("string").fillna("__MISSING__"), sort=True)
        n_clusters = len(uniques)
    for iteration in range(n_bootstrap):
        if unit == "stratified_individual":
            index = np.concatenate([
                rng.choice(positive, size=len(positive), replace=True),
                rng.choice(negative, size=len(negative), replace=True),
            ])
        else:
            sampled = rng.integers(0, n_clusters, size=n_clusters)
            weights = np.bincount(sampled, minlength=n_clusters)
            index = np.repeat(np.arange(len(frame)), weights[codes])
            if len(np.unique(y[index])) < 2:
                index = np.arange(len(frame))
        deltas[iteration] = metric_triplet(y[index], pb[index]) - metric_triplet(y[index], pa[index])
    return observed, np.quantile(deltas, [0.025, 0.975], axis=0), (deltas > 0).mean(axis=0)


def comparison_specs() -> list[tuple[str, str, str, str]]:
    specs = []
    for a, b in [("G1", "G2"), ("G2", "G3"), ("G3", "G4"), ("G4", "G5")]:
        specs.append(("primary", "CatBoost", a, b))
    for a, b in [("F1", "F2"), ("F2", "F3"), ("F2", "F4")]:
        specs.append(("primary", "CatBoost", a, b))
    for algorithm in ["CatBoost", "LogisticRegression"]:
        for a, b in [("D0", "D1"), ("D1", "D2"), ("D2", "D3"), ("D3", "D4"), ("D4", "D5"), ("D5", "D6"), ("D5", "D6i")]:
            if algorithm == "LogisticRegression" and (a == "D3" and b == "D4" or a == "D4" and b == "D5"):
                continue
            specs.append(("primary", algorithm, a, b))
    for algorithm in ["CatBoost", "LogisticRegression"]:
        specs.extend([("primary", algorithm, "M3", "M4"), ("primary", algorithm, "M5", "M6")])
    return specs


def run_comparisons(primary: pd.DataFrame, family: pd.DataFrame, spatial: pd.DataFrame, config: dict) -> pd.DataFrame:
    rows = []
    n = int(config["bootstrap_resamples"])
    seed = int(config["seed"])
    metric_names = ["roc_auc", "pr_auc", "log_loss"]
    for split_protocol, algorithm, model_a, model_b in comparison_specs():
        for population in ["Global", "Song", "Ming"]:
            paired = paired_frames(primary, population, algorithm, "target_entry_v1", split_protocol, model_a, model_b)
            observed, interval, fraction = paired_bootstrap(paired, n, seed, "stratified_individual", None)
            for index, metric in enumerate(metric_names):
                rows.append({
                    "population": population, "algorithm": algorithm, "target": "target_entry_v1",
                    "split_protocol": split_protocol, "model_a": model_a, "model_b": model_b,
                    "metric": metric, "observed_delta": observed[index], "ci_lower": interval[0, index],
                    "ci_upper": interval[1, index], "fraction_delta_positive": fraction[index],
                    "n_bootstrap": n, "bootstrap_unit": "stratified_individual",
                    "practical_magnitude_small": bool(metric == "roc_auc" and abs(observed[index]) < 0.005),
                })
    for population in ["Global", "Ming"]:
        for model_a, model_b in [("F1", "F2"), ("F2", "F3"), ("F2", "F4")]:
            paired = paired_frames(family, population, "CatBoost", "target_entry_v1", "family", model_a, model_b)
            observed, interval, fraction = paired_bootstrap(paired, n, seed, "family_cluster", "family_group_id")
            for index, metric in enumerate(metric_names):
                rows.append({
                    "population": population, "algorithm": "CatBoost", "target": "target_entry_v1",
                    "split_protocol": "family", "model_a": model_a, "model_b": model_b,
                    "metric": metric, "observed_delta": observed[index], "ci_lower": interval[0, index],
                    "ci_upper": interval[1, index], "fraction_delta_positive": fraction[index],
                    "n_bootstrap": n, "bootstrap_unit": "family_group_id",
                    "practical_magnitude_small": bool(metric == "roc_auc" and abs(observed[index]) < 0.005),
                })
    for population in ["Global", "Song", "Ming"]:
        paired = paired_frames(spatial, population, "CatBoost", "target_entry_v1", "spatial", "G4", "G5")
        observed, interval, fraction = paired_bootstrap(paired, n, seed, "spatial_cluster", "spatial_group_id")
        for index, metric in enumerate(metric_names):
            rows.append({
                "population": population, "algorithm": "CatBoost", "target": "target_entry_v1",
                "split_protocol": "spatial", "model_a": "G4", "model_b": "G5",
                "metric": metric, "observed_delta": observed[index], "ci_lower": interval[0, index],
                "ci_upper": interval[1, index], "fraction_delta_positive": fraction[index],
                "n_bootstrap": n, "bootstrap_unit": "spatial_group_id",
                "practical_magnitude_small": bool(metric == "roc_auc" and abs(observed[index]) < 0.005),
            })
    return pd.DataFrame(rows)


def atomic_savefig(figure: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.stem + ".tmp" + path.suffix)
    figure.savefig(temporary, dpi=300, bbox_inches="tight")
    os.replace(temporary, path)
    plt.close(figure)


def plot_intervals(results: pd.DataFrame, path: Path) -> None:
    selected = results.loc[
        results["metric"].eq("roc_auc")
        & results["population"].eq("Global")
        & results["algorithm"].eq("CatBoost")
        & results["split_protocol"].eq("primary")
    ].copy()
    selected["comparison"] = selected["model_b"] + " − " + selected["model_a"]
    selected = selected.sort_values("observed_delta")
    y = np.arange(len(selected))
    figure, axis = plt.subplots(figsize=(8, max(4.5, len(selected) * 0.36)))
    axis.errorbar(
        selected["observed_delta"], y,
        xerr=np.vstack([
            selected["observed_delta"] - selected["ci_lower"],
            selected["ci_upper"] - selected["observed_delta"],
        ]),
        fmt="o", color="#4c78a8", ecolor="#9ecae9", capsize=3,
    )
    axis.axvline(0, color="black", linewidth=1)
    axis.set_yticks(y, selected["comparison"])
    axis.set_xlabel("Paired Δ ROC-AUC (model B − model A)")
    axis.set_title("Global CatBoost paired bootstrap, frozen primary test")
    axis.grid(axis="x", alpha=0.25)
    figure.tight_layout()
    atomic_savefig(figure, path)


def main() -> int:
    logger = setup_logging("phase2_5_paired", PROJECT_ROOT / "outputs/phase2_5/logs/paired_bootstrap.log")
    dataset = load_phase25_dataset()
    primary, family, spatial, targets = consolidate_predictions(dataset)
    config = load_yaml("configs/phase2_5_models.yaml")
    results = run_comparisons(primary, family, spatial, config)
    atomic_to_csv(results, PROJECT_ROOT / "outputs/phase2_5/tables/paired_bootstrap_results.csv")
    plot_intervals(results, PROJECT_ROOT / "outputs/phase2_5/figures/paired_delta_ci.png")
    logger.info(
        "Prediction export/paired bootstrap complete: primary=%d family=%d spatial=%d targets=%d result_rows=%d",
        len(primary), len(family), len(spatial), len(targets), len(results),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
