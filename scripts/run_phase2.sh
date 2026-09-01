#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ -f "$PROJECT_ROOT/.venv/bin/activate" ]]; then
  source "$PROJECT_ROOT/.venv/bin/activate"
fi
export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"

pytest -q tests/test_feature_policy.py tests/test_no_target_encoding_leakage.py
python scripts/19_phase2_semantic_patch.py
python scripts/20_build_personal_features.py
python scripts/21_build_geography_features.py
python scripts/22_build_family_structural_features.py
python scripts/23_build_family_capital_features.py
python scripts/24_build_phase2_dataset.py
python scripts/25_validate_phase2_features.py
python scripts/26_train_phase2_logistic.py
python scripts/27_train_phase2_catboost.py
python scripts/28_phase2_ablation.py
python scripts/29_phase2_robustness.py
python scripts/30_phase2_report_and_sanity.py
