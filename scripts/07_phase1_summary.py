#!/usr/bin/env python3
"""Print and persist a concise summary from generated Phase 1 artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import configured_path, load_config
from src.db import connect_readonly, scalar
from src.utils import atomic_write_text, human_bytes, sha256_file


def main() -> int:
    config = load_config()
    tables = configured_path(config, "paths", "tables")
    processed = configured_path(config, "paths", "processed")
    schema = configured_path(config, "paths", "schema_docs")
    audit = configured_path(config, "paths", "audit_docs")
    figures = configured_path(config, "paths", "figures")
    raw = configured_path(config, "paths", "raw")
    inventory = pd.read_csv(tables / "database_inventory.csv")
    target = pd.read_csv(tables / "target_summary.csv").iloc[0]
    manifest = json.loads((raw / "download_manifest.json").read_text(encoding="utf-8"))
    raw_database = PROJECT_ROOT / "database" / manifest["sqlite_filename"]
    final_raw_sha256 = sha256_file(raw_database)
    if final_raw_sha256 != manifest["sqlite_sha256"]:
        raise RuntimeError(
            f"Post-pipeline raw database SHA256 mismatch: expected {manifest['sqlite_sha256']}, "
            f"observed {final_raw_sha256}"
        )
    working_database = configured_path(config, "database", "working_db")
    with connect_readonly(working_database, config["database"]["busy_timeout_ms"]) as connection:
        integrity_check = scalar(connection, "PRAGMA quick_check")
    if integrity_check != "ok":
        raise RuntimeError(f"Working database PRAGMA quick_check failed: {integrity_check}")

    summary = {
        "database": manifest["sqlite_filename"],
        "database_sha256": manifest["sqlite_sha256"],
        "sha256_status": manifest["sqlite_sha256_status"],
        "post_pipeline_raw_sha256": final_raw_sha256,
        "working_database_quick_check": integrity_check,
        "database_size_bytes": manifest["sqlite_size_bytes"],
        "tables": int((inventory["type"] == "table").sum()),
        "views": int((inventory["type"] == "view").sum()),
        "people": int(target["N_people"]),
        "entry_positive": int(target["N_positive"]),
        "entry_negative": int(target["N_negative"]),
        "positive_rate": float(target["positive_rate"]),
        "base_dataset": str((processed / "person_base_v0.parquet").relative_to(PROJECT_ROOT)),
        "schema_report": str((schema / "database_inventory.md").relative_to(PROJECT_ROOT)),
        "leakage_report": str((audit / "leakage_audit.md").relative_to(PROJECT_ROOT)),
        "figures": str(figures.relative_to(PROJECT_ROOT)),
    }
    atomic_write_text(tables / "phase1_summary.json", json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print("=" * 60)
    print("CBDB Phase 1 Complete")
    print("=" * 60)
    print(f"Database: {summary['database']} ({human_bytes(summary['database_size_bytes'])}; SHA256 {summary['sha256_status']})")
    print(f"Objects: {summary['tables']} tables, {summary['views']} views")
    print(f"People: {summary['people']:,}")
    print(f"ENTRY positive: {summary['entry_positive']:,} ({summary['positive_rate']:.2%})")
    print(f"ENTRY negative: {summary['entry_negative']:,}")
    print(f"Base dataset: {summary['base_dataset']}")
    print(f"Schema report: {summary['schema_report']}")
    print(f"Leakage report: {summary['leakage_report']}")
    print(f"Figures: {summary['figures']}")
    print("Next recommended phase: Feature Engineering")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
