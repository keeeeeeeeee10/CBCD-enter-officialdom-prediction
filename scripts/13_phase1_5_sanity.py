#!/usr/bin/env python3
"""Fail Phase 1.5 when a core database, Phase 1, or person-level invariant changes."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import configured_path, load_config
from src.db import connect_readonly, scalar
from src.utils import atomic_write_text, sha256_file


def parquet_rows(path: Path) -> int:
    return pq.ParquetFile(path).metadata.num_rows


def main() -> int:
    config = load_config()
    expected_people = int(config["phase1_5"]["expected_people"])
    expected_positive = int(config["phase1_5"]["expected_v1_positive"])
    interim = configured_path(config, "paths", "interim")
    processed = configured_path(config, "paths", "processed")
    tables = configured_path(config, "paths", "tables")
    raw_dir = configured_path(config, "paths", "raw")
    manifest = json.loads((raw_dir / "download_manifest.json").read_text(encoding="utf-8"))
    raw_database = PROJECT_ROOT / "database" / manifest["sqlite_filename"]
    working_database = configured_path(config, "database", "working_db")

    phase1_target_path = interim / "person_target.parquet"
    phase1_base_path = processed / "person_base_v0.parquet"
    phase1_target = pd.read_parquet(phase1_target_path, columns=["person_id", "target_entry", "entry_record_count"])
    phase1_base = pd.read_parquet(phase1_base_path, columns=["person_id", "target_entry", "n_entry_records"])
    new_targets = pd.read_parquet(interim / "person_targets_v1_v2.parquet")
    auxiliary = pd.read_parquet(interim / "person_auxiliary_outcomes.parquet")

    checks: dict[str, object] = {
        "expected_people": expected_people,
        "phase1_target_rows": len(phase1_target),
        "phase1_base_rows": len(phase1_base),
        "phase1_v1_positive": int(phase1_target["target_entry"].sum()),
        "new_v1_positive": int(new_targets["target_entry_v1"].sum()),
        "raw_database_sha256_expected": manifest["sqlite_sha256"],
        "raw_database_sha256_observed": sha256_file(raw_database),
        "raw_database_views": None,
        "raw_database_has_addresses": None,
        "working_database_quick_check": None,
    }
    if len(phase1_target) != expected_people or len(phase1_base) != expected_people:
        raise RuntimeError("Phase 1 person-count invariant failed")
    if int(phase1_target["target_entry"].sum()) != expected_positive:
        raise RuntimeError("Phase 1 V1-positive invariant failed")
    if len(new_targets) != expected_people or int(new_targets["target_entry_v1"].sum()) != expected_positive:
        raise RuntimeError("Phase 1.5 V1 target does not reproduce Phase 1")
    if checks["raw_database_sha256_observed"] != checks["raw_database_sha256_expected"]:
        raise RuntimeError("Original database SHA256 changed")

    compared = phase1_target.merge(
        new_targets[["person_id", "target_entry_v1"]], on="person_id", how="outer", validate="one_to_one", indicator=True
    )
    target_mismatches = int((compared["_merge"] != "both").sum() + (compared["target_entry"] != compared["target_entry_v1"]).sum())
    base_compared = phase1_base.merge(auxiliary, on="person_id", how="outer", validate="one_to_one", indicator=True)
    base_target_mismatches = int((base_compared["_merge"] != "both").sum() + (base_compared["target_entry"] != base_compared["target_entry_v1"]).sum())
    count_mismatches = int((base_compared["n_entry_records_x"] != base_compared["n_entry_records_y"]).sum())
    checks.update({
        "phase1_to_phase1_5_target_mismatches": target_mismatches,
        "phase1_base_to_aux_target_mismatches": base_target_mismatches,
        "phase1_base_to_aux_entry_count_mismatches": count_mismatches,
    })
    if target_mismatches or base_target_mismatches or count_mismatches:
        raise RuntimeError(f"Phase 1 target preservation mismatch: {checks}")

    required_parquets = [
        "person_auxiliary_outcomes.parquet", "person_targets_v1_v2.parquet", "person_safe_time_anchor.parquet",
        "person_modeling_population.parquet", "person_split_assignments.parquet",
    ]
    for filename in required_parquets:
        rows = parquet_rows(interim / filename)
        checks[f"{filename}_rows"] = rows
        if rows != expected_people:
            raise RuntimeError(f"Person-level row invariant failed for {filename}: {rows}")
    timing_rows = parquet_rows(interim / "person_entry_timing.parquet")
    checks["person_entry_timing.parquet_rows"] = timing_rows
    if timing_rows != expected_positive:
        raise RuntimeError("ENTRY-positive timing row count does not match V1 positives")

    with sqlite3.connect(f"file:{raw_database.resolve().as_posix()}?mode=ro", uri=True) as connection:
        checks["raw_database_views"] = connection.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='view'").fetchone()[0]
        checks["raw_database_has_addresses"] = connection.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='ADDRESSES'").fetchone()[0]
    if checks["raw_database_views"] != 0 or checks["raw_database_has_addresses"] != 0:
        raise RuntimeError("Original database contains working-copy post-processing objects")
    with connect_readonly(working_database, config["database"]["busy_timeout_ms"]) as connection:
        checks["working_database_quick_check"] = scalar(connection, "PRAGMA quick_check")
    if checks["working_database_quick_check"] != "ok":
        raise RuntimeError("Working database quick_check failed")

    checks["status"] = "PASS"
    atomic_write_text(tables / "phase1_5_invariants.json", json.dumps(checks, ensure_ascii=False, indent=2) + "\n")
    print("=" * 60)
    print("CBDB Phase 1.5 Complete — all invariants PASS")
    print(f"People: {expected_people:,}; V1 positives: {expected_positive:,}")
    print(f"Original SQLite SHA256: PASS; working quick_check: {checks['working_database_quick_check']}")
    print("No formal model was trained.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
