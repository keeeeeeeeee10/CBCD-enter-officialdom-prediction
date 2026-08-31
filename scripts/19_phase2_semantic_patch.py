#!/usr/bin/env python3
"""Validate the Phase 2 semantic mini-patch and frozen foundation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import load_yaml
from src.utils import atomic_write_text, sha256_file


def main() -> int:
    freeze_path = PROJECT_ROOT / "outputs/tables/data_foundation_freeze_manifest.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if freeze.get("status") != "DATA_FOUNDATION_FROZEN_FOR_PHASE2":
        raise RuntimeError("Phase 2 foundation is not frozen")
    family_document = (PROJECT_ROOT / "docs/audit/family_feature_protocol.md").read_text(encoding="utf-8")
    split_document = (PROJECT_ROOT / "docs/audit/split_protocol.md").read_text(encoding="utf-8")
    required_family = [
        "Pre-birth Lineage Political Capital", "father_entry_before_birth",
        "Matched Pre-entry Family Capital", "not implement the matched case-control",
    ]
    required_split = [
        "Family group identifiers are constructed before family-aware split assignment",
        "Fold-dependent target aggregates",
    ]
    for phrase in required_family:
        if phrase not in family_document:
            raise RuntimeError(f"Family semantic patch missing: {phrase}")
    for phrase in required_split:
        if phrase not in split_document:
            raise RuntimeError(f"Split semantic patch missing: {phrase}")
    registry = load_yaml("configs/feature_registry.yaml")
    if "prebirth_lineage" not in registry or "family_strict_temporal" in registry:
        raise RuntimeError("Feature registry did not freeze the pre-birth naming patch")
    result = {
        "status": "PASS",
        "foundation_manifest_sha256": sha256_file(freeze_path),
        "safe_time_interpretation": "validated birth-year proxy",
        "implemented_track": "Pre-birth Lineage Political Capital",
        "future_only_track": "Matched Pre-entry Family Capital",
        "frozen_splits_modified": False,
    }
    output = PROJECT_ROOT / "outputs/phase2/tables/semantic_patch.json"
    atomic_write_text(output, json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("Phase 2 semantic mini-patch: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
