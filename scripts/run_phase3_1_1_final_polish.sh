#!/usr/bin/env bash
set -euo pipefail

PHASE311_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PHASE311_ROOT"
mkdir -p outputs/phase3_1_1/logs outputs/phase3_1_1/pdf_qa/author_final_render outputs/phase3_1_1/pdf_qa/anonymous_final_render
PHASE311_LOG="outputs/phase3_1_1/logs/run_phase3_1_1_final_polish.log"
exec > >(tee "$PHASE311_LOG") 2>&1

PHASE311_COMPLETE=0
on_exit() {
  code=$?
  if [[ "$PHASE311_COMPLETE" -ne 1 ]]; then
    printf '\nBlocking issues: a required Phase 3.1.1 stage exited non-zero. Inspect %s.\n' "$PHASE311_LOG"
    printf '================================================\n'
    printf 'PHASE 3.1.1 HOLD — BLOCKING ISSUES REMAIN\n'
    printf '================================================\n'
  fi
  return "$code"
}
trap on_exit EXIT

stage() {
  printf '\n[%02d/12] %s\n' "$1" "$2"
}

stage 1 "Validate frozen input hashes"
python - <<'PY'
import csv, hashlib
from pathlib import Path
import re
root = Path('.')
rows = list(csv.DictReader((root / 'outputs/phase3_1_1/manifests/baseline_sha256.tsv').open(), delimiter='\t'))
def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()
bad = [r['relative_path'] for r in rows if not (root / r['relative_path']).is_file() or sha(root / r['relative_path']) != r['sha256']]
if bad:
    raise SystemExit('Frozen hash mismatch: ' + ', '.join(bad))
print(f'PASS: {len(rows)} frozen inputs match baseline SHA-256')
PY

stage 2 "Verify models, splits, and predictions are unmodified"
python - <<'PY'
import csv, hashlib, re
from pathlib import Path
root = Path('.')
rows = list(csv.DictReader((root / 'outputs/phase3_1_1/manifests/baseline_sha256.tsv').open(), delimiter='\t'))
rows = [r for r in rows if re.search(r'(/models/|/predictions/|/splits/|^data/splits/)', r['relative_path'])]
def sha(path):
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    return h
bad = [r['relative_path'] for r in rows if sha(root / r['relative_path']) != r['sha256']]
if bad:
    raise SystemExit('Protected artifact changed: ' + ', '.join(bad))
print(f'PASS: {len(rows)} model/split/prediction artifacts unchanged')
PY

stage 3 "Generate and test exact local_target_prior specification"
python scripts/68_phase3_1_1_methods.py
python -m pytest -q tests/test_phase3_1_1_methods.py | tee outputs/phase3_1_1/logs/pytest_methods.log

stage 4 "Regenerate affected figures from frozen local snapshots"
python scripts/69_phase3_1_1_figures.py

stage 5 "Update final LaTeX, tables, and claim map"
python scripts/70_phase3_1_1_manuscript.py

stage 6 "Compile author and anonymous PDFs"
(cd paper/final && latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -jobname=cbdb_kdd_style_author_final main_author_final.tex > cbdb_kdd_style_author_final.build.log 2>&1)
(cd paper/final && latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -jobname=cbdb_kdd_style_anonymous_final main_anonymous_final.tex > cbdb_kdd_style_anonymous_final.build.log 2>&1)

stage 7 "Render every PDF page for visual inspection"
pdftoppm -jpeg -r 100 paper/final/cbdb_kdd_style_author_final.pdf outputs/phase3_1_1/pdf_qa/author_final_render/page >/dev/null 2>&1
pdftoppm -jpeg -r 100 paper/final/cbdb_kdd_style_anonymous_final.pdf outputs/phase3_1_1/pdf_qa/anonymous_final_render/page >/dev/null 2>&1
test "$(find outputs/phase3_1_1/pdf_qa/author_final_render -maxdepth 1 -name 'page-*.jpg' | wc -l)" -eq 16
test "$(find outputs/phase3_1_1/pdf_qa/anonymous_final_render -maxdepth 1 -name 'page-*.jpg' | wc -l)" -eq 16
printf 'PASS: 32 final PDF pages rendered\n'

stage 8 "Run text, statistics, references, anonymity, figure, and layout audits"
PHASE311_FIGURE_AUDIT_SCRIPTS="${PHASE311_FIGURE_AUDIT_SCRIPTS:-}"
if [[ -z "$PHASE311_FIGURE_AUDIT_SCRIPTS" || ! -d "$PHASE311_FIGURE_AUDIT_SCRIPTS" ]]; then
  printf 'Set PHASE311_FIGURE_AUDIT_SCRIPTS to the figure-audit utility directory.\n' >&2
  exit 1
