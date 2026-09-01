#!/usr/bin/env python3
"""Create Phase 2.6 directories and fail closed on all frozen artifacts."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import load_yaml
from src.phase26 import validate_locked_feature_sets
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


def tree_manifest(roots: list[Path]) -> dict[str, str]:
    return {
        str(path.relative_to(PROJECT_ROOT)): sha256_file(path)
        for root in roots for path in sorted(root.rglob("*")) if path.is_file()
    }


def main() -> int:
    for directory in [
        "outputs/phase2_6/tables", "outputs/phase2_6/figures", "outputs/phase2_6/models",
        "outputs/phase2_6/shap", "outputs/phase2_6/logs", "docs/phase2_6/model_cards",
        "data/phase2_6/predictions", "data/phase2_6/shap_samples", "data/phase2_6/splits",
    ]:
        (PROJECT_ROOT / directory).mkdir(parents=True, exist_ok=True)
    logger = setup_logging("phase2_6_semantic", PROJECT_ROOT / "outputs/phase2_6/logs/semantic_patch.log")
    phase25_protocol = load_yaml("configs/phase2_5_protocol.yaml")
    expected = phase25_protocol["expected_sha256"]
    hashes = {key: sha256_file(PROJECT_ROOT / path) for key, path in ARTIFACTS.items()}
    for key in ["database", "target", "base", "primary", "random", "family", "temporal"]:
        if hashes[key] != expected[key]:
            raise RuntimeError(f"Frozen {key} SHA256 changed before Phase 2.6")
    phase25_semantic = json.loads(
        (PROJECT_ROOT / "outputs/phase2_5/tables/semantic_patch.json").read_text(encoding="utf-8")
    )
    for key in ["working_database", "phase2_master"]:
        if hashes[key] != phase25_semantic["frozen_hashes"][key]:
            raise RuntimeError(f"Frozen {key} SHA256 changed before Phase 2.6")
    with sqlite3.connect(
        f"file:{(PROJECT_ROOT / ARTIFACTS['working_database']).resolve().as_posix()}?mode=ro", uri=True
    ) as connection:
        quick_check = connection.execute("PRAGMA quick_check").fetchone()[0]
    if quick_check != "ok":
        raise RuntimeError("Working database PRAGMA quick_check failed")

    phase2_current = tree_manifest([PROJECT_ROOT / "outputs/phase2", PROJECT_ROOT / "docs/phase2"])
    phase2_frozen = json.loads(
        (PROJECT_ROOT / "outputs/phase2_5/tables/phase2_preservation_manifest.json").read_text(encoding="utf-8")
    )["files"]
    if phase2_current != phase2_frozen:
        raise RuntimeError("Phase 2 outputs changed before Phase 2.6")
    phase25_current = tree_manifest([PROJECT_ROOT / "outputs/phase2_5", PROJECT_ROOT / "docs/phase2_5"])
    preservation_path = PROJECT_ROOT / "outputs/phase2_6/tables/phase2_5_preservation_manifest.json"
    if preservation_path.exists():
        phase25_frozen = json.loads(preservation_path.read_text(encoding="utf-8"))["files"]
        if phase25_current != phase25_frozen:
            raise RuntimeError("Phase 2.5 outputs changed after Phase 2.6 baseline snapshot")
    else:
        atomic_write_text(
            preservation_path,
            json.dumps({"status": "FROZEN", "files": phase25_current}, indent=2) + "\n",
        )

    registry_text = (PROJECT_ROOT / "configs/feature_registry.yaml").read_text(encoding="utf-8")
    address_policy = (PROJECT_ROOT / "docs/phase2_6/address_feature_policy.md").read_text(encoding="utf-8")
    if "address_record_semantics" not in registry_text or "not treated as pure geography" not in address_policy:
        raise RuntimeError("Address-record semantic separation is incomplete")
    resolved = validate_locked_feature_sets()
    result = {
        "status": "PASS",
        "frozen_hashes": hashes,
        "working_db_quick_check": quick_check,
        "phase2_preserved_files": len(phase2_current),
        "phase2_5_preserved_files": len(phase25_current),
        "locked_feature_counts": {key: len(value["features"]) for key, value in resolved.items()},
        "birth_missingness_interpretation": "An explicit missing indicator may be redundant when the model already recognizes missing values.",
        "addr_type_feature_group": "address_record_semantics",
    }
    atomic_write_text(
        PROJECT_ROOT / "outputs/phase2_6/tables/semantic_patch.json",
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
    )
    logger.info(
        "Phase 2.6 precheck PASS: Phase2=%d files Phase2.5=%d files quick_check=%s",
        len(phase2_current), len(phase25_current), quick_check,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
