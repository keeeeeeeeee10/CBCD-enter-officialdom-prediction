#!/usr/bin/env python3
"""Construct deterministic dynasty-prefecture group holdout robustness splits."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import atomic_to_csv, atomic_to_parquet
from src.phase25 import load_phase25_dataset
from src.utils import atomic_write_text, setup_logging


PARTITIONS = ["train", "validation", "test"]
FRACTIONS = {"train": 0.70, "validation": 0.15, "test": 0.15}


def stable_tie(value: object, seed: int = 42) -> int:
    return int.from_bytes(hashlib.sha256(f"{seed}|{value}".encode()).digest()[:8], "little")


def assign_groups(groups: pd.DataFrame) -> pd.DataFrame:
    assigned = []
    for dynasty_code, block in groups.groupby("dynasty_code", dropna=False, sort=True):
        total_n = float(block["n_people"].sum())
        total_positive = float(block["n_positive"].sum())
        state = {partition: {"n": 0.0, "positive": 0.0} for partition in PARTITIONS}
        ordered = block.assign(tie=block["spatial_group_id"].map(stable_tie)).sort_values(
            ["n_people", "tie"], ascending=[False, True], kind="mergesort"
        )
        for row in ordered.itertuples():
            scores = {}
            for partition in PARTITIONS:
                target_n = max(FRACTIONS[partition] * total_n, 1.0)
                target_positive = max(FRACTIONS[partition] * total_positive, 1.0)
                projected_n = state[partition]["n"] + row.n_people
                projected_positive = state[partition]["positive"] + row.n_positive
                score = projected_n / target_n + projected_positive / target_positive
                if projected_n > target_n:
                    score += 2.0 * (projected_n - target_n) / target_n
                scores[partition] = score
            partition = min(PARTITIONS, key=lambda name: (scores[name], PARTITIONS.index(name)))
            state[partition]["n"] += row.n_people
            state[partition]["positive"] += row.n_positive
            assigned.append({
                "spatial_group_id": row.spatial_group_id,
                "dynasty_code": dynasty_code,
                "split": partition,
                "n_people": int(row.n_people),
                "n_positive": int(row.n_positive),
            })
    return pd.DataFrame(assigned)


def main() -> int:
    logger = setup_logging("phase2_5_spatial_split", PROJECT_ROOT / "outputs/phase2_5/logs/spatial_split.log")
    dataset = load_phase25_dataset()
    all_groups = []
    summaries = []
    overlaps: dict[str, object] = {}
    for population in ["Global", "Song", "Ming"]:
        eligible = dataset.loc[dataset["spatial_group_id"].notna()].copy()
        if population != "Global":
            eligible = eligible.loc[eligible["dynasty_name"].eq(population)].copy()
        groups = eligible.groupby(["spatial_group_id", "dynasty_code"], dropna=False).agg(
            n_people=("person_id", "size"), n_positive=("target_entry_v1", "sum")
        ).reset_index()
        assignment = assign_groups(groups)
        split = eligible[["person_id", "spatial_group_id"]].merge(
            assignment[["spatial_group_id", "split"]], on="spatial_group_id", how="left", validate="many_to_one"
        ).sort_values("person_id").reset_index(drop=True)
        if split["split"].isna().any() or split["person_id"].duplicated().any():
            raise RuntimeError(f"Invalid spatial split keys for {population}")
        group_sets = {
            partition: set(split.loc[split["split"].eq(partition), "spatial_group_id"])
            for partition in PARTITIONS
        }
        intersections = {
            "train_validation": len(group_sets["train"] & group_sets["validation"]),
            "train_test": len(group_sets["train"] & group_sets["test"]),
            "validation_test": len(group_sets["validation"] & group_sets["test"]),
        }
        if any(intersections.values()):
            raise RuntimeError(f"Spatial group overlap for {population}: {intersections}")
        overlaps[population] = {
            "eligible_people": len(split),
            "spatial_groups": split["spatial_group_id"].nunique(),
            "intersections": intersections,
            "status": "PASS",
        }
        atomic_to_parquet(
            split,
            PROJECT_ROOT / f"data/phase2_5/splits/split_spatial_group_{population.lower()}.parquet",
        )
        assignment.insert(0, "population", population)
        all_groups.append(assignment)
        for partition, block in split.merge(
            eligible[["person_id", "target_entry_v1", "dynasty_name"]], on="person_id", validate="one_to_one"
        ).groupby("split"):
            summaries.append({
                "population": population,
                "split": partition,
                "n_people": len(block),
                "fraction": len(block) / len(split),
                "n_positive": int(block["target_entry_v1"].sum()),
                "positive_rate": float(block["target_entry_v1"].mean()),
                "n_spatial_groups": int(block["spatial_group_id"].nunique()),
            })
        logger.info("Spatial %s: people=%d groups=%d overlap=0", population, len(split), split["spatial_group_id"].nunique())
    group_frame = pd.concat(all_groups, ignore_index=True)
    atomic_to_csv(group_frame, PROJECT_ROOT / "outputs/phase2_5/tables/spatial_group_summary.csv")
    atomic_to_csv(pd.DataFrame(summaries), PROJECT_ROOT / "outputs/phase2_5/tables/spatial_split_summary.csv")
    atomic_write_text(
        PROJECT_ROOT / "outputs/phase2_5/tables/spatial_split_overlap_check.json",
        json.dumps({"status": "PASS", "populations": overlaps}, ensure_ascii=False, indent=2) + "\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
