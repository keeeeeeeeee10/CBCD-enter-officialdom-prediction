# Modeling, split, ablation, and family-leakage protocol

Phase 1.5 freezes protocols but trains no formal model. Any future preprocessing, imputation, category consolidation, family aggregation, matching, and feature selection must be fitted on training data only. Test labels remain untouched until the final locked evaluation.

## Modeling populations

| population | people | V1 rate | posting rate | kin | address | association | SAFE time |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Global | 661124 | 33.37% | 45.23% | 43.29% | 59.83% | 6.77% | 9.05% |
| Song | 83373 | 48.27% | 37.30% | 42.69% | 67.95% | 17.10% | 7.20% |
| Ming | 225403 | 19.93% | 32.65% | 67.73% | 47.07% | 4.41% | 6.25% |
| Qing | 237423 | 54.54% | 62.11% | 14.76% | 76.10% | 3.28% | 10.19% |

Population choice must balance target definition, family/geography coverage, safe time coverage, and institutional comparability—not sample size alone. Global and dynasty-specific results must be reported separately.

## Required baselines and ablations

- **Baseline 0 / M0a — dynasty only.**
- **Baseline 1 / M0 — dynasty + SAFE cohort/time.**
- **M1 Personal — M0 + gender and safe personal background.**
- **M2 Geography — M1 + pre-entry geographic background.**
- **M3 Family — M2 + temporally valid family political capital.**
- **M4 Network — M3 + dated, pre-entry social-network features on the eligible subset.**
- **M5 Documentation — documentation-only indicators/intensity.**
- **Full historical — M0+M1+M2+M3+M4.**
- **Historical + documentation — all safe historical and documentation features.**

Every extension reports ΔROC-AUC, ΔPR-AUC, and ΔLogLoss relative to the relevant dynasty/time baseline, with uncertainty. V1 is always described as current CBDB ENTRY-record presence; V2 candidates and posting are robustness outcomes.

## Split A — random target-stratified

A deterministic 70%/15%/15% assignment with seed 42. It is a standard ML benchmark only and cannot be the sole historical validation.

## Split B — dynasty + target stratified (recommended primary benchmark)

The same proportions are assigned independently within every `(dynasty_code, target)` stratum. This prevents major dynasty concentration in one partition while preserving a locked test set. Family-connected people may later require group-aware refinement to prevent relatives crossing folds.

## Split C — temporal SAFE-anchor split

Only SAFE time-anchor people are eligible. Whole years are kept together: train through 1729, validation through 1821, and later years test. This is a limited-cohort sensitivity analysis, not a replacement for the main split.

## Split D — dynasty holdout

The concrete Qing holdout trains on Song+Yuan+Ming and tests on Qing. Additional leave-one-major-dynasty-out evaluations should rotate Tang/Song/Yuan/Ming/Qing. These evaluate transport across institutional regimes; low performance is informative rather than a tuning failure.

## Family leakage protocol

Use the real `KINSHIP_CODES` direction fields (`c_upstep`, `c_dwnstep`, `c_marstep`) plus labels to classify relations:

- `ancestor`: upstep > 1, no descendant step; highest priority older ancestors.
- `parent_generation`: upstep = 1; prioritize father, maternal elder, and known parents.
- `same_generation`: neither upward nor downward generation after resolving collaterals; siblings are not automatically pre-entry-safe.
- `descendant`: dwnstep > 0; excluded by default from a pre-entry background model.
- `marital`: marstep > 0; allowed only when marriage timing precedes the focal anchor.
- `other`: missing/sentinel/conflicting direction; manual review or exclusion.

A relative's ENTRY/posting/status can contribute to `father_official`, `grandfather_official`, or family entry rates only if the relative outcome year is valid and no later than the focal person's training-fold risk anchor. Undated career outcomes are excluded from the strict feature, retained only in sensitivity variants. Children, younger descendants, and later-life siblings are prohibited by default. Family components must be calculated after split assignment; connected-family grouping should be considered to avoid relational leakage across train/test.

## Documentation-bias separation

Documentation indicators exclude ENTRY and posting. M5 is evaluated alone, then added to the historical feature set. Differences are predictive associations with database recording intensity and must not be interpreted as historical causes.
