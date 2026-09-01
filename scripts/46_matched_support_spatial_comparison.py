#!/usr/bin/env python3
"""Compare random and spatial splits on the identical reliable-geography support."""

from __future__ import annotations

import gc
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import atomic_to_csv, atomic_to_parquet, load_yaml
from src.metrics import bootstrap_auc_intervals
from src.phase26 import fit_phase26_model, load_phase26_dataset
from src.utils import atomic_write_text, setup_logging


PARTITIONS = ["train", "validation", "test"]


def stable_hash(person_id: int, seed: int = 42) -> int:
    return int.from_bytes(hashlib.sha256(f"{seed}|{person_id}".encode()).digest()[:8], "little")


def matched_random_split(eligible: pd.DataFrame, fractions: dict[str, float], population: str) -> pd.DataFrame:
    strata = ["target_entry_v1"] if population != "Global" else ["dynasty_name", "target_entry_v1"]
    rows = []
    for _, block in eligible.groupby(strata, dropna=False, sort=True):
        ordered = block[["person_id"]].assign(
            tie=block["person_id"].astype(int).map(stable_hash).to_numpy()
        ).sort_values(["tie", "person_id"], kind="mergesort")
        n = len(ordered)
        n_train = int(round(n * fractions["train"]))
        n_validation = int(round(n * fractions["validation"]))
        n_train = min(n_train, n)
        n_validation = min(n_validation, n - n_train)
        labels = np.array(
            ["train"] * n_train + ["validation"] * n_validation + ["test"] * (n - n_train - n_validation),
            dtype=object,
        )
        ordered["split"] = labels
        rows.append(ordered[["person_id", "split"]])
    result = pd.concat(rows, ignore_index=True).sort_values("person_id").reset_index(drop=True)
    if result["person_id"].duplicated().any() or len(result) != len(eligible):
        raise RuntimeError(f"Matched random split invalid for {population}")
    return result


def summary(split: pd.DataFrame, eligible: pd.DataFrame, population: str, protocol: str) -> list[dict[str, object]]:
    merged = split.merge(
        eligible[["person_id", "target_entry_v1", "dynasty_name", "spatial_group_id"]],
        on="person_id", how="left", validate="one_to_one", suffixes=("", "_feature"),
    )
    if "spatial_group_id_feature" in merged:
        merged["spatial_group_id"] = merged.get("spatial_group_id", merged["spatial_group_id_feature"]).fillna(merged["spatial_group_id_feature"])
    return [{
        "population": population,
        "protocol": protocol,
        "split": partition,
        "n_people": len(block),
        "positive_rate": float(block["target_entry_v1"].mean()),
        "n_spatial_groups": int(block["spatial_group_id"].nunique()),
    } for partition, block in merged.groupby("split", sort=True)]


