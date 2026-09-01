# Phase 2 results

This is a database-wide prediction study of CBDB records. Target V1 means **ENTRY_DATA record presence**; it is not proof of actual office holding, a population probability, or a causal outcome. Posting variables denote recorded office-holding/posting outcomes and enter only as relatives' cross-sectional history where registered.

## Dataset

| Population | N | V1 positive | V1 rate |
| --- | --- | --- | --- |
| Global | 661,124 | 220,627 | 0.3337 |
| Song | 83,373 | 40,247 | 0.4827 |
| Ming | 225,403 | 44,915 | 0.1993 |
| Qing | 237,423 | 129,499 | 0.5454 |

Global is a benchmark over people represented in CBDB, not ancient China's general population. Song is the primary comprehensive analysis; Ming is the main family-political-capital comparison; Qing is descriptive only in this first round.

## Feature coverage

| Population | Feature/domain | Observed/present | Coverage | Positive among observed |
| --- | --- | --- | --- | --- |
| Global | safe_birth_year | 59,851 | 0.0905 |  |
| Global | geography | 391,620 | 0.5924 |  |
| Global | geography_coordinates | 382,294 | 0.5782 |  |
| Global | father_identified | 90,894 | 0.1375 |  |
| Global | any_grandfather_identified | 29,100 | 0.0440 |  |
| Global | core_family | 224,394 | 0.3394 |  |
| Global | father_ever_entry_observed | 90,891 | 0.1375 | 0.2651 |
| Global | father_ever_posting_observed | 90,891 | 0.1375 | 0.5345 |
| Global | father_entry_before_birth_observed | 1,927 | 0.0029 | 0.5833 |
| Global | any_older_kin_entry_before_birth_observed | 2,747 | 0.0042 | 0.6909 |
| Song | safe_birth_year | 6,004 | 0.0720 |  |
| Song | geography | 56,411 | 0.6766 |  |
| Song | geography_coordinates | 55,986 | 0.6715 |  |
| Song | father_identified | 19,142 | 0.2296 |  |
| Song | any_grandfather_identified | 4,152 | 0.0498 |  |
| Song | core_family | 28,749 | 0.3448 |  |
| Song | father_ever_entry_observed | 19,142 | 0.2296 | 0.4816 |
| Song | father_ever_posting_observed | 19,142 | 0.2296 | 0.5348 |
| Song | father_entry_before_birth_observed | 918 | 0.0110 | 0.6471 |
| Song | any_older_kin_entry_before_birth_observed | 1,314 | 0.0158 | 0.7405 |
| Ming | safe_birth_year | 14,098 | 0.0625 |  |
| Ming | geography | 105,255 | 0.4670 |  |
| Ming | geography_coordinates | 104,232 | 0.4624 |  |
| Ming | father_identified | 20,177 | 0.0895 |  |
| Ming | any_grandfather_identified | 16,014 | 0.0710 |  |
| Ming | core_family | 115,825 | 0.5139 |  |
| Ming | father_ever_entry_observed | 20,176 | 0.0895 | 0.2636 |
| Ming | father_ever_posting_observed | 20,176 | 0.0895 | 0.4521 |
| Ming | father_entry_before_birth_observed | 332 | 0.0015 | 0.4970 |
| Ming | any_older_kin_entry_before_birth_observed | 467 | 0.0021 | 0.6146 |
| Qing | safe_birth_year | 24,192 | 0.1019 |  |
| Qing | geography | 179,857 | 0.7575 |  |
| Qing | geography_coordinates | 173,599 | 0.7312 |  |
| Qing | father_identified | 12,753 | 0.0537 |  |
| Qing | any_grandfather_identified | 4,260 | 0.0179 |  |
| Qing | core_family | 26,017 | 0.1096 |  |
| Qing | father_ever_entry_observed | 12,753 | 0.0537 | 0.4793 |
| Qing | father_ever_posting_observed | 12,753 | 0.0537 | 0.4780 |
| Qing | father_entry_before_birth_observed | 413 | 0.0017 | 0.5375 |
| Qing | any_older_kin_entry_before_birth_observed | 581 | 0.0024 | 0.6489 |

`father_ever_entry` and related variables are relatives' recorded lifetime histories and are temporally ambiguous. Pre-birth fields require a SAFE focal birth year and a valid relative event year; unknown event years remain missing rather than being recoded as zero.

## LogisticRegression results

