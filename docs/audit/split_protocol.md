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

## Split C — Global chronological distribution-shift sensitivity

Only SAFE time-anchor people are eligible. Whole years are kept together: train through 1729, validation through 1821, and later years test. This is **not** pure temporal generalization: calendar time, dynasty/regime composition, source composition, and recording practice all shift together. It is a limited-cohort global chronological distribution-shift sensitivity analysis, not a replacement for the main split.

## Split D — dynasty holdout

The concrete Qing holdout trains on Song+Yuan+Ming and tests on Qing. Additional leave-one-major-dynasty-out evaluations should rotate Tang/Song/Yuan/Ming/Qing. These evaluate transport across institutional regimes; low performance is informative rather than a tuning failure.

## Two-track family leakage protocol

The large-sample **Cross-sectional Family Capital** track may use explicitly named `ever_*` lifetime-record features. It measures recorded family political capital in the full historical record and supports predictive association analysis, not strict pre-entry or causal interpretation. The **Pre-birth Lineage Political Capital** track is restricted to people with a SAFE birth year and requires a valid relative event year strictly before birth. It is not a true pre-entry risk-time design. Undated relative outcomes remain missing. Full rules are frozen in `family_feature_protocol.md`.

Use the real `KINSHIP_CODES` direction fields (`c_upstep`, `c_dwnstep`, `c_marstep`) plus labels to classify relations:

- `ancestor`: upstep > 1, no descendant step; highest priority older ancestors.
- `parent_generation`: upstep = 1; prioritize father, maternal elder, and known parents.
- `same_generation`: neither upward nor downward generation after resolving collaterals; siblings are not automatically pre-entry-safe.
- `descendant`: dwnstep > 0; excluded by default from a pre-entry background model.
- `marital`: marstep > 0; allowed only when marriage timing precedes the focal anchor.
- `other`: missing/sentinel/conflicting direction; manual review or exclusion.

For pre-birth features, a relative's ENTRY/posting can contribute only if its valid event year is earlier than the focal person's `safe_birth_year`. Undated career outcomes remain missing. Children, descendants, spouses, and same-generation kin are excluded from the first pre-birth specification.

Family group identifiers are constructed before family-aware split assignment. Fold-dependent target aggregates, family outcome aggregates, local target priors, encodings, and imputations must be fitted only using the corresponding training fold.

## Documentation-bias separation

Documentation indicators exclude ENTRY and posting. M5 is evaluated alone, then added to the historical feature set. Differences are predictive associations with database recording intensity and must not be interpreted as historical causes.

## Family-group robustness split

The primary benchmark remains dynasty × target stratified. A separately saved robustness split assigns whole core blood-family groups to one partition, so no `family_group_id` crosses train, validation, and test. Marriage, affinal, and distant-kin propagation are excluded from component construction to avoid an elite-network giant component.

## Within-dynasty temporal plan

Phase 2/3 should audit SAFE-time sample sizes within Song, Ming, and Qing. Where counts and target support are sufficient, save dynasty-specific early/middle/late or 70%/15%/15% chronological cohorts. These are intended to test within-regime temporal generalization more cleanly than the global chronological sensitivity. They are not forced in this patch because SAFE-time coverage remains low.