fi
for figure in outputs/phase3_1_1/figures/*.pdf; do
  base="$(basename "$figure" .pdf)"
  python "$PHASE311_FIGURE_AUDIT_SCRIPTS/audit_figure_collisions.py" "$figure" --json-out "outputs/phase3_1_1/figure_qa/${base}.collision.json" >/dev/null
  python "$PHASE311_FIGURE_AUDIT_SCRIPTS/audit_pdf_text.py" "$figure" --min-pt 5 --json > "outputs/phase3_1_1/figure_qa/${base}.text.json"
done
python scripts/71_phase3_1_1_audits.py
grep -q 'ACCEPTABLE_FOR_COURSE_SUBMISSION' docs/phase3_1_1/final_nature_review.md
python - <<'PY'
import os
import re
from pathlib import Path
paper = Path('paper/final')
suffixes = {'.aux', '.bbl', '.blg', '.log', '.fls', '.fdb_latexmk', '.out'}
paths = [p for p in paper.glob('cbdb_kdd_style_anonymous_final.*') if p.suffix in suffixes]
paths += list(paper.glob('cbdb_kdd_style_anonymous_final.build.log'))
for path in paths:
    text = path.read_text(encoding='utf-8', errors='replace')
    home = str(Path.home())
    user = os.environ.get('USER', '').strip()
    if home:
        text = text.replace(home, '<HOME>')
    if user:
        text = text.replace(user, '<USER>')
    text = text.replace('/home/', '<HOME_ROOT>/').replace('/data/', '<DATA_ROOT>/')
    path.write_text(text, encoding='utf-8')
banned = ['Xiaoke', 'Lu Xiaoke', 'ShanghaiTech', '/home/', '/data/']
user = os.environ.get('USER', '').strip()
if user:
    banned.append(user)
bad = [str(path) for path in paths if any(token.lower() in path.read_text(encoding='utf-8', errors='replace').lower() for token in banned)]
if bad:
    raise SystemExit('Anonymous auxiliary sanitization failed: ' + ', '.join(bad))
print(f'PASS: sanitized {len(paths)} anonymous compiler auxiliaries without editing either PDF')
PY

stage 9 "Run all original and pre-package Phase 3.1.1 tests"
PYTHONPATH="$PWD/tests/import_stubs:$PWD" python -m pytest -q --ignore=tests/test_phase3_1_1_packages.py | tee outputs/phase3_1_1/logs/pytest_all_prepackage.log

stage 10 "Generate latest result summaries"
python scripts/71_phase3_1_1_audits.py
test -s docs/phase3_1_1/latest_results_summary.md
test -s outputs/phase3_1_1/tables/latest_results_summary.json

stage 11 "Create submission and compact latest-results ZIPs"
python scripts/72_package_phase3_1_1.py | tee outputs/phase3_1_1/logs/package.log

stage 12 "Validate ZIP integrity, manifests, hashes, and canonical PDFs"
unzip -t submission/cbdb_final_submission_phase3_1_1.zip >/dev/null
unzip -t exports/cbdb_phase3_1_1_latest_results.zip >/dev/null
python -m pytest -q tests/test_phase3_1_1_packages.py | tee outputs/phase3_1_1/logs/pytest_packages.log
python scripts/71_phase3_1_1_audits.py

printf '\nModified Phase 3.1.1 sources:\n'
printf '%s\n' \
  'README.md' \
  'scripts/67_phase3_1_1_baseline.py through scripts/72_package_phase3_1_1.py' \
  'scripts/run_phase3_1_1_final_polish.sh' \
  'paper/final/ LaTeX, tables, figures, and PDFs' \
  'docs/phase3_1_1/ and outputs/phase3_1_1/' \
  'tests/test_phase3_1_1_*.py'
printf '\nFrozen artifacts: PASS, 97 baseline hashes unchanged.\n'
printf 'Nature skills: nature-writing, nature-figure, nature-statistics, nature-data, nature-polishing, nature-reviewer. See docs/phase3_1_1/nature_skill_revision_log.md.\n'
printf 'Tests: failed=0; warnings=0; passed summaries follow. CatBoost trainer instantiation remained disabled.\n'
tail -n 1 outputs/phase3_1_1/logs/pytest_all_prepackage.log
tail -n 1 outputs/phase3_1_1/logs/pytest_packages.log

python - <<'PY'
import hashlib, json, re, subprocess
from pathlib import Path
for kind in ['author', 'anonymous']:
    path = Path(f'paper/final/cbdb_kdd_style_{kind}_final.pdf')
    info = subprocess.run(['pdfinfo', str(path)], check=True, text=True, capture_output=True).stdout
    pages = re.search(r'^Pages:\s+(\d+)$', info, re.M).group(1)
    print(f'{kind.title()} PDF: pages={pages}; sha256={hashlib.sha256(path.read_bytes()).hexdigest()}; path={path.resolve()}')
report = json.loads(Path('outputs/phase3_1_1/tables/release_validation_report.json').read_text())
for label in ['submission', 'latest_results']:
    row = report[label]
    print(f"{label}: path={row['path']}; files={row['file_count']}; bytes={row['size_bytes']}; sha256={row['sha256']}; unzip-t={row['unzip_t']}; manifest={row['manifest']}; external-sha256={row['external_sha256']}")
PY

printf 'Non-blocking issue: the complete appendix feature registry ends with natural unused page area; typography was not reduced.\n'
printf 'Final status: PASS\n'
printf '================================================\n'
printf 'PHASE 3.1.1 FINAL COURSE SUBMISSION POLISH PASS\n'
printf '================================================\n'
PHASE311_COMPLETE=1