| Population | Set | ROC-AUC | PR-AUC | Bal. Acc. | F1 | LogLoss | Brier |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Global | M0 | 0.7398 | 0.5064 | 0.7128 | 0.6267 | 0.5842 | 0.2026 |
| Global | M1 | 0.8297 | 0.6385 | 0.7768 | 0.6980 | 0.4939 | 0.1661 |
| Global | M2 | 0.9004 | 0.8208 | 0.8325 | 0.7728 | 0.3904 | 0.1222 |
| Global | M3 | 0.9131 | 0.8437 | 0.8448 | 0.7876 | 0.3692 | 0.1146 |
| Global | M4 | 0.9138 | 0.8445 | 0.8451 | 0.7881 | 0.3680 | 0.1141 |
| Global | M5 | 0.8229 | 0.6286 | 0.7900 | 0.7179 | 0.4965 | 0.1619 |
| Global | M6 | 0.9160 | 0.8436 | 0.8485 | 0.7924 | 0.3635 | 0.1128 |
| Ming | M0 | 0.5000 | 0.1993 | 0.5000 | 0.3323 | 0.6931 | 0.2500 |
| Ming | M1 | 0.7160 | 0.4383 | 0.6346 | 0.4234 | 0.5351 | 0.1883 |
| Ming | M2 | 0.8157 | 0.6710 | 0.7341 | 0.5725 | 0.4397 | 0.1447 |
| Ming | M3 | 0.8975 | 0.7720 | 0.8011 | 0.6972 | 0.3567 | 0.1130 |
| Ming | M4 | 0.8978 | 0.7727 | 0.8023 | 0.6978 | 0.3562 | 0.1129 |
| Ming | M5 | 0.7819 | 0.4536 | 0.6802 | 0.4517 | 0.5418 | 0.1811 |
| Ming | M6 | 0.9021 | 0.7765 | 0.8020 | 0.6969 | 0.3500 | 0.1126 |
| Song | M0 | 0.5000 | 0.4827 | 0.5000 | 0.6511 | 0.6931 | 0.2500 |
| Song | M1 | 0.5702 | 0.5320 | 0.5474 | 0.6710 | 0.6629 | 0.2372 |
| Song | M2 | 0.8679 | 0.8333 | 0.7969 | 0.8025 | 0.4483 | 0.1443 |
| Song | M3 | 0.8952 | 0.8706 | 0.8252 | 0.8235 | 0.4091 | 0.1275 |
| Song | M4 | 0.8973 | 0.8728 | 0.8279 | 0.8267 | 0.4043 | 0.1252 |
| Song | M5 | 0.8593 | 0.8088 | 0.8018 | 0.8009 | 0.4576 | 0.1443 |
| Song | M6 | 0.9008 | 0.8810 | 0.8333 | 0.8317 | 0.3985 | 0.1223 |

Metrics use the untouched frozen primary test partition and the fixed 0.5 threshold. A separate row in `model_metrics.csv` uses a balanced-accuracy threshold selected on validation only.

## CatBoost results

