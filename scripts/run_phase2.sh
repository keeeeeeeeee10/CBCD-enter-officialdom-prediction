#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-${ROOT}/.venv/bin/python}"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Python executable not found or not executable: ${PYTHON_BIN}" >&2
  exit 2
fi

export PYTHONPATH="${ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
export PYTHONUNBUFFERED=1
cd "${ROOT}"

run_step() {
  echo "[phase2] $1"
  "${PYTHON_BIN}" "$1"
}

run_step scripts/19_phase2_semantic_patch.py
run_step scripts/20_build_personal_features.py
run_step scripts/21_build_geography_features.py
run_step scripts/22_build_family_structural_features.py
run_step scripts/23_build_family_capital_features.py
run_step scripts/24_build_phase2_dataset.py
run_step scripts/25_validate_phase2_features.py
run_step scripts/26_train_phase2_logistic.py
run_step scripts/27_train_phase2_catboost.py
run_step scripts/28_phase2_ablation.py
run_step scripts/29_phase2_robustness.py
run_step scripts/30_phase2_bootstrap.py
run_step scripts/31_phase2_figures.py
run_step scripts/32_phase2_report.py
run_step scripts/33_phase2_invariants.py

