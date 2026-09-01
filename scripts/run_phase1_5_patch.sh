#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$PROJECT_ROOT"
mkdir -p outputs/logs data/splits
exec > >(tee outputs/logs/run_phase1_5_patch.log) 2>&1

if [[ ! -x .venv/bin/python ]]; then
    echo "ERROR: project environment .venv is missing" >&2
    exit 2
fi

required=(
    database/cbdb_20260829.sqlite3
    database/cbdb_working.sqlite3
    data/interim/person_target.parquet
    data/processed/person_base_v0.parquet
    data/interim/person_modeling_population.parquet
    data/interim/person_split_assignments.parquet
    docs/archive/pre_phase15_patch/leakage_audit.md
    outputs/archive/pre_phase15_patch/feature_leakage_classification.csv
)
for path in "${required[@]}"; do
    if [[ ! -f "$path" ]]; then
        echo "ERROR: required foundation/archive file missing: $path" >&2
        exit 2
    fi
done

RAW_SHA_BEFORE=$(sha256sum database/cbdb_20260829.sqlite3 | awk '{print $1}')
TARGET_SHA_BEFORE=$(sha256sum data/interim/person_target.parquet | awk '{print $1}')
BASE_SHA_BEFORE=$(sha256sum data/processed/person_base_v0.parquet | awk '{print $1}')

run_step() {
    local script=$1
    echo "[$(date -u +%FT%TZ)] Running $script"
    .venv/bin/python "$script"
}

echo "[$(date -u +%FT%TZ)] CBDB Phase 1.5 Patch & Freeze starting"
run_step scripts/12_patch_phase1_5_metadata.py
run_step scripts/13_prepare_family_graph.py
run_step scripts/14_family_group_analysis.py
run_step scripts/15_family_aware_split.py

echo "[$(date -u +%FT%TZ)] Running feature-policy tests"
.venv/bin/python -m pytest -q tests/test_feature_policy.py

run_step scripts/13_phase1_5_sanity.py
run_step scripts/16_phase1_5_patch_freeze.py

RAW_SHA_AFTER=$(sha256sum database/cbdb_20260829.sqlite3 | awk '{print $1}')
TARGET_SHA_AFTER=$(sha256sum data/interim/person_target.parquet | awk '{print $1}')
BASE_SHA_AFTER=$(sha256sum data/processed/person_base_v0.parquet | awk '{print $1}')
if [[ "$RAW_SHA_BEFORE" != "$RAW_SHA_AFTER" ]]; then
    echo "ERROR: original SQLite changed during patch" >&2
    exit 3
fi
if [[ "$TARGET_SHA_BEFORE" != "$TARGET_SHA_AFTER" ]]; then
    echo "ERROR: Phase 1 target changed during patch" >&2
    exit 3
fi
if [[ "$BASE_SHA_BEFORE" != "$BASE_SHA_AFTER" ]]; then
    echo "ERROR: Phase 1 base changed during patch" >&2
    exit 3
fi
echo "Immutable foundation hashes unchanged across patch run."