| Population | Set | ROC-AUC | PR-AUC | Bal. Acc. | F1 | LogLoss | Brier |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Global | M0 | 0.7397 | 0.5062 | 0.7129 | 0.6267 | 0.5840 | 0.2022 |
| Global | M1 | 0.8313 | 0.6397 | 0.7373 | 0.6495 | 0.4544 | 0.1515 |
| Global | M2 | 0.9053 | 0.8315 | 0.8329 | 0.7804 | 0.3532 | 0.1099 |
| Global | M3 | 0.9287 | 0.8677 | 0.8612 | 0.8103 | 0.3349 | 0.1035 |
| Global | M4 | 0.9293 | 0.8686 | 0.8622 | 0.8117 | 0.3332 | 0.1030 |
| Global | M5 | 0.8519 | 0.6818 | 0.8080 | 0.7391 | 0.4579 | 0.1471 |
| Global | M6 | 0.9374 | 0.8831 | 0.8695 | 0.8214 | 0.3140 | 0.0970 |
| Ming | M0 | 0.5000 | 0.1993 | 0.5000 | 0.0000 | 0.4994 | 0.1596 |
| Ming | M1 | 0.7161 | 0.4371 | 0.6348 | 0.4239 | 0.3880 | 0.1218 |
| Ming | M2 | 0.8169 | 0.6762 | 0.7163 | 0.5996 | 0.3214 | 0.0969 |
| Ming | M3 | 0.9114 | 0.7921 | 0.8124 | 0.7113 | 0.3329 | 0.1069 |
| Ming | M4 | 0.9124 | 0.7935 | 0.8141 | 0.7138 | 0.3312 | 0.1063 |
| Ming | M5 | 0.7978 | 0.5327 | 0.6891 | 0.4610 | 0.4969 | 0.1692 |
| Ming | M6 | 0.9170 | 0.8015 | 0.8173 | 0.7281 | 0.3219 | 0.1022 |
| Song | M0 | 0.5000 | 0.4827 | 0.5000 | 0.0000 | 0.6926 | 0.2497 |
| Song | M1 | 0.5692 | 0.5320 | 0.5263 | 0.1674 | 0.6583 | 0.2359 |
| Song | M2 | 0.8719 | 0.8466 | 0.7983 | 0.8031 | 0.4405 | 0.1421 |
| Song | M3 | 0.9164 | 0.9091 | 0.8471 | 0.8419 | 0.3634 | 0.1122 |
| Song | M4 | 0.9185 | 0.9117 | 0.8510 | 0.8457 | 0.3579 | 0.1098 |
| Song | M5 | 0.9150 | 0.8972 | 0.8388 | 0.8389 | 0.3963 | 0.1205 |
| Song | M6 | 0.9396 | 0.9412 | 0.8725 | 0.8671 | 0.3053 | 0.0927 |

Metrics use the untouched frozen primary test partition and the fixed 0.5 threshold. A separate row in `model_metrics.csv` uses a balanced-accuracy threshold selected on validation only.

## Ablation

| Algorithm | Population | Comparison | Δ ROC-AUC | Δ PR-AUC | Δ LogLoss |
| --- | --- | --- | --- | --- | --- |
| LogisticRegression | Global | M2 - M1 | 0.0708 | 0.1824 | -0.1036 |
| LogisticRegression | Global | M3 - M2 | 0.0127 | 0.0229 | -0.0211 |
| LogisticRegression | Global | M4 - M3 | 0.0007 | 0.0007 | -0.0012 |
| LogisticRegression | Global | M6 - M4 | 0.0023 | -0.0009 | -0.0045 |
| LogisticRegression | Song | M2 - M1 | 0.2977 | 0.3013 | -0.2146 |
| LogisticRegression | Song | M3 - M2 | 0.0273 | 0.0372 | -0.0392 |
| LogisticRegression | Song | M4 - M3 | 0.0021 | 0.0023 | -0.0047 |
| LogisticRegression | Song | M6 - M4 | 0.0034 | 0.0082 | -0.0059 |
| LogisticRegression | Ming | M2 - M1 | 0.0997 | 0.2327 | -0.0955 |
| LogisticRegression | Ming | M3 - M2 | 0.0818 | 0.1010 | -0.0830 |
| LogisticRegression | Ming | M4 - M3 | 0.0004 | 0.0006 | -0.0005 |
| LogisticRegression | Ming | M6 - M4 | 0.0042 | 0.0038 | -0.0063 |
| CatBoost | Global | M2 - M1 | 0.0741 | 0.1918 | -0.1012 |
| CatBoost | Global | M3 - M2 | 0.0233 | 0.0362 | -0.0183 |
| CatBoost | Global | M4 - M3 | 0.0007 | 0.0009 | -0.0017 |
| CatBoost | Global | M6 - M4 | 0.0081 | 0.0145 | -0.0192 |
| CatBoost | Song | M2 - M1 | 0.3027 | 0.3147 | -0.2178 |
| CatBoost | Song | M3 - M2 | 0.0444 | 0.0625 | -0.0770 |
| CatBoost | Song | M4 - M3 | 0.0022 | 0.0026 | -0.0056 |
| CatBoost | Song | M6 - M4 | 0.0211 | 0.0295 | -0.0526 |
| CatBoost | Ming | M2 - M1 | 0.1008 | 0.2391 | -0.0665 |
| CatBoost | Ming | M3 - M2 | 0.0945 | 0.1159 | 0.0115 |
| CatBoost | Ming | M4 - M3 | 0.0009 | 0.0014 | -0.0017 |
| CatBoost | Ming | M6 - M4 | 0.0046 | 0.0080 | -0.0093 |

Negative Δ LogLoss indicates improvement. M4 measures incremental information in relatives' recorded cross-sectional political history; it does not identify a causal family effect.

