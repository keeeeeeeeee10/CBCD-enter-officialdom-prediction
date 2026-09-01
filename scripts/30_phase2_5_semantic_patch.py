#!/usr/bin/env python3
"""Precheck frozen artifacts and validate the Phase 2.5 semantic patch."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import load_yaml
from src.phase25 import build_relation_edge_cache
from src.utils import atomic_write_text, setup_logging, sha256_file


ARTIFACTS = {
    "database": "database/cbdb_20260829.sqlite3",
    "working_database": "database/cbdb_working.sqlite3",
    "target": "data/interim/person_target.parquet",
    "base": "data/processed/person_base_v0.parquet",
    "phase2_master": "data/modeling/person_phase2_features.parquet",
    "primary": "data/splits/split_primary_dynasty_target.parquet",
    "random": "data/splits/split_random_benchmark.parquet",
    "family": "data/splits/split_family_group_robustness.parquet",
    "temporal": "data/splits/split_safe_temporal.parquet",
}


def phase2_manifest() -> dict[str, str]:
    roots = [PROJECT_ROOT / "outputs/phase2", PROJECT_ROOT / "docs/phase2"]
    files = sorted(path for root in roots for path in root.rglob("*") if path.is_file())
    return {str(path.relative_to(PROJECT_ROOT)): sha256_file(path) for path in files}


def main() -> int:
    logger = setup_logging("phase2_5_semantic", PROJECT_ROOT / "outputs/phase2_5/logs/semantic_patch.log")
    protocol = load_yaml("configs/phase2_5_protocol.yaml")
    expected = protocol["expected_sha256"]
    hashes = {key: sha256_file(PROJECT_ROOT / path) for key, path in ARTIFACTS.items()}
    for key in ["database", "target", "base", "primary", "random", "family", "temporal"]:
        if hashes[key] != expected[key]:
            raise RuntimeError(f"Frozen {key} SHA256 changed")
    with sqlite3.connect(f"file:{(PROJECT_ROOT / ARTIFACTS['working_database']).resolve().as_posix()}?mode=ro", uri=True) as connection:
        quick_check = connection.execute("PRAGMA quick_check").fetchone()[0]
    if quick_check != "ok":
        raise RuntimeError("Working database quick_check failed")

    preservation_path = PROJECT_ROOT / "outputs/phase2_5/tables/phase2_preservation_manifest.json"
    observed_phase2 = phase2_manifest()
    if preservation_path.exists():
        frozen_phase2 = json.loads(preservation_path.read_text(encoding="utf-8"))["files"]
        if observed_phase2 != frozen_phase2:
            raise RuntimeError("An existing Phase 2 output changed after the Phase 2.5 baseline snapshot")
    else:
        atomic_write_text(
            preservation_path,
            json.dumps({"status": "FROZEN", "files": observed_phase2}, ensure_ascii=False, indent=2) + "\n",
        )

    family_doc = (PROJECT_ROOT / "docs/audit/family_feature_protocol.md").read_text(encoding="utf-8")
    split_doc = (PROJECT_ROOT / "docs/audit/split_protocol.md").read_text(encoding="utf-8")
    if "Pre-birth Lineage Political Capital" not in family_doc or "Matched Pre-entry Family Capital" not in family_doc:
        raise RuntimeError("Pre-birth/matched pre-entry semantics are not explicit")
    required_split = [
        "Family group identifiers are constructed before family-aware split assignment.",
        "inductive relative-outcome features are fitted after the split is locked, using training data only.",
    ]
    if any(phrase not in split_doc for phrase in required_split):
        raise RuntimeError("Family split ordering semantic patch is incomplete")
    features = load_yaml("configs/phase2_5_features.yaml")
    predictor_text = json.dumps(features["feature_sets"])
    if "birth_year" in predictor_text.replace("safe_birth_year", "") or "safe_index_year" in predictor_text:
        raise RuntimeError("Unsafe/redundant birth/index fields entered Phase 2.5 models")
    edge_count = len(build_relation_edge_cache())
    result = {
        "status": "PASS",
        "frozen_hashes": hashes,
        "working_db_quick_check": quick_check,
        "phase2_preserved_file_count": len(observed_phase2),
        "prebirth_definition": "relative event year < focal safe_birth_year",
        "matched_pre_entry_implemented": False,
        "older_relation_edge_count": edge_count,
    }
    atomic_write_text(
        PROJECT_ROOT / "outputs/phase2_5/tables/semantic_patch.json",
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
    )
    logger.info("Phase 2.5 semantic/frozen precheck PASS; older relation edges=%d", edge_count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
