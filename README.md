# CBDB Phase 2: Predicting Recorded Entry-Data Presence

> Final report generated from the frozen CBDB foundation and the locked Phase 2 outputs.

## Executive Summary

This project predicts whether a person appears in `ENTRY_DATA` at least once. The target is a database-record presence label, not proof that a historical person actually held office or that a person without a record never entered government.

The primary benchmark uses the frozen dynasty-by-target split (seed 42). Logistic Regression and CatBoost use train-only preprocessing; CatBoost class weighting is selected on validation only. Test metrics below use the fixed 0.5 threshold unless otherwise noted.

## Reproduction

Run the complete Phase 2 pipeline from the project root:

```bash
bash scripts/run_phase2.sh
```

The pipeline uses the frozen Phase 1.5 foundation and writes features, predictions, models, result tables, figures, the report, and the final invariant manifest.

## Data Sources

- [Official CBDB SQLite repository](https://github.com/cbdb-project/cbdb_sqlite)
- [CBDB download page](https://projects.iq.harvard.edu/chinesecbdb/%E4%B8%8B%E8%BC%89cbdb%E5%96%AE%E6%A9%9F%E7%89%88)
- [CBDB Chinese user guide](https://projects.iq.harvard.edu/files/cbdb/files/cbdb_users_guide_ch_20210322.pdf)

## Dataset

The retained master table contains **661,124** unique people and **220,627** V1 positives (33.37%). V2a/V2b and posting are auxiliary sensitivity outcomes and are not predictors.

| Population | N | V1 positive | V1 rate | V2a positive | V2a rate | Posting rate |
| --- | --- | --- | --- | --- | --- | --- |
| Global | 661,124 | 220,627 | 33.37% | 155,531 | 23.53% | 45.23% |
| Song | 83,373 | 40,247 | 48.27% | 38,736 | 46.46% | 37.30% |
| Ming | 225,403 | 44,915 | 19.93% | 36,165 | 16.04% | 32.65% |
| Qing | 237,423 | 129,499 | 54.54% | 75,740 | 31.90% | 62.11% |

Global is a database-wide benchmark and must not be described as the historical population of China. Song is relatively balanced and has the strongest address coverage among the principal populations. Ming has a lower V1 rate and stronger kin coverage. Qing is used here for external and temporal comparison rather than as a full primary model population.

## Feature Coverage

| Group | Representative feature | Global | Song | Ming | Qing |
| --- | --- | --- | --- | --- | --- |
| Personal | gender | 100.00% | 100.00% | 100.00% | 100.00% |
| Personal | safe_birth_year | 9.05% | 7.20% | 6.25% | 10.19% |
| Geography | has_geography | 100.00% | 100.00% | 100.00% | 100.00% |
| Geography | latitude | 57.82% | 67.15% | 46.24% | 73.12% |
| Family structural | father_identified | 100.00% | 100.00% | 100.00% | 100.00% |
| Family structural | paternal_grandfather_identified | 100.00% | 100.00% | 100.00% | 100.00% |
| Family capital | father_ever_entry | 13.75% | 22.96% | 8.95% | 5.37% |
| Family capital | paternal_grandfather_ever_entry | 4.37% | 4.93% | 7.09% | 1.75% |
| Pre-birth lineage | father_entry_before_birth | 0.29% | 1.10% | 0.15% | 0.17% |
| Pre-birth lineage | any_older_kin_entry_before_birth | 0.42% | 1.58% | 0.21% | 0.24% |
| Documentation | documentation_intensity | 100.00% | 100.00% | 100.00% | 100.00% |

Family lifetime `ever_*` features are cross-sectional and temporally ambiguous. Pre-birth lineage features require a valid SAFE birth year and a relative event year strictly earlier than that birth year; missing relative event years remain missing.

## Primary Model Results

### Logistic Regression

| Population | Set | ROC-AUC | PR-AUC | Balanced acc. | F1 | Log loss |
| --- | --- | --- | --- | --- | --- | --- |
| Global | M0 | 0.7398 | 0.5064 | 0.7128 | 0.6267 | 0.5842 |
| Global | M0b | 0.7842 | 0.5810 | 0.7459 | 0.6626 | 0.5444 |
| Global | M1 | 0.8297 | 0.6385 | 0.7768 | 0.6980 | 0.4939 |
| Global | M2 | 0.9004 | 0.8208 | 0.8325 | 0.7728 | 0.3904 |
| Global | M3 | 0.9131 | 0.8437 | 0.8448 | 0.7876 | 0.3692 |
| Global | M4 | 0.9138 | 0.8445 | 0.8451 | 0.7881 | 0.3680 |
| Global | M5 | 0.8229 | 0.6286 | 0.7900 | 0.7179 | 0.4965 |
| Global | M6 | 0.9160 | 0.8436 | 0.8485 | 0.7924 | 0.3635 |
| Song | M0 | 0.5000 | 0.4827 | 0.5000 | 0.6511 | 0.6931 |
| Song | M0b | 0.5270 | 0.5081 | 0.5264 | 0.1743 | 0.6874 |
| Song | M1 | 0.5702 | 0.5320 | 0.5474 | 0.6710 | 0.6629 |
| Song | M2 | 0.8679 | 0.8333 | 0.7969 | 0.8025 | 0.4483 |
| Song | M3 | 0.8952 | 0.8706 | 0.8252 | 0.8235 | 0.4091 |
| Song | M4 | 0.8973 | 0.8728 | 0.8279 | 0.8267 | 0.4043 |
| Song | M5 | 0.8593 | 0.8088 | 0.8018 | 0.8009 | 0.4576 |
| Song | M6 | 0.9008 | 0.8810 | 0.8333 | 0.8317 | 0.3985 |
| Ming | M0 | 0.5000 | 0.1993 | 0.5000 | 0.3323 | 0.6931 |
| Ming | M0b | 0.6354 | 0.4072 | 0.6348 | 0.4237 | 0.5803 |
| Ming | M1 | 0.7160 | 0.4383 | 0.6346 | 0.4234 | 0.5351 |
| Ming | M2 | 0.8157 | 0.6710 | 0.7341 | 0.5725 | 0.4397 |
| Ming | M3 | 0.8975 | 0.7720 | 0.8011 | 0.6972 | 0.3567 |
| Ming | M4 | 0.8978 | 0.7727 | 0.8023 | 0.6978 | 0.3562 |
| Ming | M5 | 0.7819 | 0.4536 | 0.6802 | 0.4517 | 0.5418 |
| Ming | M6 | 0.9021 | 0.7765 | 0.8020 | 0.6969 | 0.3500 |

### CatBoost

| Population | Set | ROC-AUC | PR-AUC | Balanced acc. | F1 | Log loss |
| --- | --- | --- | --- | --- | --- | --- |
| Global | M0 | 0.7397 | 0.5062 | 0.7129 | 0.6267 | 0.5840 |
| Global | M0b | 0.7851 | 0.5820 | 0.7109 | 0.6162 | 0.5026 |
| Global | M1 | 0.8313 | 0.6397 | 0.7373 | 0.6495 | 0.4544 |
| Global | M2 | 0.9053 | 0.8315 | 0.8329 | 0.7804 | 0.3532 |
| Global | M3 | 0.9287 | 0.8677 | 0.8612 | 0.8103 | 0.3349 |
| Global | M4 | 0.9293 | 0.8686 | 0.8622 | 0.8117 | 0.3332 |
| Global | M5 | 0.8519 | 0.6818 | 0.8080 | 0.7391 | 0.4579 |
| Global | M6 | 0.9374 | 0.8831 | 0.8695 | 0.8214 | 0.3140 |
| Song | M0 | 0.5000 | 0.4827 | 0.5000 | 0.0000 | 0.6926 |
| Song | M0b | 0.5264 | 0.5070 | 0.5262 | 0.1747 | 0.6871 |
| Song | M1 | 0.5692 | 0.5320 | 0.5263 | 0.1674 | 0.6583 |
| Song | M2 | 0.8719 | 0.8466 | 0.7983 | 0.8031 | 0.4405 |
| Song | M3 | 0.9164 | 0.9091 | 0.8471 | 0.8419 | 0.3634 |
| Song | M4 | 0.9185 | 0.9117 | 0.8510 | 0.8457 | 0.3579 |
| Song | M5 | 0.9150 | 0.8972 | 0.8388 | 0.8389 | 0.3963 |
| Song | M6 | 0.9396 | 0.9412 | 0.8725 | 0.8671 | 0.3053 |
| Ming | M0 | 0.5000 | 0.1993 | 0.5000 | 0.0000 | 0.4994 |
| Ming | M0b | 0.6354 | 0.4057 | 0.6348 | 0.4237 | 0.5811 |
| Ming | M1 | 0.7161 | 0.4371 | 0.6348 | 0.4239 | 0.3880 |
| Ming | M2 | 0.8169 | 0.6762 | 0.7163 | 0.5996 | 0.3214 |
| Ming | M3 | 0.9114 | 0.7921 | 0.8124 | 0.7113 | 0.3329 |
| Ming | M4 | 0.9124 | 0.7935 | 0.8141 | 0.7138 | 0.3312 |
| Ming | M5 | 0.7978 | 0.5327 | 0.6891 | 0.4610 | 0.4969 |
| Ming | M6 | 0.9170 | 0.8015 | 0.8173 | 0.7281 | 0.3219 |

CatBoost M6 reaches ROC-AUC values of 0.9374 (Global), 0.9396 (Song), and 0.9170 (Ming), compared with Logistic M6 values of 0.9160, 0.9008, and 0.9021.

## Feature Ablation

The following paired comparisons use CatBoost primary test predictions. Confidence intervals are paired bootstrap intervals with the configured 500 resamples. Positive ROC-AUC and PR-AUC deltas indicate improved ranking; a negative log-loss delta indicates improved probabilistic accuracy.

| Population | Comparison | Block | Delta ROC-AUC | 95% CI | Delta PR-AUC | Delta log loss |
| --- | --- | --- | --- | --- | --- | --- |
| Global | M1 -> M2 | geography | 0.0741 | [0.0723, 0.0757] | 0.1918 | -0.1012 |
| Global | M2 -> M3 | family_structure | 0.0233 | [0.0224, 0.0243] | 0.0362 | -0.0183 |
| Global | M3 -> M4 | family_capital | 0.0007 | [0.0004, 0.0009] | 0.0009 | -0.0017 |
| Global | M4 -> M6 | documentation_addition | 0.0081 | [0.0076, 0.0087] | 0.0145 | -0.0192 |
| Ming | M1 -> M2 | geography | 0.1008 | [0.0961, 0.1063] | 0.2391 | -0.0665 |
| Ming | M2 -> M3 | family_structure | 0.0945 | [0.0895, 0.0994] | 0.1159 | 0.0115 |
| Ming | M3 -> M4 | family_capital | 0.0009 | [0.0004, 0.0014] | 0.0014 | -0.0017 |
| Ming | M4 -> M6 | documentation_addition | 0.0046 | [0.0036, 0.0058] | 0.0080 | -0.0093 |
| Song | M1 -> M2 | geography | 0.3027 | [0.2952, 0.3100] | 0.3147 | -0.2178 |
| Song | M2 -> M3 | family_structure | 0.0444 | [0.0407, 0.0482] | 0.0625 | -0.0770 |
| Song | M3 -> M4 | family_capital | 0.0022 | [0.0012, 0.0030] | 0.0026 | -0.0056 |
| Song | M4 -> M6 | documentation_addition | 0.0211 | [0.0186, 0.0236] | 0.0295 | -0.0526 |

For CatBoost, the geography increment M2-M1 is 0.0741 ROC-AUC in Global, 0.3027 in Song, and 0.1008 in Ming. The family-structure increment M3-M2 is 0.0233, 0.0444, and 0.0945 respectively. The family-capital increment M4-M3 is 0.0007, 0.0022, and 0.0009.

## Documentation Bias

M5 contains only domain-presence and documentation-intensity variables. It is a diagnostic for recording structure, not a historical mechanism. M6 combines the historical feature set with these recording variables.

The primary tables show that M5 alone can be strong, especially in Song. The improvement from M4 to M6 therefore should not be interpreted as a purely historical gain; it may partly reflect which people and relations CBDB records more completely.

## Robustness

### Family-Group Split

| Population | Set | Primary AUC | Family AUC | Change | Family test N |
| --- | --- | --- | --- | --- | --- |
| Global | M4 | 0.9138 | 0.9112 | -0.0026 | 99,169 |
| Global | M6 | 0.9160 | 0.9139 | -0.0022 | 99,169 |
| Ming | M4 | 0.8978 | 0.8942 | -0.0037 | 33,810 |
| Ming | M6 | 0.9021 | 0.8990 | -0.0031 | 33,810 |
| Song | M4 | 0.8973 | 0.8939 | -0.0034 | 12,506 |
| Song | M6 | 0.9008 | 0.8973 | -0.0034 | 12,506 |

For the M6 Logistic model, the family-group split changes ROC-AUC by -0.0022 in Global, -0.0034 in Song, and -0.0031 in Ming relative to the primary split. This is a generalization check across whole core-family groups, not a replacement for the primary benchmark.

### SAFE Temporal Sensitivity

| Population | Set | Temporal test ROC-AUC | Test N |
| --- | --- | --- | --- |
| Global | M4 | 0.6981 | 8,963 |
| Global | M6 | 0.7395 | 8,963 |
| Qing | M4 | 0.6992 | 5,892 |
| Qing | M6 | 0.6962 | 5,892 |

The SAFE temporal support audit shows that only Global, Qing have all three partitions. Song and Ming are explicitly skipped because their SAFE people fall entirely in the temporal training partition.

The temporal split is restricted to the small SAFE birth-year subset. Calendar time, dynasty composition, source composition, and recording practice shift together, so it is a distribution-shift sensitivity analysis rather than a clean causal time experiment.

### Qing Holdout

The Qing holdout trains on Song/Yuan/Ming source people using frozen primary train/validation assignments and evaluates all Qing people. It measures transport across institutional regimes.

| Set | Qing holdout ROC-AUC | PR-AUC | Qing test N |
| --- | --- | --- | --- |
| M0 | 0.5000 | 0.5454 | 237,423 |
| M2 | 0.6952 | 0.6168 | 237,423 |
| M4 | 0.7198 | 0.6445 | 237,423 |
| M6 | 0.7265 | 0.6549 | 237,423 |

### Pre-birth Lineage

| Population | Set | ROC-AUC | PR-AUC | Safe-birth test N |
| --- | --- | --- | --- | --- |
| Global | PB0 | 0.8608 | 0.8298 | 9,066 |
| Global | PB1 | 0.8664 | 0.8335 | 9,066 |
| Ming | PB0 | 0.7630 | 0.9452 | 2,127 |
| Ming | PB1 | 0.7648 | 0.9458 | 2,127 |
| Qing | PB0 | 0.5912 | 0.3088 | 3,679 |
| Qing | PB1 | 0.6080 | 0.3602 | 3,679 |
| Song | PB0 | 0.6202 | 0.7595 | 925 |
| Song | PB1 | 0.6556 | 0.7886 | 925 |

PB1 is a sensitivity analysis for recorded political capital already present before the focal person's birth. Its coverage is very low, so any difference from PB0 should be treated as suggestive and not as a population-wide estimate.

## Uncertainty

| Algorithm | Population | ROC-AUC | ROC 95% CI | PR-AUC | PR 95% CI | B |
| --- | --- | --- | --- | --- | --- | --- |
| CatBoost | Global | 0.9374 | [0.9359, 0.9390] | 0.8831 | [0.8802, 0.8860] | 500 |
| LogisticRegression | Global | 0.9160 | [0.9141, 0.9180] | 0.8436 | [0.8399, 0.8471] | 500 |
| CatBoost | Ming | 0.9170 | [0.9136, 0.9208] | 0.8015 | [0.7946, 0.8092] | 500 |
| LogisticRegression | Ming | 0.9021 | [0.8981, 0.9060] | 0.7765 | [0.7691, 0.7835] | 500 |
| CatBoost | Song | 0.9396 | [0.9353, 0.9440] | 0.9412 | [0.9368, 0.9457] | 500 |
| LogisticRegression | Song | 0.9008 | [0.8948, 0.9064] | 0.8810 | [0.8720, 0.8896] | 500 |

Primary-model intervals use stratified bootstrap resampling of positive and negative test rows. Ablation intervals are paired on the same frozen test IDs. These intervals reflect test-set sampling uncertainty and do not account for database coverage bias or target-definition uncertainty.

## Top Features

### CatBoost Global/M6

| Feature | Importance | Rank |
| --- | --- | --- |
| gender | 21.679 | 1 |
| dynasty_name | 16.449 | 2 |
| local_entry_prior | 9.132 | 3 |
| documentation_intensity | 7.060 | 4 |
| has_kin | 6.636 | 5 |
| has_safe_birth_year | 6.115 | 6 |
| family_group_size | 5.355 | 7 |
| addr_type_name | 4.982 | 8 |
| has_status | 2.954 | 9 |
| prefecture_id | 2.275 | 10 |

### Logistic Global/M6

| Transformed feature | Coefficient | Absolute rank |
| --- | --- | --- |
| categorical__addr_type_name_Household address | 6.792 | 1 |
| categorical__dynasty_name_Choson | -3.713 | 2 |
| categorical__prefecture_id_700161 | -3.373 | 3 |
| categorical__prefecture_id_700165 | -3.312 | 4 |
| categorical__dynasty_name_NanBei Chao | -3.296 | 5 |
| categorical__prefecture_id_20049 | 3.269 | 6 |
| categorical__addr_type_name_Birth Address | -3.251 | 7 |
| categorical__safe_birth_decade_1890.0 | -3.213 | 8 |
| categorical__prefecture_id_25999 | 3.197 | 9 |
| categorical__addr_type_name_Eight Banner Qing Dynasty | -2.913 | 10 |
| categorical__safe_birth_decade_1640.0 | -2.838 | 11 |
| categorical__safe_birth_decade_1880.0 | -2.810 | 12 |

Coefficients and importances are predictive associations. They should not be read as causal effects, and lifetime family variables should not be described as definitely available before the focal person's own entry.

## Figures

- [Primary ROC-AUC comparison](outputs/phase2/figures/phase2_primary_auc.png)
- [Ablation deltas](outputs/phase2/figures/phase2_ablation_delta.png)
- [Family and temporal robustness](outputs/phase2/figures/phase2_robustness_auc.png)
- [Top CatBoost features](outputs/phase2/figures/phase2_feature_importance.png)
- [Population context](outputs/phase2/figures/phase2_population_context.png)
- [Bootstrap intervals](outputs/phase2/figures/phase2_bootstrap_ci.png)

## Scientific Conclusions

1. The current target measures recorded presence in CBDB `ENTRY_DATA`, so all results describe documentation-linked prediction rather than a verified historical office-holding rate.
2. Dynasty and SAFE birth-cohort information provide a useful baseline, but the largest primary gain is geographic: CatBoost increases Global ROC-AUC from 0.831 at M1 to 0.905 at M2.
3. Family structure adds substantial predictive information after geography, with Global CatBoost ROC-AUC rising from 0.9053 to 0.9287.
4. Cross-sectional family political capital adds a smaller incremental gain in Global, from 0.9287 to 0.9293; its lifetime timing is ambiguous.
5. Documentation-only features are often strong, so the historical interpretation of M6 must be separated from database recording intensity.
6. CatBoost generally outperforms the linear model on the same frozen primary test set, indicating useful nonlinearities and categorical interactions, but this does not establish transport to undocumented people.
7. Family-group and temporal sensitivities are the relevant checks for generalization; their estimates should be read separately from the primary random-within-dynasty benchmark.
8. Pre-birth lineage results are limited by approximately 9% SAFE birth-year coverage and much lower valid relative-event coverage, so they are robustness evidence rather than a broad estimate of inherited political capital.

## Limitations and Next Steps

The database is a selective historical source, dynasty composition is uneven, and `ENTRY_DATA` is not a complete census of entry into government. Cross-sectional family outcomes can include events after the focal person's entry. The current pre-birth design is not the future matched case-control risk-time design. Network centrality, SHAP, GNNs, and large hyperparameter searches were intentionally excluded from this phase.

The full Phase 2 invariant check records the final status after all tables, figures, report sections, and frozen-split checks are present.

Configuration: `configs/phase2_models.yaml`, bootstrap resamples = 500, seed = 42.