## Documentation bias

| Algorithm | Population | Set | ROC-AUC | PR-AUC | LogLoss |
| --- | --- | --- | --- | --- | --- |
| LogisticRegression | Global | M4 | 0.9138 | 0.8445 | 0.3680 |
| LogisticRegression | Global | M5 | 0.8229 | 0.6286 | 0.4965 |
| LogisticRegression | Global | M6 | 0.9160 | 0.8436 | 0.3635 |
| LogisticRegression | Song | M4 | 0.8973 | 0.8728 | 0.4043 |
| LogisticRegression | Song | M5 | 0.8593 | 0.8088 | 0.4576 |
| LogisticRegression | Song | M6 | 0.9008 | 0.8810 | 0.3985 |
| LogisticRegression | Ming | M4 | 0.8978 | 0.7727 | 0.3562 |
| LogisticRegression | Ming | M5 | 0.7819 | 0.4536 | 0.5418 |
| LogisticRegression | Ming | M6 | 0.9021 | 0.7765 | 0.3500 |
| CatBoost | Global | M4 | 0.9293 | 0.8686 | 0.3332 |
| CatBoost | Global | M5 | 0.8519 | 0.6818 | 0.4579 |
| CatBoost | Global | M6 | 0.9374 | 0.8831 | 0.3140 |
| CatBoost | Song | M4 | 0.9185 | 0.9117 | 0.3579 |
| CatBoost | Song | M5 | 0.9150 | 0.8972 | 0.3963 |
| CatBoost | Song | M6 | 0.9396 | 0.9412 | 0.3053 |
| CatBoost | Ming | M4 | 0.9124 | 0.7935 | 0.3312 |
| CatBoost | Ming | M5 | 0.7978 | 0.5327 | 0.4969 |
| CatBoost | Ming | M6 | 0.9170 | 0.8015 | 0.3219 |

M5's predictive strength demonstrates that CBDB recording structure itself carries substantial target information. M6 should therefore be read as a prediction benchmark with documentation controls, not as a cleaner estimate of historical mobility.

## Family-aware robustness

| Algorithm | Population | Set | Primary AUC | Family AUC | Δ AUC | Δ PR-AUC |
| --- | --- | --- | --- | --- | --- | --- |
| LogisticRegression | Global | M0 | 0.7398 | 0.7404 | 0.0005 | 0.0002 |
| CatBoost | Global | M0 | 0.7397 | 0.7402 | 0.0005 | 0.0002 |
| LogisticRegression | Global | M4 | 0.9138 | 0.9112 | -0.0026 | -0.0006 |
| CatBoost | Global | M4 | 0.9293 | 0.9275 | -0.0019 | -0.0020 |
| LogisticRegression | Ming | M0 | 0.5000 | 0.5000 | 0.0000 | -0.0000 |
| CatBoost | Ming | M0 | 0.5000 | 0.5000 | 0.0000 | -0.0000 |
| LogisticRegression | Ming | M4 | 0.8978 | 0.8942 | -0.0037 | -0.0026 |
| CatBoost | Ming | M4 | 0.9124 | 0.9096 | -0.0028 | -0.0035 |

A decline under the frozen family-group split means part of conventional-split prediction may rely on shared structure among relatives; it is not a model failure. Largest Tang-component exclusion is recorded separately in `robustness_results.csv` without changing the frozen split.

## Pre-birth lineage analysis

| Algorithm | Set | Test N | ROC-AUC | PR-AUC | Δ AUC vs PB0 | Δ PR-AUC vs PB0 |
| --- | --- | --- | --- | --- | --- | --- |
| LogisticRegression | PB0 | 9,066 | 0.8606 | 0.8298 | 0.0000 | 0.0000 |
| CatBoost | PB0 | 9,066 | 0.8623 | 0.8324 | 0.0000 | 0.0000 |
| LogisticRegression | PB1 | 9,066 | 0.8666 | 0.8336 | 0.0060 | 0.0038 |
| CatBoost | PB1 | 9,066 | 0.8696 | 0.8395 | 0.0073 | 0.0071 |

PB1 asks whether recorded lineage political capital already present before a person's birth adds predictive information for that person's later V1 record. It is not a matched pre-entry risk-time design; that design remains a future sensitivity analysis.

## Bootstrap uncertainty

The prespecified first-round bootstrap covers Global M0/M4/M5/M6 test predictions with 500 stratified resamples and seed 42.

