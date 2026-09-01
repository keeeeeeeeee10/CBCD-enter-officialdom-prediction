# Phase 3.1 statistical audit

## Statistics review scope

**Input reviewed.** Tables 3, 4, and 5; Appendix Tables A1 to A4; Phase 2.5 paired-bootstrap artifacts and person-level prediction parquets; Phase 2.6 locked metrics, calibration, multi-seed, spatial-shift, family, and address-decomposition artifacts; Phase 3 generated tables and LaTeX.

**Study design readout.** The primary endpoint is binary ENTRY-record presence among CBDB-covered individuals. The primary analysis unit is `person_id` in the frozen test partition. Model fitting, early stopping, class-weight choice, thresholds, and sigmoid calibration use training or validation data according to the frozen protocol. The primary test is used for evaluation, not calibrator fitting.

**Replication readout.** Bootstrap resamples quantify variation across frozen-test people for exact retained model pairs. The five model seeds are algorithmic stability runs, not independent historical samples and not confidence intervals. Matched random and spatial tests use the same reliable-prefecture support but different people, so individual-paired bootstrap is not applicable.

**Boundary.** This audit recomputes metrics from retained predictions and repairs reporting. It does not retrain models, create a new split, tune hyperparameters, or estimate uncertainty for a contrast whose exact paired predictions were not retained.

## Major statistical issues

### P0. Physical Geography point estimates and intervals used different model definitions

**Evidence.** `outputs/phase3/tables/grouped_ablation_summary.csv` takes the Physical Geography point estimate from the Phase 2.6 A3 minus A2 address decomposition. `scripts/56_generate_final_paper_figures.py` previously obtained the interval by querying the Phase 2.5 paired-bootstrap table for G2 and G3. The A and G definitions are different. The discrepancy is visible because the Global PR-AUC point estimate, -0.000343, falls outside the borrowed interval [-0.001574, -0.000414]. The appendix Ming point estimates also fall outside the borrowed intervals.

**Why it matters.** A paired interval is only valid for the exact pair of predictions used to compute the point estimate, on identical test people and labels. Similar interpretation or sign does not make model definitions exchangeable.

**Correction.** The A3 minus A2 point estimates are retained. All Physical Geography confidence intervals are set to not available. The table caption must state, “Exact paired predictions were not retained for this contrast.” The old G3 minus G2 intervals are rejected and are not reused.

**Why no exact recomputation was performed.** Phase 2.6 saved A2 and A3 aggregate metrics and prediction hashes but no person-level A2/A3 prediction rows. The retained geography parquet contains G0 to G5, not A2 or A3. The locked Phase 2.6 prediction parquet contains only H_STRUCT, D5_MAIN, and D6_UPPER. Recreating A2/A3 probabilities would require a new model run, which this phase prohibits.

### P1. Raw and calibrated probability metrics were visually mixed

**Evidence.** Table 3 places raw LogLoss and raw Brier next to ECE computed after validation-fitted sigmoid calibration. The caption mentions calibration, but the column headers do not identify the probability version.

**Correction.** Use `Raw LogLoss`, `Raw Brier`, and `Validation-calibrated ECE` as the column labels. An appendix comparison is generated at `outputs/phase3_1/tables/raw_vs_validation_calibrated_metrics.csv`, with explicit raw and validation-calibrated LogLoss, Brier, and ECE.

### P1. PR-AUC needs local prevalence

**Evidence.** Appendix Table A2 includes prevalence, but the headline Table 3 omits it. Test prevalence differs materially across Global (0.333854), Song (0.482731), and Ming (0.199278).

**Correction.** Add a prevalence column to the revised headline performance table or include the exact prevalence in its caption. Interpret cross-population PR-AUC only together with prevalence.

### P1. Repeated use of the primary test limits inferential scope

**Evidence.** The manuscript acknowledges that later analyses were designed after earlier benchmark results had been observed.

**Correction.** Retain the frozen estimates, but describe the primary-test evidence as repeatedly inspected and potentially adaptive. Bootstrap intervals cover resampling of test people conditional on the frozen records and models. They do not cover this researcher-adaptation risk.

## Metric and table verification

### Table 3

All 9 locked population-model combinations were recomputed from the person-level Phase 2.6 prediction parquet. ROC-AUC, PR-AUC, raw LogLoss, raw Brier, raw ECE, validation-calibrated ECE, validation-calibrated LogLoss, validation-calibrated Brier, prevalence, and test size matched the frozen metric and calibration tables. This produced 90 recomputation checks in `outputs/phase3_1/tables/final_metric_recomputation.csv`.