def main() -> int:
    logger = setup_logging("phase2_6_matched_spatial", PROJECT_ROOT / "outputs/phase2_6/logs/matched_spatial.log")
    config = load_yaml("configs/phase2_6_models.yaml")
    dataset = load_phase26_dataset()
    support_rows, random_summaries, spatial_summaries, result_rows = [], [], [], []
    overlap_payload: dict[str, object] = {"status": "PASS", "populations": {}}
    split_paths: dict[tuple[str, str], Path] = {}
    for population in ["Global", "Song", "Ming"]:
        eligible = dataset.loc[dataset["spatial_group_id"].notna()].copy()
        if population != "Global":
            eligible = eligible.loc[eligible["dynasty_name"].eq(population)].copy()
        source_spatial = pd.read_parquet(
            PROJECT_ROOT / f"data/phase2_5/splits/split_spatial_group_{population.lower()}.parquet"
        )
        source_spatial = source_spatial.loc[source_spatial["person_id"].isin(eligible["person_id"])].copy()
        if set(source_spatial["person_id"]) != set(eligible["person_id"]):
            raise RuntimeError(f"Spatial support differs from reliable-geography support for {population}")
        fractions = source_spatial["split"].value_counts(normalize=True).to_dict()
        random_split = matched_random_split(eligible, fractions, population)
        random_path = PROJECT_ROOT / f"data/phase2_6/splits/matched_random_{population.lower()}.parquet"
        spatial_path = PROJECT_ROOT / f"data/phase2_6/splits/matched_spatial_{population.lower()}.parquet"
        atomic_to_parquet(random_split, random_path)
        atomic_to_parquet(source_spatial[["person_id", "spatial_group_id", "split"]], spatial_path)
        split_paths[(population, "matched_random")] = random_path
        split_paths[(population, "matched_spatial")] = spatial_path
        support_rows.append({
            "population": population,
            "n_people": len(eligible),
            "n_positive": int(eligible["target_entry_v1"].sum()),
            "positive_rate": float(eligible["target_entry_v1"].mean()),
            "n_spatial_groups": int(eligible["spatial_group_id"].nunique()),
            "support_definition": "nonmissing dynasty_code and historical prefecture_id",
        })
        random_summaries.extend(summary(random_split, eligible, population, "matched_random"))
        spatial_summaries.extend(summary(source_spatial, eligible, population, "matched_spatial"))
        group_sets = {
            part: set(source_spatial.loc[source_spatial["split"].eq(part), "spatial_group_id"])
            for part in PARTITIONS
        }
        intersections = {
            "train_validation": len(group_sets["train"] & group_sets["validation"]),
            "train_test": len(group_sets["train"] & group_sets["test"]),
            "validation_test": len(group_sets["validation"] & group_sets["test"]),
        }
        if any(intersections.values()):
            raise RuntimeError(f"Matched spatial overlap for {population}: {intersections}")
        overlap_payload["populations"][population] = {"status": "PASS", "intersections": intersections}

    for population in ["Global", "Song", "Ming"]:
        for protocol in ["matched_random", "matched_spatial"]:
            for model_id in ["H_STRUCT", "D5_MAIN"]:
                run = fit_phase26_model(
                    dataset, population, model_id, seed=42,
                    split_path=split_paths[(population, protocol)], split_protocol=protocol,
                )
                ci = bootstrap_auc_intervals(
                    run.test_predictions["y_true"].to_numpy(int),
                    run.test_predictions["y_probability_raw"].to_numpy(float),
                    n_resamples=int(config["bootstrap_resamples"]), seed=42,
                    confidence=float(config["bootstrap_confidence"]),
                )
                result_rows.append(run.metric | ci)
                logger.info("Matched %s/%s/%s AUC=%.6f", protocol, population, model_id, run.metric["roc_auc"])
                del run
                gc.collect()

    results = pd.DataFrame(result_rows)
    comparison_rows = []
    for (population, model_id), group in results.groupby(["population", "model_id"]):
        indexed = group.set_index("split_protocol")
        random_row, spatial_row = indexed.loc["matched_random"], indexed.loc["matched_spatial"]
        comparison_rows.append({
            "population": population,
            "model_id": model_id,
            "support_definition": "identical reliable historical-prefecture population",
            "matched_random_roc_auc": random_row["roc_auc"],
            "matched_spatial_roc_auc": spatial_row["roc_auc"],
            "delta_spatial_minus_random_roc_auc": spatial_row["roc_auc"] - random_row["roc_auc"],
            "matched_random_pr_auc": random_row["pr_auc"],
            "matched_spatial_pr_auc": spatial_row["pr_auc"],
            "delta_spatial_minus_random_pr_auc": spatial_row["pr_auc"] - random_row["pr_auc"],
            "random_roc_ci_lower": random_row["roc_auc_ci_low"],
            "random_roc_ci_upper": random_row["roc_auc_ci_high"],
            "spatial_roc_ci_lower": spatial_row["roc_auc_ci_low"],
            "spatial_roc_ci_upper": spatial_row["roc_auc_ci_high"],
            "random_pr_ci_lower": random_row["pr_auc_ci_low"],
            "random_pr_ci_upper": random_row["pr_auc_ci_high"],
            "spatial_pr_ci_lower": spatial_row["pr_auc_ci_low"],
            "spatial_pr_ci_upper": spatial_row["pr_auc_ci_high"],
            "paired_individual_bootstrap_used": False,
            "interpretation": "matched-support spatial distribution-shift sensitivity",
        })
    tables = PROJECT_ROOT / "outputs/phase2_6/tables"
    atomic_to_csv(pd.DataFrame(support_rows), tables / "matched_geo_support_population.csv")
    atomic_to_csv(pd.DataFrame(random_summaries), tables / "matched_random_split_summary.csv")
    atomic_to_csv(pd.DataFrame(spatial_summaries), tables / "matched_spatial_split_summary.csv")
    atomic_to_csv(pd.DataFrame(comparison_rows), tables / "matched_random_vs_spatial_results.csv")
    atomic_write_text(
        tables / "matched_spatial_overlap_check.json",
        json.dumps(overlap_payload, ensure_ascii=False, indent=2) + "\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
