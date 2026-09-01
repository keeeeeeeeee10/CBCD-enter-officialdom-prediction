#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$PROJECT_ROOT"
mkdir -p outputs/logs
exec > >(tee outputs/logs/run_phase1.log) 2>&1

echo "[$(date -u +%FT%TZ)] CBDB Phase 1 starting in $PROJECT_ROOT"

if [[ ! -x .venv/bin/python ]]; then
    echo "Creating project virtual environment with Python 3.11-compatible interpreter"
    python3 -m venv --system-site-packages .venv
fi

REQ_HASH=$(.venv/bin/python -c 'import hashlib,pathlib; print(hashlib.sha256(pathlib.Path("requirements.txt").read_bytes()).hexdigest())')
INSTALLED_HASH=""
if [[ -f .venv/.cbdb_requirements.sha256 ]]; then
    INSTALLED_HASH=$(<.venv/.cbdb_requirements.sha256)
fi
if [[ "$REQ_HASH" != "$INSTALLED_HASH" ]]; then
    echo "Installing project requirements through Tsinghua mirror with official PyPI fallback"
    if ! .venv/bin/python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple; then
        echo "WARNING: Tsinghua PyPI mirror failed; retrying official PyPI"
        .venv/bin/python -m pip install -r requirements.txt -i https://pypi.org/simple
    fi
    echo "$REQ_HASH" > .venv/.cbdb_requirements.sha256
fi

if [[ ! -f external/cbdb_sqlite/latest.json || ! -f external/cbdb_sqlite/scripts/create_views.sh ]]; then
    echo "Fetching official cbdb-project/cbdb_sqlite repository"
    mkdir -p external
    if [[ -e external/cbdb_sqlite ]]; then
        INCOMPLETE_BACKUP="external/cbdb_sqlite.incomplete.$(date -u +%Y%m%dT%H%M%SZ)"
        mv external/cbdb_sqlite "$INCOMPLETE_BACKUP"
        echo "Preserved incomplete official checkout at $INCOMPLETE_BACKUP"
    fi
    CLONE_ONE=$(mktemp -d external/cbdb_sqlite.clone.XXXXXX)
    rmdir "$CLONE_ONE"
    if git clone https://github.com/cbdb-project/cbdb_sqlite.git "$CLONE_ONE"; then
        mv "$CLONE_ONE" external/cbdb_sqlite
    else
        CLONE_TWO=$(mktemp -d external/cbdb_sqlite.shallow.XXXXXX)
        rmdir "$CLONE_TWO"
        if git clone --depth 1 https://github.com/cbdb-project/cbdb_sqlite.git "$CLONE_TWO"; then
            mv "$CLONE_TWO" external/cbdb_sqlite
        else
            mkdir -p external/cbdb_sqlite/scripts
            echo "WARNING: git clone failed; downloading the required files directly from the official GitHub repository"
            curl --fail --location --retry 3 --output external/cbdb_sqlite/latest.json https://raw.githubusercontent.com/cbdb-project/cbdb_sqlite/master/latest.json
            curl --fail --location --retry 3 --output external/cbdb_sqlite/scripts/create_views.sh https://raw.githubusercontent.com/cbdb-project/cbdb_sqlite/master/scripts/create_views.sh
            curl --fail --location --retry 3 --output external/cbdb_sqlite/scripts/create_addresses_table.py https://raw.githubusercontent.com/cbdb-project/cbdb_sqlite/master/scripts/create_addresses_table.py
        fi
    fi
fi

run_step() {
    local script=$1
    echo "[$(date -u +%FT%TZ)] Running $script"
    .venv/bin/python "$script"
}

run_step scripts/00_setup_check.py
run_step scripts/01_download_cbdb.py
run_step scripts/01_postprocess_database.py
run_step scripts/02_database_inventory.py
run_step scripts/03_schema_analysis.py
run_step scripts/04_target_definition.py
run_step scripts/05_leakage_audit.py
run_step scripts/06_build_base_dataset.py
run_step scripts/07_phase1_summary.py
