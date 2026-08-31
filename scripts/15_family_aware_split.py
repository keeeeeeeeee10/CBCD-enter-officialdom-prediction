#!/usr/bin/env python3
"""Freeze existing splits and add a deterministic family-group robustness split."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import configured_path, load_config
from src.utils import atomic_write_text, setup_logging, sha256_file


MAJOR_DYNASTIES = {"Tang", "Song", "Yuan", "Ming", "Qing"}
SPLIT_NAMES = np.array(["train", "validation", "test"], dtype=object)


def atomic_to_csv(frame: pd.DataFrame, path: Path) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, path)


def greedy_group_assignment(
    population: pd.DataFrame,
    fractions: np.ndarray,
    seed: int,
) -> dict[int, str]:
    work = population[["family_group_id", "dynasty_bucket", "target_entry_v1"]].copy()
    work["stratum"] = work["dynasty_bucket"].astype(str) + "|" + work["target_entry_v1"].astype(str)
    vectors = pd.crosstab(work["family_group_id"], work["stratum"]).sort_index()
    all_strata = [f"{dynasty}|{target}" for dynasty in ["Tang", "Song", "Yuan", "Ming", "Qing", "Other"] for target in [0, 1]]
    vectors = vectors.reindex(columns=all_strata, fill_value=0)
    matrix = vectors.to_numpy(dtype=np.float64)
    group_sizes = matrix.sum(axis=1)
    target = fractions[:, None] * matrix.sum(axis=0)[None, :]
    denominator = target + 1.0
    current = np.zeros_like(target)

    rng = np.random.default_rng(seed)
    tie_breaker = rng.random(len(vectors))
    order = np.lexsort((tie_breaker, -group_sizes))
    assignments = np.empty(len(vectors), dtype=np.int8)
    total_col = np.ones(matrix.shape[1], dtype=np.float64)
    total_target = fractions * group_sizes.sum()
    current_total = np.zeros(3, dtype=np.float64)

    for row_index in order:
        vector = matrix[row_index]
        deltas = np.empty(3, dtype=np.float64)
        for split_index in range(3):
            before = current[split_index] - target[split_index]
            after = before + vector
            stratum_delta = np.sum((after * after - before * before) / denominator[split_index])
            total_before = current_total[split_index] - total_target[split_index]
            total_after = total_before + group_sizes[row_index]
            total_delta = (total_after * total_after - total_before * total_before) / (total_target[split_index] + 1.0)
            deltas[split_index] = stratum_delta + 2.0 * total_delta
        best = int(np.argmin(deltas))
        assignments[row_index] = best
        current[best] += vector
        current_total[best] += group_sizes[row_index]

    return {
        int(group_id): str(SPLIT_NAMES[int(split_index)])
        for group_id, split_index in zip(vectors.index.to_numpy(), assignments, strict=True)
    }


def split_counts(frame: pd.DataFrame) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for split, subset in frame.groupby("split", sort=True):
        result[str(split)] = {
            "n_people": int(len(subset)),
            "positive_count": int(subset["target_entry_v1"].sum()),
            "positive_rate": float(subset["target_entry_v1"].mean()) if len(subset) else None,
        }
    return result


def save_split(frame: pd.DataFrame, path: Path) -> str:
    output = frame[["person_id", "split"]].sort_values("person_id").reset_index(drop=True)
    if output["person_id"].duplicated().any() or output["split"].isna().any():
        raise RuntimeError(f"Invalid split output: {path}")
    output.to_parquet(path, index=False, compression="zstd")
    return sha256_file(path)


def main() -> int:
    config = load_config()
    interim = configured_path(config, "paths", "interim")
    tables = configured_path(config, "paths", "tables")
    splits_dir = configured_path(config, "paths", "splits")
    splits_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(
        "family_aware_split",
        configured_path(config, "paths", "logs") / "family_aware_split.log",
    )
    component_summary = pd.read_csv(tables / "family_component_summary.csv").iloc[0]
    if bool(component_summary["giant_component_warning"]):
        raise RuntimeError(
            "Core-family giant component exceeds 5%; family grouping requires explicit review before splitting"
        )

    population = pd.read_parquet(
        interim / "person_modeling_population.parquet",
        columns=["person_id", "dynasty", "target_entry_v1"],
    )
    groups = pd.read_parquet(interim / "person_family_groups.parquet")
    existing = pd.read_parquet(interim / "person_split_assignments.parquet")
    population = population.merge(groups, on="person_id", how="left", validate="one_to_one")
    population = population.merge(existing, on="person_id", how="left", validate="one_to_one")
    if population["family_group_id"].isna().any():
        raise RuntimeError("Missing family group assignment")
    population["dynasty_bucket"] = population["dynasty"].where(
        population["dynasty"].isin(MAJOR_DYNASTIES), "Other"
    )

    settings = config["phase1_5"]
    fractions = np.array([
        float(settings["split_train_fraction"]),
        float(settings["split_validation_fraction"]),
        float(settings["split_test_fraction"]),
    ])
    if not np.isclose(fractions.sum(), 1.0):
        raise RuntimeError("Split fractions must sum to one")
    seed = int(config["seed"])
    group_to_split = greedy_group_assignment(population, fractions, seed)
    population["family_split"] = population["family_group_id"].map(group_to_split)
    if population["family_split"].isna().any():
        raise RuntimeError("Family split assignment is incomplete")

    group_sets = {
        split: set(population.loc[population["family_split"].eq(split), "family_group_id"].astype("int64"))
        for split in SPLIT_NAMES
    }
    overlaps = {
        "train_validation": len(group_sets["train"] & group_sets["validation"]),
        "train_test": len(group_sets["train"] & group_sets["test"]),
        "validation_test": len(group_sets["validation"] & group_sets["test"]),
    }
    if any(overlaps.values()):
        raise RuntimeError(f"Family group overlap detected: {overlaps}")
    overlap_document = {
        "status": "PASS",
        "group_overlap_counts": overlaps,
        "all_pairwise_group_intersections_zero": True,
        "grouping_rule": "core blood-family only; marriage, affinal, and distant kin excluded",
    }
    atomic_write_text(
        tables / "family_split_overlap_check.json",
        json.dumps(overlap_document, ensure_ascii=False, indent=2) + "\n",
    )

    summary_rows = []
    for split in SPLIT_NAMES:
        subset = population[population["family_split"].eq(split)]
        common = {
            "split": split,
            "n_people": len(subset),
            "entry_v1_positive": int(subset["target_entry_v1"].sum()),
            "positive_rate": float(subset["target_entry_v1"].mean()),
            "n_family_groups": int(subset["family_group_id"].nunique()),
            "largest_group": int(subset["family_group_size"].max()),
        }
        for dynasty in ["Global", "Tang", "Song", "Yuan", "Ming", "Qing", "Other"]:
            dynasty_subset = subset if dynasty == "Global" else subset[subset["dynasty_bucket"].eq(dynasty)]
            summary_rows.append({
                **common,
                "dynasty": dynasty,
                "dynasty_n": len(dynasty_subset),
                "dynasty_fraction": len(dynasty_subset) / len(subset),
                "dynasty_positive_rate": float(dynasty_subset["target_entry_v1"].mean()) if len(dynasty_subset) else None,
            })
    atomic_to_csv(pd.DataFrame(summary_rows), tables / "family_split_summary.csv")

    split_frames = {
        "primary_dynasty_target": population[["person_id", "target_entry_v1"]].assign(split=population["split_dynasty_stratified"]),
        "random_benchmark": population[["person_id", "target_entry_v1"]].assign(split=population["split_random_stratified"]),
        "family_group_robustness": population[["person_id", "target_entry_v1"]].assign(split=population["family_split"]),
        "safe_temporal": population[["person_id", "target_entry_v1"]].assign(split=population["split_temporal_safe"]),
    }
    filenames = {
        "primary_dynasty_target": "split_primary_dynasty_target.parquet",
        "random_benchmark": "split_random_benchmark.parquet",
        "family_group_robustness": "split_family_group_robustness.parquet",
        "safe_temporal": "split_safe_temporal.parquet",
    }
    algorithms = {
        "primary_dynasty_target": "exact deterministic shuffle within dynasty_code × target strata",
        "random_benchmark": "exact deterministic shuffle within target strata",
        "family_group_robustness": "deterministic greedy whole-group assignment balancing dynasty bucket × target",
        "safe_temporal": "whole-year global chronological sensitivity; <=1729 / <=1821 / >1821; others not_eligible",
    }
    stratification = {
        "primary_dynasty_target": ["dynasty_code", "target_entry_v1"],
        "random_benchmark": ["target_entry_v1"],
        "family_group_robustness": ["dynasty_bucket", "target_entry_v1"],
        "safe_temporal": ["safe_index_year"],
    }
    manifest_splits = {}
    for key, frame in split_frames.items():
        path = splits_dir / filenames[key]
        file_hash = save_split(frame, path)
        manifest_splits[key] = {
            "file": str(path.relative_to(PROJECT_ROOT)),
            "sha256": file_hash,
            "algorithm": algorithms[key],
            "stratification_keys": stratification[key],
            "grouping_rules": "family_group_id cannot cross partitions" if key == "family_group_robustness" else None,
            "counts": split_counts(frame),
        }
    target_path = interim / "person_target.parquet"
    manifest = {
        "seed": seed,
        "creation_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source_target_file": str(target_path.relative_to(PROJECT_ROOT)),
        "source_target_sha256": sha256_file(target_path),
        "person_count": int(len(population)),
        "positive_count": int(population["target_entry_v1"].sum()),
        "fractions": {"train": fractions[0], "validation": fractions[1], "test": fractions[2]},
        "splits": manifest_splits,
    }
    atomic_write_text(
        splits_dir / "split_manifest.json",
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    )
    logger.info(
        "Family-aware split PASS: train=%d validation=%d test=%d; group overlaps=0",
        *(len(population[population["family_split"].eq(split)]) for split in SPLIT_NAMES),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
