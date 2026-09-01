#!/usr/bin/env bash
set -euo pipefail

PHASE31_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PHASE31_ROOT"
mkdir -p outputs/phase3_1/logs
PHASE31_LOG="outputs/phase3_1/logs/run_phase3_1_nature_revision.log"
exec > >(tee "$PHASE31_LOG") 2>&1

stage() {
  printf '\n[%02d/21] %s\n' "$1" "$2"
}

stage 1 "Frozen invariant precheck"
python scripts/65_phase3_1_audits.py --precheck-only

stage 2 "Nature reviewer Round 1 artifact"
test -s docs/phase3_1/nature_review_round1.md

stage 3 "Nature statistics audit and recomputation"
python scripts/61_phase3_1_statistics.py
test -s docs/phase3_1/nature_statistics_audit.md

stage 4 "Statistical correction and manuscript safeguards"
python scripts/64_prepare_phase3_1_manuscript.py

stage 5 "Nature writing structure"
test -s docs/phase3_1/nature_writing_structure.md
test -s paper/revised/main_body_revised.tex

stage 6 "Nature citation literature support"
test -s docs/phase3_1/nature_citation_search.md
test -s outputs/phase3_1/tables/nature_citation_candidates.ris

stage 7 "Nature reference verification"
python scripts/62_build_revised_references.py
test -s docs/phase3_1/reference_verification_report.md

stage 8 "Nature figure revision"
python scripts/63_phase3_1_figures.py

stage 9 "Nature data audit"
test -s docs/phase3_1/nature_data_audit.md
test -s outputs/phase3_1/tables/data_availability_inventory.csv

stage 10 "Nature polishing audit"
python scripts/65_phase3_1_audits.py
test -s docs/phase3_1/nature_polishing_audit.md

stage 11 "Compile author PDF"
(cd paper/revised && latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -jobname=cbdb_kdd_style_author_revised main_author_revised.tex > cbdb_kdd_style_author_revised.build.log 2>&1)

stage 12 "Compile anonymous PDF"
(cd paper/revised && latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -jobname=cbdb_kdd_style_anonymous_revised main_anonymous_revised.tex > cbdb_kdd_style_anonymous_revised.build.log 2>&1)
python scripts/65_phase3_1_audits.py

stage 13 "Run pre-package consistency tests"
pytest -q tests/test_phase3_1_statistics.py tests/test_phase3_1_claims.py tests/test_phase3_1_references.py tests/test_phase3_1_figures.py tests/test_phase3_1_latex.py | tee outputs/phase3_1/logs/pytest_phase3_1_prepackage.log

stage 14 "Nature reviewer Round 2 artifact"
test -s docs/phase3_1/nature_review_round2.md
grep -q 'ACCEPTABLE_FOR_COURSE_SUBMISSION' docs/phase3_1/nature_review_round2.md

stage 15 "Apply non-substantive final audits"
python scripts/65_phase3_1_audits.py

stage 16 "Recompile final PDFs"
(cd paper/revised && latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -jobname=cbdb_kdd_style_author_revised main_author_revised.tex > cbdb_kdd_style_author_revised.build.log 2>&1)
(cd paper/revised && latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -jobname=cbdb_kdd_style_anonymous_revised main_anonymous_revised.tex > cbdb_kdd_style_anonymous_revised.build.log 2>&1)
python scripts/65_phase3_1_audits.py

stage 17 "Final pre-package tests"
pytest -q tests/test_phase3_1_statistics.py tests/test_phase3_1_claims.py tests/test_phase3_1_references.py tests/test_phase3_1_figures.py tests/test_phase3_1_latex.py | tee outputs/phase3_1/logs/pytest_phase3_1.log

stage 18 "Package submission ZIP"
python scripts/66_package_phase3_1.py --kind submission

stage 19 "Package and finalize review ZIP"
python scripts/66_package_phase3_1.py --kind review --finalize

stage 20 "Validate both ZIPs"
unzip -t submission/cbdb_final_submission_nature_revised.zip >/dev/null
unzip -t review_bundles/cbdb_final_paper_review_bundle_nature_revised.zip >/dev/null

stage 21 "Final invariant and full test check"
python scripts/65_phase3_1_audits.py
pytest -q tests/test_phase3_1_statistics.py tests/test_phase3_1_claims.py tests/test_phase3_1_references.py tests/test_phase3_1_figures.py tests/test_phase3_1_latex.py tests/test_phase3_1_packages.py tests/test_phase3_1_invariants.py

printf '\n================================================\n'
printf 'PHASE 3.1 NATURE-ASSISTED PAPER REVISION PASS\n'
printf '================================================\n'
printf 'Author paper: paper/revised/cbdb_kdd_style_author_revised.pdf\n'
printf 'Submission: submission/cbdb_final_submission_nature_revised.zip\n'
printf 'Review bundle: review_bundles/cbdb_final_paper_review_bundle_nature_revised.zip\n'
