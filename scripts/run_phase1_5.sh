#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$PROJECT_ROOT"
mkdir -p outputs/logs
exec > >(tee outputs/logs/run_phase1_5.log) 2>&1

if [[ ! -x .venv/bin/python ]]; then
    echo "ERROR: Phase 1 environment .venv is missing; run bash scripts/run_phase1.sh first." >&2
    exit 2
fi
for required in data/interim/person_target.parquet data/processed/person_base_v0.parquet database/cbdb_working.sqlite3 data/raw/download_manifest.json; do
    if [[ ! -f "$required" ]]; then
        echo "ERROR: required Phase 1 artifact missing: $required" >&2
        exit 2
    fi
done

PHASE1_TARGET_SHA_BEFORE=$(sha256sum data/interim/person_target.parquet | awk '{print $1}')
PHASE1_BASE_SHA_BEFORE=$(sha256sum data/processed/person_base_v0.parquet | awk '{print $1}')

run_step() {
    local script=$1
    echo "[$(date -u +%FT%TZ)] Running $script"
    .venv/bin/python "$script"
}

echo "[$(date -u +%FT%TZ)] CBDB Phase 1.5 starting (no download, no database mutation)"
run_step scripts/07_entry_posting_semantics.py
run_step scripts/08_index_year_provenance.py
run_step scripts/09_entry_code_taxonomy.py
run_step scripts/10_temporal_anchor_audit.py
run_step scripts/11_modeling_population.py
run_step scripts/12_split_protocol.py
run_step scripts/13_phase1_5_sanity.py

PHASE1_TARGET_SHA_AFTER=$(sha256sum data/interim/person_target.parquet | awk '{print $1}')
PHASE1_BASE_SHA_AFTER=$(sha256sum data/processed/person_base_v0.parquet | awk '{print $1}')
if [[ "$PHASE1_TARGET_SHA_BEFORE" != "$PHASE1_TARGET_SHA_AFTER" ]]; then
    echo "ERROR: Phase 1 person_target.parquet was modified" >&2
    exit 3
fi
if [[ "$PHASE1_BASE_SHA_BEFORE" != "$PHASE1_BASE_SHA_AFTER" ]]; then
    echo "ERROR: Phase 1 person_base_v0.parquet was modified" >&2
    exit 3
fi
echo "Phase 1 artifact hashes unchanged."

