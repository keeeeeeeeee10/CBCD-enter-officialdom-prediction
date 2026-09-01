#!/usr/bin/env python3
"""Run native CatBoost SHAP for the nine canonical locked population models."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from catboost import Pool

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import atomic_to_csv, atomic_to_parquet, load_yaml
from src.modeling import predictor_frame
from src.phase26 import (
    feature_group_lookup, load_locked_model, load_phase26_dataset, prepare_phase26_data,
)
from src.utils import atomic_write_text, setup_logging


def stratified_sample(frame: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    if len(frame) <= n:
        return frame.sort_values("person_id").reset_index(drop=True)
    counts = frame["target_entry_v1"].value_counts().to_dict()
    n_positive = min(counts.get(1, 0), int(round(n * counts.get(1, 0) / len(frame))))
    n_negative = n - n_positive
    pieces = [
        frame.loc[frame["target_entry_v1"].eq(0)].sample(n=n_negative, random_state=seed),
        frame.loc[frame["target_entry_v1"].eq(1)].sample(n=n_positive, random_state=seed + 1),
    ]
    return pd.concat(pieces).sort_values("person_id").reset_index(drop=True)


def save_figure(figure: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.stem + ".tmp" + path.suffix)
    figure.savefig(temporary, dpi=300, bbox_inches="tight")
    os.replace(temporary, path)
    plt.close(figure)


def plot_groups(group: pd.DataFrame, model_id: str, population: str, path: Path) -> None:
    block = group.sort_values("mean_abs_shap", ascending=True)
    figure, axis = plt.subplots(figsize=(8, max(4.5, 0.42 * len(block))))
    axis.barh(block["feature_group"], block["mean_abs_shap"], color="#4c78a8")
    axis.set_xlabel("Mean absolute SHAP value (raw model output)")
    axis.set_ylabel("Feature group")
    axis.set_title(f"{model_id} — {population}: grouped prediction attribution")
    axis.grid(axis="x", alpha=0.2)
    figure.tight_layout()
    save_figure(figure, path)


def plot_features(feature: pd.DataFrame, model_id: str, population: str, path: Path) -> None:
    block = feature.nsmallest(20, "rank").sort_values("mean_abs_shap", ascending=True)
    figure, axis = plt.subplots(figsize=(8.5, 7))
    axis.barh(block["feature"], block["mean_abs_shap"], color="#f58518")
    axis.set_xlabel("Mean absolute SHAP value (raw model output)")
    axis.set_ylabel("Feature")
    axis.set_title(f"{model_id} — {population}: top feature attribution")
    axis.grid(axis="x", alpha=0.2)
    figure.tight_layout()
    save_figure(figure, path)


def plot_beeswarm(
    x: pd.DataFrame,
    shap: np.ndarray,
    features: list[str],
    feature_summary: pd.DataFrame,
    model_id: str,
    population: str,
    max_rows: int,
    path: Path,
) -> None:
    top = feature_summary.nsmallest(20, "rank")["feature"].tolist()[::-1]
    indices = np.linspace(0, len(x) - 1, min(max_rows, len(x)), dtype=int)
    rng = np.random.default_rng(42)
    figure, axis = plt.subplots(figsize=(9, 8))
    for y_index, feature in enumerate(top):
        feature_index = features.index(feature)
        values = shap[indices, feature_index]
        source = pd.to_numeric(x.iloc[indices][feature], errors="coerce").to_numpy(float)
        jitter = rng.normal(0, 0.095, len(indices))
        if np.isfinite(source).sum() > 10:
            finite = source[np.isfinite(source)]
            low, high = np.quantile(finite, [0.05, 0.95])
            colour = np.clip((source - low) / max(high - low, 1e-12), 0, 1)
            colour[~np.isfinite(colour)] = 0.5
            axis.scatter(values, y_index + jitter, c=colour, cmap="coolwarm", s=4, alpha=0.35, linewidths=0)
        else:
            axis.scatter(values, y_index + jitter, color="#6f6f6f", s=4, alpha=0.3, linewidths=0)
    axis.axvline(0, color="black", linewidth=0.8)
    axis.set_yticks(range(len(top)), top)
    axis.set_xlabel("SHAP value (raw model output)")
    axis.set_ylabel("Feature")
    axis.set_title(f"{model_id} — {population}: top-feature SHAP distribution")
    axis.grid(axis="x", alpha=0.15)
    figure.tight_layout()
    save_figure(figure, path)


def direction_rows(
    x: pd.DataFrame, shap: np.ndarray, features: list[str], groups: dict[str, str],
    model_id: str, population: str,
) -> list[dict[str, object]]:
    rows = []
    for index, feature in enumerate(features):
        feature_shap = shap[:, index]
        numeric = pd.to_numeric(x[feature], errors="coerce")
        valid = numeric.notna().to_numpy()
        correlation = np.nan
        if valid.sum() >= 20 and numeric[valid].nunique() > 1:
            correlation = float(np.corrcoef(numeric.to_numpy(float)[valid], feature_shap[valid])[0, 1])
            method = "numeric_pearson_value_vs_shap"
            positive_descriptor = "higher numeric values" if correlation >= 0 else "lower numeric values"
            negative_descriptor = "lower numeric values" if correlation >= 0 else "higher numeric values"
        else:
            category = x[feature].astype("string").fillna("__MISSING__")
            means = pd.DataFrame({"category": category, "shap": feature_shap}).groupby("category")["shap"].agg(["mean", "size"])
            means = means.loc[means["size"].ge(max(5, int(0.001 * len(x))))]
            method = "category_mean_shap"
            positive_descriptor = str(means["mean"].idxmax()) if len(means) else "insufficient support"
            negative_descriptor = str(means["mean"].idxmin()) if len(means) else "insufficient support"
        rows.append({
            "model_id": model_id,
            "population": population,
            "feature": feature,
            "feature_group": groups[feature],
            "direction_method": method,
            "value_shap_correlation": correlation,
            "positive_descriptor": positive_descriptor,
            "negative_descriptor": negative_descriptor,
            "positive_shap_share": float((feature_shap > 0).mean()),
            "negative_shap_share": float((feature_shap < 0).mean()),
            "signed_mean_shap": float(feature_shap.mean()),
        })
    return rows


def main() -> int:
    logger = setup_logging("phase2_6_shap", PROJECT_ROOT / "outputs/phase2_6/logs/grouped_shap.log")
    lock = json.loads((PROJECT_ROOT / "outputs/phase2_6/tables/final_model_lock_manifest.json").read_text())
    if lock.get("status") != "FINAL_MODELS_LOCKED":
        raise RuntimeError("Formal SHAP cannot run before FINAL_MODELS_LOCKED")
    config = load_yaml("configs/phase2_6_shap.yaml")
    dataset = load_phase26_dataset()
    primary = pd.read_parquet(PROJECT_ROOT / "data/splits/split_primary_dynasty_target.parquet")
    sample_frames = []
    samples: dict[str, pd.DataFrame] = {}
    for population in config["populations"]:
        eligible = dataset.merge(primary, on="person_id", how="inner", validate="one_to_one")
        eligible = eligible.loc[eligible["split"].eq("test")]
        if population != "Global":
            eligible = eligible.loc[eligible["dynasty_name"].eq(population)]
        sample = stratified_sample(
            eligible[["person_id", "target_entry_v1"]],
            int(config["max_explanation_rows_per_population"]), int(config["sample_seed"]),
        )
        samples[population] = sample
        sample_frames.append(pd.DataFrame({
            "person_id": sample["person_id"].astype("int64"),
            "population": population,
            "target": "target_entry_v1",
            "split": "frozen_primary_test",
            "sample_seed": int(config["sample_seed"]),
        }))
    sample_ids = pd.concat(sample_frames, ignore_index=True)
    atomic_to_parquet(sample_ids, PROJECT_ROOT / "data/phase2_6/shap_samples/shap_sample_ids.parquet")

    feature_rows, group_rows, directions, raw_frames, checks = [], [], [], [], []
    figures = PROJECT_ROOT / "outputs/phase2_6/figures"
    tolerance = float(config["additivity_absolute_tolerance"])
    for population in config["populations"]:
        sample = samples[population]
        for model_id in config["models"]:
            prepared = prepare_phase26_data(dataset, population, model_id, seed=42)
            test = prepared.test.set_index("person_id").loc[sample["person_id"]].reset_index()
            if list(test["person_id"]) != list(sample["person_id"]):
                raise RuntimeError(f"SHAP sample alignment failure: {population}/{model_id}")
            x = predictor_frame(test, prepared)
            categorical_indices = [x.columns.get_loc(column) for column in prepared.categorical]
            pool = Pool(x, cat_features=categorical_indices)
            model = load_locked_model(population, model_id)
            shap_all = np.asarray(model.get_feature_importance(pool, type="ShapValues"), dtype=float)
            feature_shap, base = shap_all[:, :-1], shap_all[:, -1]
            raw_prediction = np.asarray(model.predict(pool, prediction_type="RawFormulaVal"), dtype=float)
            probability = np.asarray(model.predict_proba(pool)[:, 1], dtype=float)
            error = np.abs(base + feature_shap.sum(axis=1) - raw_prediction)
            check_n = min(int(config["additivity_check_rows"]), len(error))
            checked_error = error[:check_n]
            status = "PASS" if float(checked_error.max()) <= tolerance else "FAIL"
            if status != "PASS":
                raise RuntimeError(f"SHAP additivity failed for {population}/{model_id}: {checked_error.max()}")
            groups = feature_group_lookup(prepared.feature_names)
            feature_block = pd.DataFrame({
                "model_id": model_id,
                "population": population,
                "feature": prepared.feature_names,
                "feature_group": [groups[name] for name in prepared.feature_names],
                "mean_abs_shap": np.mean(np.abs(feature_shap), axis=0),
                "median_abs_shap": np.median(np.abs(feature_shap), axis=0),
                "signed_mean_shap": np.mean(feature_shap, axis=0),
                "sample_n": len(x),
            }).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
            feature_block["rank"] = np.arange(1, len(feature_block) + 1)
            feature_rows.extend(feature_block.to_dict("records"))
            group_block = feature_block.groupby(["model_id", "population", "feature_group"], as_index=False).agg(
                mean_abs_shap=("mean_abs_shap", "sum"),
                signed_mean_shap=("signed_mean_shap", "sum"),
                n_features=("feature", "size"),
                sample_n=("sample_n", "first"),
            )
            group_block["group_share_of_total_abs_shap"] = group_block["mean_abs_shap"] / group_block["mean_abs_shap"].sum()
            group_block = group_block.sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
            group_block["rank"] = np.arange(1, len(group_block) + 1)
            share_sum = float(group_block["group_share_of_total_abs_shap"].sum())
            if abs(share_sum - 1.0) > float(config["group_share_tolerance"]):
                raise RuntimeError(f"SHAP group shares do not sum to one: {population}/{model_id}/{share_sum}")
            group_rows.extend(group_block.to_dict("records"))
            directions.extend(direction_rows(x, feature_shap, prepared.feature_names, groups, model_id, population))
            raw_n = min(int(config["max_raw_rows_per_model_population"]), len(x))
            raw_indices = np.linspace(0, len(x) - 1, raw_n, dtype=int)
            raw = pd.DataFrame({
                "person_id": test.iloc[raw_indices]["person_id"].astype("int64").to_numpy(),
                "population": population,
                "model_id": model_id,
                "target": "target_entry_v1",
                "y_true": test.iloc[raw_indices]["target_entry_v1"].astype("int8").to_numpy(),
                "base_value": base[raw_indices],
                "raw_prediction": raw_prediction[raw_indices],
                "probability": probability[raw_indices],
            })
            for index, feature in enumerate(prepared.feature_names):
                raw[f"shap__{feature}"] = feature_shap[raw_indices, index]
            for group in sorted(set(groups.values())):
                indices = [index for index, feature in enumerate(prepared.feature_names) if groups[feature] == group]
                raw[f"group_shap__{group}"] = feature_shap[raw_indices][:, indices].sum(axis=1)
            raw_frames.append(raw)
            checks.append({
                "model_id": model_id,
                "population": population,
                "sample_n": len(x),
                "rows_checked": check_n,
                "max_abs_additivity_error": float(checked_error.max()),
                "mean_abs_additivity_error": float(checked_error.mean()),
                "tolerance": tolerance,
                "group_share_sum": share_sum,
                "status": status,
            })
            suffix = f"{model_id}_{population.lower()}"
            plot_groups(group_block, model_id, population, figures / f"shap_{suffix}_groups.png")
            plot_features(feature_block, model_id, population, figures / f"shap_{suffix}_features.png")
            plot_beeswarm(
                x, feature_shap, prepared.feature_names, feature_block, model_id, population,
                int(config["plot_rows_per_model_population"]), figures / f"shap_{suffix}_beeswarm.png",
            )
            logger.info(
                "SHAP %s/%s n=%d max_additivity_error=%.3g top_group=%s",
                population, model_id, len(x), checked_error.max(), group_block.iloc[0]["feature_group"],
            )

    shap_dir = PROJECT_ROOT / "outputs/phase2_6/shap"
    atomic_to_csv(pd.DataFrame(feature_rows), shap_dir / "shap_feature_summary.csv")
    atomic_to_csv(pd.DataFrame(group_rows), shap_dir / "shap_group_summary.csv")
    atomic_to_csv(pd.DataFrame(directions), shap_dir / "shap_direction_summary.csv")
    atomic_to_parquet(
        pd.concat(raw_frames, ignore_index=True, sort=False),
        PROJECT_ROOT / "data/phase2_6/shap_samples/shap_values_sample.parquet",
    )
    payload = {
        "status": "PASS",
        "implementation": "CatBoost native ShapValues",
        "output_space": "raw_model_logit",
        "formal_shap_run": True,
        "causal_interpretation": False,
        "checks": checks,
    }
    atomic_write_text(
        shap_dir / "shap_additivity_check.json",
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