The three metric directions are now explicit.

- Higher is better for ROC-AUC, PR-AUC, balanced accuracy, and F1.
- Lower is better for LogLoss, Brier score, and ECE.
- ECE is a descriptive binned calibration error and depends on the declared 10-bin implementation.

D5_MAIN remains the headline model. The Global estimates are ROC-AUC 0.936956 and PR-AUC 0.882535. D6_UPPER is only a database-internal record-structure upper bound.

### Table 4

All 27 grouped ablation rows were traced to their source contrasts. The revised table preserves exact paired intervals only where the exact model pair was retained. Eighteen retained ROC or PR intervals pass the automated check `ci_lower <= point_estimate <= ci_upper`.

For Physical Geography, Global, Song, and Ming retain their A3 minus A2 point estimates and show no interval. No result is substituted from G3 minus G2.

The small Global family-capital increments remain correctly bounded. Statistical detectability and practical importance are kept distinct. Increments of roughly 0.0003 to 0.0011 are not described as substantively large.

### Table 5

All 36 displayed matched-support spatial quantities were traced to `matched_random_vs_spatial_results.csv`. The matched random and matched spatial partitions have identical support definitions but different person IDs. The manuscript must not call their differences paired-individual estimates.

Family holdout keeps connected family groups disjoint. SAFE temporal and Qing rows correctly remain missing because there is no frozen locked-model performance artifact for those analyses. Full-coverage source-group confirmation remains unavailable under the prespecified connected-component gate.

### Appendix and multi-seed stability

All 48 multi-seed summary rows were recalculated from seeds 42, 202, 2024, 2025, and 2026. Means, sample standard deviations, minima, maxima, medians, positive-seed counts, and seed counts match the saved summaries. These ranges describe fitted-model stability under the five seeds. They are not bootstrap or population confidence intervals, and no best seed was selected.

Appendix performance metrics retain six-decimal precision and include prevalence. Raw and validation-calibrated probability metrics are separated in the new appendix comparison table.

## Paired and unpaired comparison policy

An interval may be labeled paired only when all of the following hold.

1. The two model IDs match the reported contrast exactly.
2. Both prediction sets contain the same unique `person_id` values.
3. The corresponding `y_true` values are identical.
4. The predictions use the same target, population, split protocol, subset, and evaluation partition.
5. Resampling applies the same sampled rows or clusters to both predictions.

The retained Phase 2.5 individual paired intervals use 500 seed-42 stratified resamples. Family-cluster and spatial-cluster analyses use their stated cluster units. Matched random versus matched spatial results are unpaired at person level.

## Calibration audit

The sigmoid calibrator is fit on validation logits and evaluated on test predictions. No test label is used to fit the calibrator. Raw balanced-weight probabilities can have substantial mean-probability bias, especially in Ming. The calibrated values are a diagnostic correction for the frozen test distribution, not estimates of a person's true historical probability of entering government and not a guarantee of calibration under distribution shift.

## Bootstrap interpretation

The reported percentile intervals quantify conditional test-sample variability under the resampling unit and fixed predictions. They do not include uncertainty from the definition of $E$, latent $T$, incomplete $P$, nonrandom CBDB coverage, source survival, editorial encoding, feature construction choices, hyperparameter choices, or repeated human inspection of the primary test.

## Generated correction artifacts

- `outputs/phase3_1/tables/statistical_correction_manifest.csv`
- `outputs/phase3_1/tables/grouped_ablation_corrected.csv`
- `outputs/phase3_1/tables/final_metric_recomputation.csv`
- `outputs/phase3_1/tables/statistics_verification.csv`
- `outputs/phase3_1/tables/raw_vs_validation_calibrated_metrics.csv`
- `outputs/phase3_1/tables/statistics_audit_status.json`
- `data/phase3_1/final_model_test_predictions.parquet`

The prediction export contains 436,881 person-model rows for H_STRUCT, D5_MAIN, and D6_UPPER across Global, Song, and Ming. It contains no direct identity text and uses Parquet with zstd compression. Its SHA256 is `86ee951335c09fbaf3e010ce95407304a612243ea1e18affd784db55fd526fbe`.

## Reviewer-risk note

After the correction, the most important remaining statistical risk is interpretive rather than computational. The primary test has been inspected across multiple analysis phases, and its bootstrap intervals cannot absorb adaptation or target-definition uncertainty. The manuscript should therefore make the spatial-shift evidence, small practical magnitude of family-capital increments, and proxy-label boundary at least as prominent as the high primary-test discrimination.
