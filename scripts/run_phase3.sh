#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PROJECT_ROOT}/.venv/bin/python"
LOG_DIR="${PROJECT_ROOT}/outputs/phase3/logs"
RUN_LOG="${LOG_DIR}/run_phase3.log"

mkdir -p "${LOG_DIR}"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Project Python is missing: ${PYTHON_BIN}" >&2
  exit 1
fi

export PYTHONPATH="${PROJECT_ROOT}"
cd "${PROJECT_ROOT}"

exec > >(tee "${RUN_LOG}") 2>&1

echo "[Phase 3] frozen invariant precheck and source linkage audit"
"${PYTHON_BIN}" scripts/53_source_linkage_audit.py

echo "[Phase 3] target-independent source connected components and feasibility gate"
"${PYTHON_BIN}" scripts/54_build_source_groups.py

echo "[Phase 3] optional one-shot locked source confirmation"
"${PYTHON_BIN}" scripts/55_run_source_group_confirmation.py

echo "[Phase 3] final scientific tables and locally generated figures"
"${PYTHON_BIN}" scripts/56_generate_final_paper_figures.py

echo "[Phase 3] generated LaTeX tables, manuscripts, bibliography, and Chinese summary"
"${PYTHON_BIN}" scripts/57_write_final_paper.py

echo "[Phase 3] compile author/anonymous PDFs and enforce paper quality gates"
"${PYTHON_BIN}" scripts/58_validate_final_paper.py

echo "[Phase 3] provisional archives required by the package tests"
"${PYTHON_BIN}" scripts/59_build_submission_package.py
"${PYTHON_BIN}" scripts/60_package_final_review.py
"${PYTHON_BIN}" scripts/58_validate_final_paper.py --invariants

echo "[Phase 3] automated tests"
"${PYTHON_BIN}" -m pytest -q 2>&1 | tee "${LOG_DIR}/pytest_phase3.log"

echo "[Phase 3] final archives, including test and run logs"
"${PYTHON_BIN}" scripts/59_build_submission_package.py
"${PYTHON_BIN}" scripts/60_package_final_review.py
"${PYTHON_BIN}" scripts/58_validate_final_paper.py --check-zips
"${PYTHON_BIN}" scripts/58_validate_final_paper.py --invariants

echo "[Phase 3] independent ZIP CRC validation"
unzip -t submission/cbdb_final_submission.zip
unzip -t review_bundles/cbdb_final_paper_review_bundle.zip
sha256sum submission/cbdb_final_submission.zip
sha256sum review_bundles/cbdb_final_paper_review_bundle.zip

echo "================================================"
echo "PHASE 3 FINAL PAPER & SUBMISSION PACKAGE PASS"
echo "================================================"
echo "Paper: paper/cbdb_kdd_style_author.pdf"
echo "Submission: submission/cbdb_final_submission.zip"
echo "Review bundle: review_bundles/cbdb_final_paper_review_bundle.zip"
