#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ -f "$PROJECT_ROOT/.venv/bin/activate" ]]; then
  source "$PROJECT_ROOT/.venv/bin/activate"
fi
export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"

mkdir -p outputs/phase2_5/logs
RUN_LOG="outputs/phase2_5/logs/run_phase2_5.log"
exec > >(tee "$RUN_LOG") 2>&1

python scripts/30_phase2_5_semantic_patch.py
python scripts/31_gender_audit.py
python scripts/32_geography_decomposition.py
python scripts/33_family_signal_decomposition.py
python scripts/34_documentation_controlled_ablation.py
python scripts/35_build_spatial_holdout.py
python scripts/36_run_spatial_robustness.py
python scripts/37_target_sensitivity.py
python scripts/38_paired_bootstrap_validation.py
python scripts/39_calibration_audit.py
python scripts/40_generate_phase2_5_report.py

pytest -q \
  tests/test_feature_policy.py \
  tests/test_no_target_encoding_leakage.py \
  tests/test_phase2_5_geo_encoding.py \
  tests/test_phase2_5_family_inductive.py \
  tests/test_phase2_5_spatial_split.py \
  tests/test_phase2_5_predictions.py \
  tests/test_phase2_5_invariants.py \
  | tee outputs/phase2_5/logs/pytest_phase2_5.log

python scripts/40_generate_phase2_5_report.py --final-invariants
python scripts/41_package_phase2_5_review.py
