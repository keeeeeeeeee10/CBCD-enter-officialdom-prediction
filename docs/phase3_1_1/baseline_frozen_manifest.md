# Phase 3.1 frozen baseline

This manifest records the last accepted Phase 3.1 state before the non-experimental Phase 3.1.1 polish. It is an audit record, not a new scientific result.

## Repository state

- Git status: `NOT_A_GIT_REPOSITORY`
- Existing Phase 3.1 precheck: `PASS: Phase 1--3 frozen artifacts unchanged`
- Existing focused test suite: `21 passed`
- SHA-256 inventory: `outputs/phase3_1_1/manifests/baseline_sha256.tsv` (97 files)

## Manuscript state

- Total PDF pages: 16
- Main-text pages: 8
- References start page: 9
- Appendix start page: 10
- Section commands in source: 19
- Subsection commands in source: 6
- Figure environments: 11
- Table inputs: 10
- Bibliography entries: 20

## Frozen scientific invariants

- Global D5_MAIN: ROC-AUC 0.936956; PR-AUC 0.882535; raw LogLoss 0.315106; raw Brier 0.097356; validation-calibrated ECE 0.003438.
- Table A2, Table A3 and Table A4 values are frozen; Physical geography retains a dash for unavailable confidence intervals.
- Model, split and prediction hashes in the inventory are immutable Phase 3.1.1 release checks.
- Phase 3.1 outputs remain in place and are never overwritten by the Phase 3.1.1 generation scripts.
