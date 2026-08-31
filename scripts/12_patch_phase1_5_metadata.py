#!/usr/bin/env python3
"""Apply idempotent Phase 1.5 metadata fixes without changing target values."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import configured_path, load_config
from src.utils import setup_logging


TARGET_DISPLAY = {
    "V1": (
        "ENTRY record presence",
        "是否存在 ENTRY_DATA 记录",
        "Presence of at least one current CBDB ENTRY_DATA record; not proof of office holding.",
    ),
    "V2a": (
        "Broad formal entry/credential target",
        "广义正式入仕途径/资格记录",
        "Broad taxonomy-based formal entry route or credential candidate.",
    ),
    "V2b": (
        "High-confidence formal entry/credential target",
        "高置信度正式入仕途径/资格记录",
        "High-confidence formal entry route or credential candidate; not equivalent to a posting.",
    ),
    "posting": (
        "Recorded office-holding / posting outcome",
        "是否存在任官记录",
        "Auxiliary presence of a valid CBDB posting record; incomplete and not ground truth.",
    ),
}


def atomic_to_csv(frame: pd.DataFrame, path: Path) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, path)


def patch_leakage_table(project_root: Path, output: Path) -> None:
    archived = project_root / "outputs/archive/pre_phase15_patch/feature_leakage_classification.csv"
    base = pd.read_csv(archived)
    combined = base["feature_group"].eq("gender / birth year / index year / dynasty")
    if int(combined.sum()) != 1:
        raise RuntimeError("Archived leakage table does not contain the expected combined BIOG_MAIN row")
    base = base.loc[~combined].copy()
    class_by_level = {0: "DIRECT_TARGET", 1: "UNSAFE", 2: "CONDITIONAL", 3: "SAFE_OR_CONDITIONAL"}
    base["leakage_class"] = base["leakage_level"].map(class_by_level)
    reason_raw = (
        "Some index years are algorithmically derived from ENTRY_DATA, examination years, "
        "death years, relatives or later-life events. Raw index year therefore mixes safe "
        "and unsafe provenance and cannot be used directly."
    )
    replacements = [
        ("gender", 3, "SAFE", "Substantive personal background field; retain unknown as missing.", True),
        ("birth_year", 3, "SAFE", "Allowed only after field-aware sentinel/range validation.", True),
        ("dynasty", 3, "SAFE_BACKGROUND_REGIME", "Historical regime baseline; preserve missing/unknown category.", True),
        ("raw_index_year", 1, "UNSAFE_AS_RAW_FEATURE", reason_raw + " Never use directly in a leakage-controlled / pre-entry model.", False),
        ("safe_index_year", 3, "SAFE", "Only provenance 01 (Based on Birth Year), after year validation.", True),
        ("conditional_index_year", 2, "CONDITIONAL", "Kin/recursive provenance without explicit outcome evidence; sensitivity analysis only.", "sensitivity_only"),
        ("unsafe_index_year", 1, "UNSAFE", "Derived from ENTRY/examination, death, descendants, or other later-life information.", False),
        ("unknown_index_year", 1, "UNKNOWN", "Unknown/unparsed provenance is never promoted to SAFE.", False),
    ]
    rows = []
    for feature, level, leakage_class, reason, allowed in replacements:
        rows.append({
            "table": "BIOG_MAIN" if feature != "safe_index_year" else "person_safe_time_anchor",
            "feature_group": feature,
            "leakage_level": level,
            "reason": reason,
            "allowed_full_model": True,
            "allowed_pre_entry_model": allowed,
            "leakage_class": leakage_class,
        })
    patched = pd.concat([base, pd.DataFrame(rows)], ignore_index=True)
    atomic_to_csv(patched, output)


def patch_target_tables(tables: Path) -> None:
    comparison_path = tables / "target_definition_comparison.csv"
    comparison = pd.read_csv(comparison_path)
    if "target_key" in comparison.columns:
        keys = comparison["target_key"].astype(str).tolist()
    else:
        keys = []
        for label in comparison["target"].astype(str):
            lower = label.lower()
            keys.append("V2a" if "v2a" in lower else "V2b" if "v2b" in lower else "posting" if "posting" in lower else "V1")
    comparison["target_key"] = keys
    comparison["display_name"] = [TARGET_DISPLAY[key][0] for key in keys]
    comparison["display_name_zh"] = [TARGET_DISPLAY[key][1] for key in keys]
    comparison["description"] = [TARGET_DISPLAY[key][2] for key in keys]
    comparison["target"] = comparison["display_name"]
    leading = ["target_key", "target", "display_name", "display_name_zh", "description"]
    comparison = comparison[leading + [column for column in comparison.columns if column not in leading]]
    atomic_to_csv(comparison, comparison_path)

    codes_path = tables / "target_v2_candidate_codes.csv"
    codes = pd.read_csv(codes_path)
    codes["target_v2a_semantic_name"] = TARGET_DISPLAY["V2a"][0]
    codes["target_v2b_semantic_name"] = TARGET_DISPLAY["V2b"][0]
    atomic_to_csv(codes, codes_path)


def validate_docs(audit_dir: Path) -> None:
    requirements = {
        "leakage_audit.md": ["Never use directly", "safe_index_year", "unknown_index_year"],
        "entry_code_taxonomy.md": ["High-confidence formal entry/credential target", "not ground-truth"],
        "target_definition.md": ["POSTING_DATA", "not treated as ground-truth"],
        "split_protocol.md": ["Global chronological distribution-shift sensitivity", "Within-dynasty temporal"],
    }
    for filename, phrases in requirements.items():
        text = (audit_dir / filename).read_text(encoding="utf-8")
        missing = [phrase for phrase in phrases if phrase not in text]
        if missing:
            raise RuntimeError(f"{filename} is missing frozen policy text: {missing}")


def main() -> int:
    config = load_config()
    tables = configured_path(config, "paths", "tables")
    audit_dir = configured_path(config, "paths", "audit_docs")
    logger = setup_logging(
        "phase15_patch_metadata",
        configured_path(config, "paths", "logs") / "phase1_5_patch_metadata.log",
    )
    patch_leakage_table(PROJECT_ROOT, tables / "feature_leakage_classification.csv")
    patch_target_tables(tables)
    validate_docs(audit_dir)
    logger.info("Leakage and target display metadata patched; target values were not changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
