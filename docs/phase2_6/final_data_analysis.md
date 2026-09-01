# 谁会留下入仕记录？

## 基于 CBDB 的性别、地域、家族可观测性与史料记录偏差分析

**English title:** Who Leaves a Recorded Path into Government? Gender, Geography, Family Observability, and Documentation Bias in CBDB

The outcome throughout this chapter is **presence of at least one CBDB `ENTRY_DATA` record**. Every rate is a share among CBDB-listed people; it is not an estimate of actual office holding, actual government entry, or the historical Chinese population.

## 1. Dynasty and gender context

| Dynasty | CBDB-listed people | ENTRY-positive | Recorded share |
| --- | --- | --- | --- |
| Qing | 237,423 | 129,499 | 54.54% |
| Ming | 225,403 | 44,915 | 19.93% |
| Song | 83,373 | 40,247 | 48.27% |
| Tang | 57,477 | 1,824 | 3.17% |
| Yuan | 25,310 | 2,331 | 9.21% |

Gender differences are large in the recorded data, but they combine historical structure, database selection, and documentation processes. They are not causal gender effects.

| Population | Gender | People | Recorded share |
| --- | --- | --- | --- |
| Global | female | 58,054 | 1.22% |
| Global | male | 578,833 | 37.96% |
| Global | unknown | 24,237 | 0.79% |
| Song | female | 5,047 | 9.63% |
| Song | male | 78,166 | 50.86% |
| Song | unknown | 160 | 4.38% |
| Ming | female | 36,809 | 0.06% |
| Ming | male | 184,402 | 24.33% |
| Ming | unknown | 4,192 | 0.86% |
| Qing | female | 9,272 | 0.66% |
| Qing | male | 213,754 | 60.52% |
| Qing | unknown | 14,397 | 0.44% |

## 2. ENTRY pathway composition

`entry_category_by_dynasty_records.csv` reports mutually assigned record-level shares. `entry_category_by_dynasty_people.csv` reports non-exclusive unique-person prevalence: one person can have multiple categories, so prevalence can sum above 100%.

See `outputs/phase2_6/figures/final_entry_pathways_by_dynasty.png`.

## 3. Birth information

| Population | Comparison | Δ ROC-AUC | Δ PR-AUC |
| --- | --- | --- | --- |
| Global | B1 - B0 | +0.037830 | +0.070487 |
| Global | B2 - B0 | +0.038984 | +0.075759 |
| Global | B3 - B2 | +0.000142 | +0.000192 |
| Ming | B1 - B0 | +0.103332 | +0.178774 |
| Ming | B2 - B0 | +0.103706 | +0.194849 |
| Ming | B3 - B2 | +0.000231 | +0.001094 |
| Song | B1 - B0 | +0.021212 | +0.017502 |
| Song | B2 - B0 | +0.022688 | +0.025848 |
| Song | B3 - B2 | -0.001179 | -0.001344 |
| Global | B_OBSERVED_1 - B_OBSERVED_0 | +0.024039 | +0.077166 |
| Ming | B_OBSERVED_1 - B_OBSERVED_0 | +0.247604 | +0.058793 |
| Song | B_OBSERVED_1 - B_OBSERVED_0 | +0.079052 | +0.082831 |

The Phase 2.5 P3−P2 result requires a narrower interpretation. In the current CatBoost missing-value mechanism, an explicit missing indicator supplies little additional information after a missing-aware birth value is already present. It does **not** show that birth-year availability has no predictive information by itself.

## 4. Geography: location versus record semantics

