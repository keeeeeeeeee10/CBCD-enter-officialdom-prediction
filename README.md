# Who Leaves a Recorded Path into Government?

[中文说明](README_ZH.md)

This repository contains the public, frozen Phase 3.1.1 release of a CBDB data-mining course project on structure, documentation, and distribution shift in the China Biographical Database (CBDB).

## Research question and target

The project asks how reliably personal, geographic, family, and documentation features predict whether a CBDB-covered person has at least one `ENTRY_DATA` record.

The target is retrospective **record presence** (`E`), not true historical entry into government (`T`) and not posting-record presence (`P`). These constructs are not interchangeable. The models do not recover historical ground truth and the reported associations are not causal effects.

## Frozen release

Phase 3.1.1 is a non-experimental publication revision. It did not train or tune models, select a split, access reserve or protected data, reconstruct missing confidence intervals, or change frozen predictions and metrics.

The designated Global D5_MAIN result remains:

| Metric | Frozen value |
| --- | ---: |
| ROC-AUC | 0.936956 |
| PR-AUC | 0.882535 |
| Raw LogLoss | 0.315106 |
| Raw Brier score | 0.097356 |
| Validation-calibrated ECE | 0.003438 |

Interpretation boundaries and unavailable robustness results are documented in the [latest results summary](docs/phase3_1_1/latest_results_summary.md), [claim–evidence map](docs/phase3_1_1/final_claim_evidence_map.md), and [reproducibility audit](docs/phase3_1_1/final_reproducibility_audit.md).

## Paper

- [Author version (PDF)](paper/final/cbdb_kdd_style_author_final.pdf)
- [Anonymous version (PDF)](paper/final/cbdb_kdd_style_anonymous_final.pdf)
- [LaTeX source and bibliography](paper/final/)

Frozen PDF SHA-256 values:

```text
6d010ffb2592b3e3309efb69ffcb480f841c80c90e55c918b0acc03f85adcaa2  cbdb_kdd_style_author_final.pdf
988b050c0045541209d2eb01ea0d28739ecdf6c56d6073faac2c02f71bd2f624  cbdb_kdd_style_anonymous_final.pdf
```

## Data availability

CBDB is a third-party research database. This repository does **not** redistribute the CBDB SQLite database or grant rights to its data. Obtain an authorized release through the official [CBDB SQLite release channel](https://github.com/cbdb-project/cbdb_sqlite) and follow the provider's terms.

The frozen analysis used `cbdb_20260829.sqlite3`, containing 661,124 `BIOG_MAIN` person records. Counts are release-specific and do not represent the historical population of China.

Raw and derived databases, row-level feature matrices, split assignments, trained models, full predictions, protected/reserve artifacts, caches, logs, and duplicate release ZIPs are intentionally excluded. The repository therefore supports inspection of the code, paper, configurations, lightweight aggregate evidence, and release checks; it is not a self-contained copy of the private frozen experiment workspace.

## Environment

Python 3.11 is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Conda users can instead run:

```bash
conda env create -f environment.yml
conda activate cbdb
```

## Public release verification

The following checks do not train a model or alter frozen artifacts:

```bash
python scripts/verify_public_release.py
PYTHONPATH="$PWD/tests/import_stubs:$PWD" python -m pytest -q \
  tests/test_phase3_1_1_claims.py \
  tests/test_phase3_1_1_methods.py
```

The complete archival runner, [`scripts/run_phase3_1_1_final_polish.sh`](scripts/run_phase3_1_1_final_polish.sh), requires the non-public frozen models, splits, predictions, compiler artifacts, and optional figure-audit utilities. It is published for method transparency and will intentionally stop when those inputs are absent. It must be run only from an authorized complete checkout; it is not the public-repository smoke test.

## Repository structure

```text
configs/                  Frozen feature, model, reporting, and geography settings
docs/phase3_1_1/          Scope, audit, claim–evidence, and reproducibility records
outputs/                  Lightweight aggregate tables, manifests, and method specs
paper/final/              Final PDFs, LaTeX/BibTeX, tables, and figure files
scripts/                  Non-experimental release and audit scripts
src/                      Reusable feature, geography, and utility modules
tests/                    Frozen full-checkout tests and public-safe focused tests
```

The baseline SHA-256 inventory lists both public summaries and deliberately excluded private artifacts. A listed hash does not imply that the underlying database, model, split, or prediction file is distributed here.

## Reproduction boundaries

- The public checks verify PDF identity, repository hygiene, frozen claims, and the recovered `local_target_prior` behavior.
- Full end-to-end reproduction requires lawful CBDB access and the private frozen experimental artifacts.
- The repository does not include enough material to retrain or independently reproduce every reported metric from row-level data.
- Whole-family evidence applies only to the frozen F2 comparator for Global and Ming; D5_MAIN was not directly evaluated under that protocol.
- Results on CBDB record presence must not be interpreted as population entry rates, historical truth, or causal estimates.

## Citation

Use the metadata in [`CITATION.cff`](CITATION.cff). A plain-text citation is:

> Lu, Xiaoke (2026). *Who Leaves a Recorded Path into Government? Structure, Documentation, and Distribution Shift in CBDB*. Phase 3.1.1 software and course-project release.

## License

Project code and documentation are available under the [MIT License](LICENSE). The license does not apply to third-party CBDB data and does not grant data-redistribution rights.