| Algorithm | Set | ROC 95% CI | PR 95% CI |
| --- | --- | --- | --- |
| CatBoost | M0 | [0.7367, 0.7425] | [0.5029, 0.5095] |
| CatBoost | M4 | [0.9279, 0.9309] | [0.8659, 0.8714] |
| CatBoost | M5 | [0.8494, 0.8539] | [0.6778, 0.6856] |
| CatBoost | M6 | [0.9360, 0.9388] | [0.8804, 0.8857] |
| LogisticRegression | M0 | [0.7367, 0.7426] | [0.5031, 0.5096] |
| LogisticRegression | M4 | [0.9120, 0.9156] | [0.8411, 0.8478] |
| LogisticRegression | M5 | [0.8203, 0.8253] | [0.6248, 0.6323] |
| LogisticRegression | M6 | [0.9142, 0.9178] | [0.8403, 0.8471] |

## Top model signals (sanity check, not causal effects)

Logistic Global M4 (standardized/one-hot transformed scale):

| Transformed feature | Coefficient | Absolute rank |
| --- | --- | --- |
| categorical__addr_type_name_Household address | 6.8848 | 1 |
| categorical__dynasty_name_Choson | -3.7131 | 2 |
| categorical__dynasty_name_NanBei Chao | -3.5298 | 3 |
| categorical__prefecture_id_700165 | -3.4489 | 4 |
| categorical__safe_birth_decade_1890.0 | -3.4413 | 5 |
| categorical__prefecture_id_700161 | -3.3611 | 6 |
| categorical__prefecture_id_20049 | 3.2959 | 7 |
| categorical__addr_type_name_Birth Address | -3.2421 | 8 |
| categorical__prefecture_id_25999 | 3.0260 | 9 |
| categorical__safe_birth_decade_1880.0 | -2.9532 | 10 |
| categorical__addr_type_name_Eight Banner Qing Dynasty | -2.9466 | 11 |
| categorical__safe_birth_decade_1640.0 | -2.8927 | 12 |

CatBoost Global M4 built-in importance:

| Feature | Importance | Rank |
| --- | --- | --- |
| gender | 25.4972 | 1 |
| dynasty_name | 15.8252 | 2 |
| local_entry_prior | 10.3716 | 3 |
| family_group_size | 7.4829 | 4 |
| addr_type_name | 7.0033 | 5 |
| has_safe_birth_year | 5.2061 | 6 |
| n_known_descendants | 4.6422 | 7 |
| has_core_family | 2.8969 | 8 |
| n_known_core_kin | 2.7001 | 9 |
| prefecture_id | 2.4279 | 10 |
| safe_birth_decade | 2.2860 | 11 |
| n_eligible_older_kin | 1.2875 | 12 |

No SHAP, interaction attribution, network centrality, GNN, or hyperparameter search was run in Phase 2.

## Scientific conclusions

1. Dynasty alone is a strong database-wide baseline (Global M0 ROC-AUC 0.740 Logistic; 0.740 CatBoost), largely reflecting between-dynasty differences in CBDB representation and V1 recording.
2. Geography adds substantial incremental prediction in the Global benchmark (M2−M1 Δ ROC-AUC +0.071 Logistic; +0.074 CatBoost).
3. Family structural fields add further Global information (M3−M2 +0.013 Logistic; +0.023 CatBoost).
4. Cross-sectional family political capital has a smaller conditional Global increment beyond M3 (M4−M3 +0.001 Logistic; +0.001 CatBoost).
5. Documentation-only prediction is substantial (Global M5 ROC-AUC 0.823 Logistic; 0.852 CatBoost), so selection and recording processes are central limitations.
6. Song and Ming estimates differ in magnitude; period-specific models should not be assumed interchangeable.
7. The most negative M4 family-aware change is -0.004 ROC-AUC, quantifying generalization sensitivity when relatives cannot cross partitions.
8. Father's recorded ENTRY history is an association with focal V1 record presence, not evidence that paternal entry caused the focal record.
9. Pre-birth results apply only to the minority with a SAFE birth year and sufficiently dated relative events; sparse coverage limits generalization.
10. All results describe people represented in CBDB and are not estimates of historical population entry or social-mobility rates.

## Next step

Prioritize documentation-bias-controlled modeling before substantive interpretation. SHAP can be run later on locked M4/M6 models, but must be stratified/controlled by documentation intensity and presented as predictive attribution only.
