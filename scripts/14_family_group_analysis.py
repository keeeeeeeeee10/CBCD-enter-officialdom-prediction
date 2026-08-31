#!/usr/bin/env python3
"""Build stable core blood-family components without marital/affinal propagation."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import configured_path, load_config
from src.utils import setup_logging


class UnionFind:
    def __init__(self, identifiers: np.ndarray) -> None:
        self.parent = np.arange(len(identifiers), dtype=np.int64)
        self.size = np.ones(len(identifiers), dtype=np.int64)
        self.minimum = identifiers.astype(np.int64, copy=True)

    def find(self, value: int) -> int:
        parent = self.parent
        root = value
        while parent[root] != root:
            root = int(parent[root])
        while parent[value] != value:
            next_value = int(parent[value])
            parent[value] = root
            value = next_value
        return root

    def union(self, left: int, right: int) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return
        if self.size[left_root] < self.size[right_root]:
            left_root, right_root = right_root, left_root
        self.parent[right_root] = left_root
        self.size[left_root] += self.size[right_root]
        self.minimum[left_root] = min(self.minimum[left_root], self.minimum[right_root])


def atomic_to_csv(frame: pd.DataFrame, path: Path) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, path)


def quantile_higher(values: pd.Series, probability: float) -> int:
    return int(values.quantile(probability, interpolation="higher"))


def main() -> int:
    config = load_config()
    interim = configured_path(config, "paths", "interim")
    tables = configured_path(config, "paths", "tables")
    logger = setup_logging(
        "family_group_analysis",
        configured_path(config, "paths", "logs") / "family_group_analysis.log",
    )

    population = pd.read_parquet(
        interim / "person_modeling_population.parquet",
        columns=["person_id", "dynasty", "target_entry_v1"],
    ).sort_values("person_id").reset_index(drop=True)
    if population["person_id"].duplicated().any():
        raise RuntimeError("Modeling population person_id is not unique")
    identifiers = population["person_id"].astype("int64").to_numpy()
    index = pd.Index(identifiers)
    edges = pd.read_parquet(
        interim / "family_edges_core.parquet",
        columns=["person_id", "kin_id", "canonical_pair_id", "is_blood_core", "is_affinal"],
    )
    core = edges[edges["is_blood_core"].eq(True)].drop_duplicates("canonical_pair_id").copy()
    if core["is_affinal"].any():
        raise RuntimeError("Core blood-family graph contains affinal edges")
    left = index.get_indexer(core["person_id"].astype("int64"))
    right = index.get_indexer(core["kin_id"].astype("int64"))
    if (left < 0).any() or (right < 0).any():
        raise RuntimeError("Core family graph contains people outside BIOG_MAIN")

    components = UnionFind(identifiers)
    for left_index, right_index in zip(left, right, strict=True):
        components.union(int(left_index), int(right_index))
    roots = np.fromiter((components.find(i) for i in range(len(identifiers))), dtype=np.int64)
    group_ids = np.fromiter((components.minimum[root] for root in roots), dtype=np.int64)
    groups = pd.DataFrame({"person_id": identifiers, "family_group_id": group_ids})
    sizes = groups.groupby("family_group_id").size().rename("family_group_size")
    groups = groups.merge(sizes, on="family_group_id", how="left", validate="many_to_one")
    groups["has_core_family"] = groups["family_group_size"].gt(1)
    groups.to_parquet(interim / "person_family_groups.parquet", index=False, compression="zstd")

    n_people = len(groups)
    n_components = len(sizes)
    largest = int(sizes.max())
    warning_fraction = float(config["phase1_5_patch"]["giant_component_warning_fraction"])
    giant_fraction = largest / n_people
    summary = pd.DataFrame([{
        "n_people": n_people,
        "n_core_edges": len(core),
        "n_components": n_components,
        "largest_component_size": largest,
        "largest_component_fraction": giant_fraction,
        "median_component_size": float(sizes.median()),
        "p90_component_size": quantile_higher(sizes, 0.90),
        "p95_component_size": quantile_higher(sizes, 0.95),
        "p99_component_size": quantile_higher(sizes, 0.99),
        "singletons": int(sizes.eq(1).sum()),
        "components_gt_10": int(sizes.gt(10).sum()),
        "components_gt_50": int(sizes.gt(50).sum()),
        "components_gt_100": int(sizes.gt(100).sum()),
        "giant_component_threshold": warning_fraction,
        "giant_component_warning": bool(giant_fraction > warning_fraction),
    }])
    atomic_to_csv(summary, tables / "family_component_summary.csv")

    enriched = groups.merge(population, on="person_id", how="left", validate="one_to_one")
    top_ids = sizes.sort_values(ascending=False, kind="mergesort").head(20).index
    top = enriched[enriched["family_group_id"].isin(top_ids)].groupby("family_group_id").agg(
        family_group_size=("person_id", "size"),
        entry_v1_positive=("target_entry_v1", "sum"),
        entry_v1_rate=("target_entry_v1", "mean"),
        modal_dynasty=("dynasty", lambda values: values.value_counts(dropna=False).index[0]),
    ).reset_index().sort_values(
        ["family_group_size", "family_group_id"], ascending=[False, True], kind="mergesort"
    )
    top.insert(0, "rank", np.arange(1, len(top) + 1))
    atomic_to_csv(top, tables / "family_component_top20.csv")

    if giant_fraction > warning_fraction:
        logger.warning(
            "GIANT COMPONENT: largest group %d is %.2f%% of the modeling population; do not use automatically for group split",
            largest, giant_fraction * 100,
        )
    else:
        logger.info(
            "Core graph accepted for robustness grouping: components=%d singletons=%d largest=%d (%.4f%%)",
            n_components, int(sizes.eq(1).sum()), largest, giant_fraction * 100,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
