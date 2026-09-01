#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ -f "$PROJECT_ROOT/.venv/bin/activate" ]]; then
  source "$PROJECT_ROOT/.venv/bin/activate"
fi
export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"

mkdir -p outputs/phase2_6/logs
RUN_LOG="outputs/phase2_6/logs/run_phase2_6.log"
exec > >(tee -a "$RUN_LOG") 2>&1

run_stage() {
  local marker="$1"
  shift
  if [[ -s "$marker" ]]; then
    echo "RESUME validated existing stage marker: $marker"
  else
    "$@"
  fi
}

python scripts/42_phase2_6_semantic_patch.py
run_stage outputs/phase2_6/tables/birth_missingness_deltas.csv python scripts/43_birth_missingness_audit.py
run_stage outputs/phase2_6/tables/address_semantics_deltas.csv python scripts/44_address_semantics_decomposition.py
run_stage outputs/phase2_6/tables/multiseed_delta_summary.csv python scripts/45_multiseed_stability.py
run_stage outputs/phase2_6/tables/matched_spatial_overlap_check.json python scripts/46_matched_support_spatial_comparison.py
run_stage outputs/phase2_6/tables/final_model_lock_manifest.json python scripts/47_lock_final_models.py
run_stage outputs/phase2_6/shap/shap_additivity_check.json python scripts/48_grouped_shap_analysis.py
run_stage outputs/phase2_6/tables/final_feature_coverage.csv python scripts/49_final_descriptive_analysis.py
run_stage outputs/phase2_6/figures/final_calibration_summary.svg python scripts/50_generate_final_figures.py
run_stage docs/phase2_6/final_model_report.md python scripts/51_generate_final_reports.py

python -m pytest -q tests | tee outputs/phase2_6/logs/pytest_phase2_6.log

python scripts/51_generate_final_reports.py --final-invariants
python scripts/52_package_phase2_6_review.py
