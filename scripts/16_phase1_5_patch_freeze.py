#!/usr/bin/env python3
"""Validate all patch invariants and freeze the data foundation for Phase 2."""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import configured_path, load_config
from src.db import connect_readonly, scalar
from src.feature_policy import FeaturePolicyError, validate_feature_set
from src.utils import atomic_write_text, sha256_file


def parquet_rows(path: Path) -> int:
    return pq.ParquetFile(path).metadata.num_rows


def must_fail(features: list[str], track: str) -> None:
    try:
        validate_feature_set(features, track)
    except FeaturePolicyError:
        return
    raise RuntimeError(f"Feature policy unexpectedly allowed {features} in {track}")


def main() -> int:
    config = load_config()
    expected_people = int(config["phase1_5"]["expected_people"])
    expected_positive = int(config["phase1_5"]["expected_v1_positive"])
    expected = config["phase1_5_patch"]
    interim = configured_path(config, "paths", "interim")
    processed = configured_path(config, "paths", "processed")
    tables = configured_path(config, "paths", "tables")
    splits = configured_path(config, "paths", "splits")
    raw_dir = configured_path(config, "paths", "raw")
    working_database = configured_path(config, "database", "working_db")
    download_manifest = json.loads((raw_dir / "download_manifest.json").read_text(encoding="utf-8"))
    raw_database = PROJECT_ROOT / "database" / download_manifest["sqlite_filename"]
    target_path = interim / "person_target.parquet"
    base_path = processed / "person_base_v0.parquet"

    target = pd.read_parquet(target_path, columns=["person_id", "target_entry"])
    checks: dict[str, object] = {
        "n_people": len(target),
        "v1_positive": int(target["target_entry"].sum()),
        "raw_database_sha256": sha256_file(raw_database),
        "person_target_sha256": sha256_file(target_path),
        "person_base_sha256": sha256_file(base_path),
    }
    if checks["n_people"] != expected_people or checks["v1_positive"] != expected_positive:
        raise RuntimeError(f"Person/target invariant failed: {checks}")
    for observed_key, expected_key in (
        ("raw_database_sha256", "raw_database_sha256"),
        ("person_target_sha256", "phase1_target_sha256"),
        ("person_base_sha256", "phase1_base_sha256"),
    ):
        if checks[observed_key] != expected[expected_key]:
            raise RuntimeError(f"Immutable SHA256 changed for {observed_key}")

    with sqlite3.connect(f"file:{raw_database.resolve().as_posix()}?mode=ro", uri=True) as connection:
        checks["raw_database_view_count"] = connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='view'"
        ).fetchone()[0]
        checks["raw_database_addresses_count"] = connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='ADDRESSES'"
        ).fetchone()[0]
    if checks["raw_database_view_count"] != 0 or checks["raw_database_addresses_count"] != 0:
        raise RuntimeError("Raw database contains working-copy objects")
    with connect_readonly(working_database, config["database"]["busy_timeout_ms"]) as connection:
        checks["working_database_quick_check"] = scalar(connection, "PRAGMA quick_check")
    if checks["working_database_quick_check"] != "ok":
        raise RuntimeError("Working database quick_check failed")

    must_fail(["dynasty", "raw_index_year"], "pre_entry")
    must_fail(["dynasty", "target_entry_v1"], "pre_entry")
    must_fail(["dynasty", "target_posting"], "pre_entry")
    must_fail(["has_kin", "documentation_intensity"], "historical_only")
    if not validate_feature_set(["dynasty", "gender", "safe_index_year"], "pre_entry"):
        raise RuntimeError("SAFE feature policy validation did not pass")
    checks["feature_policy_invariants"] = {
        "raw_index_year_forbidden_pre_entry": True,
        "target_forbidden": True,
        "posting_outcome_forbidden_pre_entry": True,
        "documentation_separated": True,
        "safe_index_year_allowed_pre_entry": True,
    }

    split_manifest_path = splits / "split_manifest.json"
    split_manifest = json.loads(split_manifest_path.read_text(encoding="utf-8"))
    for key, details in split_manifest["splits"].items():
        path = PROJECT_ROOT / details["file"]
        if parquet_rows(path) != expected_people:
            raise RuntimeError(f"Frozen split row count failed: {key}")
        frame = pd.read_parquet(path)
        if frame["person_id"].duplicated().any() or frame["split"].isna().any():
            raise RuntimeError(f"Frozen split key invariant failed: {key}")
        if sha256_file(path) != details["sha256"]:
            raise RuntimeError(f"Frozen split hash differs from split manifest: {key}")

    overlap_path = tables / "family_split_overlap_check.json"
    overlap = json.loads(overlap_path.read_text(encoding="utf-8"))
    if overlap.get("status") != "PASS" or not overlap.get("all_pairwise_group_intersections_zero"):
        raise RuntimeError("Family split overlap check is not PASS")
    if any(overlap.get("group_overlap_counts", {}).values()):
        raise RuntimeError("Family split contains a nonzero group overlap")
    checks["family_split_group_overlap"] = 0

    family_edges = pd.read_parquet(
        interim / "family_edges_core.parquet",
        columns=["person_id", "kin_id", "canonical_pair_id", "canonical_relation_class", "is_blood_core", "is_affinal"],
    )
    if family_edges[["person_id", "kin_id"]].isna().any().any():
        raise RuntimeError("Family edge contains a missing endpoint")
    if (family_edges[["person_id", "kin_id"]] <= 0).any().any():
        raise RuntimeError("Family edge contains a sentinel/nonpositive endpoint")
    if family_edges["person_id"].eq(family_edges["kin_id"]).any():
        raise RuntimeError("Family edge contains a self-loop")
    if family_edges["canonical_pair_id"].duplicated().any():
        raise RuntimeError("Family edge reciprocal/canonical pair duplicate remains")
    if family_edges.loc[family_edges["is_blood_core"], "is_affinal"].any():
        raise RuntimeError("Core family edge is affinal")

    family_groups = pd.read_parquet(interim / "person_family_groups.parquet")
    if len(family_groups) != expected_people or family_groups["person_id"].duplicated().any():
        raise RuntimeError("Person family groups do not cover the modeling population one-to-one")
    component_summary = pd.read_csv(tables / "family_component_summary.csv").iloc[0]
    if bool(component_summary["giant_component_warning"]):
        raise RuntimeError("A giant family component prevents automatic foundation freezing")

    target_comparison = pd.read_csv(tables / "target_definition_comparison.csv")
    expected_names = {
        "V1": "ENTRY record presence",
        "V2a": "Broad formal entry/credential target",
        "V2b": "High-confidence formal entry/credential target",
        "posting": "Recorded office-holding / posting outcome",
    }
    observed_names = dict(zip(target_comparison["target_key"], target_comparison["display_name"], strict=True))
    if observed_names != expected_names:
        raise RuntimeError(f"Target display semantics are not frozen: {observed_names}")

    feature_policy_path = PROJECT_ROOT / "configs/feature_policy.yaml"
    feature_registry_path = PROJECT_ROOT / "configs/feature_registry.yaml"
    primary = split_manifest["splits"]["primary_dynasty_target"]
    family = split_manifest["splits"]["family_group_robustness"]
    temporal = split_manifest["splits"]["safe_temporal"]
    freeze_manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "database_version": raw_database.name,
        "database_sha256": checks["raw_database_sha256"],
        "person_target_sha256": checks["person_target_sha256"],
        "person_base_sha256": checks["person_base_sha256"],
        "person_count": expected_people,
        "V1_definition": "ENTRY record presence",
        "V1_positive_count": expected_positive,
        "V2a_semantic_name": "Broad formal entry/credential target",
        "V2b_semantic_name": "High-confidence formal entry/credential target",
        "posting_semantic_name": "Recorded office-holding / posting outcome",
        "raw_index_year_allowed": False,
        "safe_index_year_allowed": True,
        "primary_split_sha256": primary["sha256"],
        "family_split_sha256": family["sha256"],
        "temporal_split_sha256": temporal["sha256"],
        "feature_policy_sha256": sha256_file(feature_policy_path),
        "feature_registry_sha256": sha256_file(feature_registry_path),
        "canonical_family_edge_count": int(len(family_edges)),
        "family_edge_count": int(family_edges["is_blood_core"].sum()),
        "family_group_count": int(family_groups["family_group_id"].nunique()),
        "largest_family_component": int(component_summary["largest_component_size"]),
        "family_split_group_overlap": 0,
        "working_database_quick_check": checks["working_database_quick_check"],
        "formal_model_trained": False,
        "status": "DATA_FOUNDATION_FROZEN_FOR_PHASE2",
    }
    checks["status"] = "PASS"
    atomic_write_text(
        tables / "phase1_5_patch_invariants.json",
        json.dumps(checks, ensure_ascii=False, indent=2) + "\n",
    )
    atomic_write_text(
        tables / "data_foundation_freeze_manifest.json",
        json.dumps(freeze_manifest, ensure_ascii=False, indent=2) + "\n",
    )
    print("=========================================")
    print("DATA FOUNDATION FROZEN FOR PHASE 2")
    print("=========================================")
    print(f"People: {expected_people:,}; V1 positives: {expected_positive:,}")
    print("Raw/Phase 1 hashes: PASS; working quick_check: ok")
    print("Feature policy and family-group overlap invariants: PASS")
    print("No formal model was trained.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