| Population | Comparison | Δ ROC-AUC | Δ PR-AUC |
| --- | --- | --- | --- |
| Global | A1 - A0 | +0.046510 | +0.093855 |
| Global | A2 - A1 | +0.018820 | +0.076062 |
| Global | A3 - A2 | +0.000014 | -0.000343 |
| Global | A4 - A3 | +0.008980 | +0.022396 |
| Global | A5 - A4 | +0.000112 | +0.000235 |
| Ming | A1 - A0 | +0.054365 | +0.047488 |
| Ming | A2 - A1 | +0.016509 | +0.090486 |
| Ming | A3 - A2 | +0.000152 | +0.002470 |
| Ming | A4 - A3 | +0.030118 | +0.099341 |
| Ming | A5 - A4 | +0.000160 | -0.000251 |
| Song | A1 - A0 | +0.200425 | +0.147162 |
| Song | A2 - A1 | +0.102003 | +0.166421 |
| Song | A3 - A2 | +0.000311 | +0.000883 |
| Song | A4 - A3 | +0.000514 | +0.001088 |
| Song | A5 - A4 | -0.000367 | -0.001078 |

Address observability, historical administrative categories, continuous coordinates/capital distance, and `addr_type_name` are reported separately. `addr_type_name` is documentation-linked address semantics, not pure physical geography. The matched-support comparison is a spatial distribution-shift sensitivity, not a causal experiment.

## 5. Family: observability, topology, and recorded capital

Phase 2.5 showed that family observability is the dominant family signal and topology adds a smaller increment. The five-seed results below assess whether full-record or train-observed cross-sectional family capital adds stable predictive discrimination.

| Population | Comparison | Mean ΔAUC | SD | Min | Max | Positive seeds | Magnitude |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Global | F3 - F2 | +0.000620 | 0.000086 | +0.000520 | +0.000720 | 5/5 | small |
| Global | F4 - F2 | +0.000329 | 0.000082 | +0.000247 | +0.000457 | 5/5 | small |
| Global | D6 - D5 | +0.000407 | 0.000102 | +0.000270 | +0.000539 | 5/5 | small |
| Global | D6i - D5 | +0.000247 | 0.000177 | +0.000105 | +0.000458 | 5/5 | small |
| Song | F3 - F2 | +0.002295 | 0.000305 | +0.001821 | +0.002674 | 5/5 | not_flagged |
| Song | F4 - F2 | +0.001188 | 0.000306 | +0.000902 | +0.001603 | 5/5 | small |
| Song | D6 - D5 | +0.000803 | 0.000203 | +0.000545 | +0.001088 | 5/5 | small |
| Song | D6i - D5 | +0.000283 | 0.000212 | -0.000074 | +0.000467 | 4/5 | small |
| Ming | F3 - F2 | +0.000496 | 0.000714 | -0.000319 | +0.001189 | 3/5 | small |
| Ming | F4 - F2 | +0.000005 | 0.000440 | -0.000394 | +0.000632 | 2/5 | small |
| Ming | D6 - D5 | +0.000517 | 0.000259 | +0.000216 | +0.000861 | 5/5 | small |
| Ming | D6i - D5 | +0.000241 | 0.000452 | -0.000342 | +0.000685 | 3/5 | small |

F3 is full-record cross-sectional capital; F4/D6i use only relatives observed in training, but remain cross-sectional rather than strict pre-entry measures. Neither supports a strong causal inheritance claim.

## 6. Documentation bias and spatial transport

High AUC and strong documentation bias can coexist. H_STRUCT is the cleaner structural association model, D5_MAIN is the main documentation-linked predictor, and D6_UPPER is a database record-structure upper bound. Their distinct meanings must not be collapsed into one ‘best’ model.

The matched random/spatial results use the identical reliable-prefecture support. Lower spatial performance indicates weaker transport to unseen historical regions; it does not identify a causal geography effect.

## 7. Feature coverage

`final_feature_coverage.csv` distinguishes `non_missing_rate` from `positive_flag_rate`. For binary flags, 100% non-missing means the 0/1 field is complete; it does not mean every person has the recorded characteristic.

## Interpretation rule

SHAP explains model prediction attribution, not causal effect. The final figures and tables consistently refer to ENTRY record presence among CBDB-listed people.
