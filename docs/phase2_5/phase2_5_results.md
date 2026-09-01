# Phase 2.5 — Documentation-Controlled Validation

Target V1 is **ENTRY_DATA record presence**, not actual office-holding probability. All Primary/Family/Temporal IDs and Phase 2 outputs remain frozen. The spatial-group split is a separately labeled robustness design.

## Gender audit and personal decomposition

The actual database field is `BIOG_MAIN.c_female`: 0=male, 1=female, NULL=unknown. No standalone gender code table exists; the mapping is verified against working-database values and the frozen Phase 1 ETL/schema.

| Population | Gender | N | V1 rate | Geo coverage | Kin coverage | Documentation mean |
| --- | --- | --- | --- | --- | --- | --- |
| Global | female | 58,054 | 0.0122 | 0.1650 | 0.8775 | 1.2159 |
| Global | male | 578,833 | 0.3796 | 0.6588 | 0.3758 | 1.2187 |
| Global | unknown | 24,237 | 0.0079 | 0.0295 | 0.7315 | 1.0484 |
| Song | female | 5,047 | 0.0963 | 0.1700 | 0.9558 | 1.4995 |
| Song | male | 78,166 | 0.5086 | 0.7104 | 0.3925 | 1.6486 |
| Song | unknown | 160 | 0.0437 | 0.1562 | 0.5312 | 1.2312 |
| Ming | female | 36,809 | 0.0006 | 0.0369 | 0.9686 | 1.0309 |
| Ming | male | 184,402 | 0.2433 | 0.5631 | 0.6133 | 1.2947 |
| Ming | unknown | 4,192 | 0.0086 | 0.0129 | 0.9342 | 1.0181 |
| Qing | female | 9,272 | 0.0066 | 0.6511 | 0.4994 | 1.7825 |
| Qing | male | 213,754 | 0.6052 | 0.8115 | 0.0819 | 0.9846 |
| Qing | unknown | 14,397 | 0.0044 | 0.0249 | 0.8967 | 1.0258 |

| Population | Comparison | Δ ROC-AUC | Δ PR-AUC | Δ LogLoss |
| --- | --- | --- | --- | --- |
| Global | P1 - P0 | 0.0526 | 0.0580 | -0.0525 |
| Global | P2 - P1 | 0.0388 | 0.0755 | -0.0770 |
| Global | P3 - P2 | 0.0001 | 0.0000 | -0.0001 |
| Ming | P1 - P0 | 0.1120 | 0.0436 | -0.0217 |
| Ming | P2 - P1 | 0.1041 | 0.1943 | 0.0666 |
| Ming | P3 - P2 | -0.0001 | -0.0000 | -0.1564 |
| Song | P1 - P0 | 0.0471 | 0.0248 | -0.0138 |
| Song | P2 - P1 | 0.0206 | 0.0240 | -0.0191 |
| Song | P3 - P2 | 0.0015 | 0.0005 | -0.0013 |

Male-only results are a frozen-split subgroup sensitivity; women and unknown-gender records are not merged into it.

| Population | Model | All AUC | Male AUC | Δ AUC |
| --- | --- | --- | --- | --- |
| Song | P1 | 0.5471 | 0.5000 | -0.0471 |
| Ming | P1 | 0.6120 | 0.5000 | -0.1120 |
| Song | G4 | 0.8722 | 0.8600 | -0.0122 |
| Song | G5 | 0.8722 | 0.8603 | -0.0120 |
| Ming | G4 | 0.8173 | 0.7662 | -0.0511 |
| Ming | G5 | 0.8162 | 0.7640 | -0.0522 |
| Song | F2 | 0.9178 | 0.9108 | -0.0070 |
| Song | F3 | 0.9196 | 0.9130 | -0.0067 |
| Ming | F2 | 0.9122 | 0.8868 | -0.0254 |
| Ming | F3 | 0.9118 | 0.8873 | -0.0245 |
| Song | D0 | 0.9150 | 0.9082 | -0.0068 |
| Song | D6 | 0.9394 | 0.9341 | -0.0053 |
| Ming | D0 | 0.7978 | 0.7476 | -0.0502 |
| Ming | D6 | 0.9171 | 0.8937 | -0.0234 |

## Geography decomposition

| Population | Comparison | Δ ROC-AUC | Δ PR-AUC | Δ LogLoss |
| --- | --- | --- | --- | --- |
| Global | G1 - G0 | 0.0465 | 0.0939 | -0.0587 |
| Global | G2 - G1 | 0.0278 | 0.0984 | -0.0427 |
| Global | G3 - G2 | 0.0001 | -0.0010 | 0.0261 |
| Global | G4 - G3 | 0.0001 | 0.0002 | -0.0003 |
| Global | G5 - G4 | -0.0004 | -0.0003 | 0.0008 |
| Ming | G1 - G0 | 0.0544 | 0.0475 | 0.1297 |
| Ming | G2 - G1 | 0.0477 | 0.1929 | -0.0799 |
| Ming | G3 - G2 | -0.0012 | -0.0003 | -0.0004 |
| Ming | G4 - G3 | 0.0003 | -0.0008 | 0.0033 |
| Ming | G5 - G4 | -0.0011 | -0.0001 | -0.1195 |
| Song | G1 - G0 | 0.2004 | 0.1472 | -0.1497 |
| Song | G2 - G1 | 0.1023 | 0.1667 | -0.0677 |
| Song | G3 - G2 | -0.0001 | 0.0009 | 0.0010 |
| Song | G4 - G3 | 0.0003 | -0.0006 | -0.0014 |
| Song | G5 - G4 | 0.0001 | 0.0009 | 0.0004 |

G1 is address/coordinate observability; G2 historical administrative categories; G3 continuous coordinates/capital distance; G4 train-only unsupervised density; G5 OOF/train-only supervised local target prior. G5−G4 must be interpreted specifically as region-level supervised target information, not physical geography.

## Spatial generalization

| Population | Model | Primary AUC | Spatial AUC | Δ AUC | Δ PR-AUC |
| --- | --- | --- | --- | --- | --- |
| Song | D0 | 0.9150 | 0.8542 | -0.0608 | -0.0061 |
| Global | D0 | 0.8519 | 0.7641 | -0.0878 | -0.0011 |
| Ming | D0 | 0.7978 | 0.7352 | -0.0627 | 0.0738 |
| Ming | D6 | 0.9171 | 0.9328 | 0.0156 | 0.1191 |
| Song | D6 | 0.9394 | 0.8953 | -0.0441 | -0.0099 |
| Global | D6 | 0.9374 | 0.8991 | -0.0384 | -0.0034 |
| Ming | F2 | 0.9122 | 0.9280 | 0.0159 | 0.1202 |
| Song | F2 | 0.9178 | 0.8077 | -0.1102 | -0.0662 |
| Global | F2 | 0.9293 | 0.8694 | -0.0599 | -0.0327 |
| Ming | F3 | 0.9118 | 0.9297 | 0.0179 | 0.1215 |
| Song | F3 | 0.9196 | 0.8152 | -0.1044 | -0.0601 |
| Global | F3 | 0.9300 | 0.8840 | -0.0460 | -0.0152 |
| Ming | G0 | 0.7161 | 0.6725 | -0.0436 | 0.1110 |
| Song | G0 | 0.5692 | 0.5232 | -0.0460 | 0.1012 |
| Global | G0 | 0.8313 | 0.7986 | -0.0327 | 0.0817 |
| Ming | G4 | 0.8173 | 0.7895 | -0.0278 | 0.0975 |
| Song | G4 | 0.8722 | 0.6582 | -0.2140 | -0.1114 |
| Global | G4 | 0.9058 | 0.8394 | -0.0664 | -0.0313 |
| Song | G5 | 0.8722 | 0.6429 | -0.2294 | -0.1341 |
| Global | G5 | 0.9053 | 0.8293 | -0.0760 | -0.0300 |
| Ming | G5 | 0.8162 | 0.8141 | -0.0021 | 0.0996 |

A spatial-holdout decline indicates weaker transfer to entirely unseen dynasty-prefecture groups, not model failure. Unseen local priors fall back to the training global prior.

## Family signal decomposition

| Population | Comparison | Δ ROC-AUC | Δ PR-AUC | Δ LogLoss |
| --- | --- | --- | --- | --- |
| Global | F1 - F0 | 0.0217 | 0.0354 | -0.0414 |
| Global | F2 - F1 | 0.0023 | 0.0024 | -0.0050 |
| Global | F3 - F2 | 0.0007 | 0.0011 | -0.0014 |
| Ming | F1 - F0 | 0.0881 | 0.1060 | 0.0207 |
| Ming | F2 - F1 | 0.0079 | 0.0107 | -0.0095 |
| Ming | F3 - F2 | -0.0003 | 0.0006 | -0.0884 |
| Song | F1 - F0 | 0.0364 | 0.0566 | -0.0616 |
| Song | F2 - F1 | 0.0091 | 0.0078 | -0.0181 |
| Song | F3 - F2 | 0.0018 | 0.0019 | -0.0043 |
| Global | F4 - F2 | 0.0003 | 0.0005 | -0.0006 |
| Ming | F4 - F2 | -0.0004 | 0.0005 | -0.0884 |
| Song | F4 - F2 | 0.0009 | 0.0010 | -0.0026 |

F3 is `full_record_cross_sectional`; F4 is `train_observed_inductive`. Relatives outside the locked training IDs are unknown, never zero. Family-observed/eligible-relative subset results are retained separately.

| Subset | Population | Comparison | Δ ROC-AUC | Δ PR-AUC |
| --- | --- | --- | --- | --- |
| eligible_older_kin | Ming | F2 - F1 | 0.0022 | 0.0011 |
| eligible_older_kin | Ming | F3 - F2 | 0.0006 | 0.0003 |
| family_observed | Ming | F2 - F1 | 0.0112 | 0.0216 |
| family_observed | Ming | F3 - F2 | 0.0004 | 0.0008 |
| eligible_older_kin | Song | F2 - F1 | 0.0425 | 0.0441 |
| eligible_older_kin | Song | F3 - F2 | 0.0150 | 0.0171 |
| family_observed | Song | F2 - F1 | 0.0402 | 0.0552 |
| family_observed | Song | F3 - F2 | 0.0079 | 0.0125 |
| eligible_older_kin | Ming | F4 - F2 | 0.0004 | 0.0002 |
| family_observed | Ming | F4 - F2 | -0.0001 | -0.0008 |
| eligible_older_kin | Song | F4 - F2 | 0.0028 | 0.0037 |
| family_observed | Song | F4 - F2 | 0.0038 | 0.0054 |

## Documentation-controlled ablation

| Algorithm | Population | Comparison | Δ ROC-AUC | Δ PR-AUC | Δ LogLoss |
| --- | --- | --- | --- | --- | --- |
| CatBoost | Global | D1 - D0 | 0.0711 | 0.1496 | -0.1170 |
| CatBoost | Global | D2 - D1 | 0.0103 | 0.0447 | -0.0173 |
| CatBoost | Global | D3 - D2 | -0.0001 | 0.0002 | 0.0001 |
| CatBoost | Global | D4 - D3 | 0.0027 | 0.0049 | -0.0058 |
| CatBoost | Global | D5 - D4 | 0.0011 | 0.0014 | -0.0029 |
| CatBoost | Global | D6 - D5 | 0.0005 | 0.0007 | -0.0010 |
| CatBoost | Ming | D1 - D0 | 0.0934 | 0.1995 | -0.1240 |
| CatBoost | Ming | D2 - D1 | 0.0095 | 0.0425 | -0.0239 |
| CatBoost | Ming | D3 - D2 | 0.0001 | 0.0004 | -0.0011 |
| CatBoost | Ming | D4 - D3 | 0.0105 | 0.0178 | -0.0178 |
| CatBoost | Ming | D5 - D4 | 0.0054 | 0.0079 | -0.0072 |
| CatBoost | Ming | D6 - D5 | 0.0005 | 0.0008 | -0.0019 |
| CatBoost | Song | D1 - D0 | 0.0055 | 0.0089 | -0.0515 |
| CatBoost | Song | D2 - D1 | 0.0116 | 0.0276 | -0.0204 |
| CatBoost | Song | D3 - D2 | -0.0001 | -0.0004 | 0.0001 |
| CatBoost | Song | D4 - D3 | 0.0029 | 0.0033 | -0.0056 |
| CatBoost | Song | D5 - D4 | 0.0035 | 0.0035 | -0.0103 |
| CatBoost | Song | D6 - D5 | 0.0011 | 0.0009 | -0.0028 |
| LogisticRegression | Global | D1 - D0 | 0.0624 | 0.1171 | -0.0862 |
| LogisticRegression | Global | D2 - D1 | 0.0237 | 0.0775 | -0.0317 |
| LogisticRegression | Global | D3 - D2 | 0.0000 | -0.0000 | -0.0000 |
| LogisticRegression | Global | D6 - D5 | 0.0006 | 0.0010 | -0.0012 |
| LogisticRegression | Ming | D1 - D0 | 0.0933 | 0.1775 | -0.1019 |
| LogisticRegression | Ming | D2 - D1 | 0.0096 | 0.0940 | -0.0345 |
| LogisticRegression | Ming | D3 - D2 | 0.0005 | -0.0006 | -0.0030 |
| LogisticRegression | Ming | D6 - D5 | 0.0007 | 0.0016 | -0.0007 |
| LogisticRegression | Song | D1 - D0 | 0.0100 | 0.0191 | -0.0084 |
| LogisticRegression | Song | D2 - D1 | 0.0236 | 0.0372 | -0.0341 |
| LogisticRegression | Song | D3 - D2 | 0.0001 | 0.0008 | -0.0001 |
| LogisticRegression | Song | D6 - D5 | 0.0022 | 0.0037 | -0.0040 |
| CatBoost | Global | D6i - D5 | 0.0001 | 0.0002 | -0.0002 |
| CatBoost | Ming | D6i - D5 | -0.0003 | 0.0007 | -0.0852 |
| CatBoost | Song | D6i - D5 | 0.0004 | -0.0001 | -0.0006 |
| LogisticRegression | Global | D6i - D5 | 0.0004 | 0.0009 | -0.0008 |
| LogisticRegression | Ming | D6i - D5 | 0.0007 | 0.0023 | -0.0014 |
| LogisticRegression | Song | D6i - D5 | 0.0013 | 0.0014 | -0.0027 |
| CatBoost | Global | D5 - D3 | 0.0039 | 0.0062 | -0.0087 |
| CatBoost | Ming | D5 - D3 | 0.0158 | 0.0256 | -0.0250 |
| CatBoost | Song | D5 - D3 | 0.0063 | 0.0068 | -0.0159 |
| LogisticRegression | Global | D5 - D3 | 0.0061 | 0.0189 | -0.0136 |
| LogisticRegression | Ming | D5 - D3 | 0.0160 | 0.0501 | -0.0514 |
| LogisticRegression | Song | D5 - D3 | 0.0053 | 0.0108 | -0.0121 |

D0 establishes a database-recording baseline. D2/D3 isolate raw geography versus supervised local prior; D4/D5 separate family observability/topology; D6 and D6i contrast full-record versus inductive political capital.

## Target sensitivity

| Algorithm | Population | Target | Model | ROC-AUC | PR-AUC | LogLoss |
| --- | --- | --- | --- | --- | --- | --- |
| CatBoost | Global | target_entry_v1 | S0 | 0.9058 | 0.8311 | 0.3789 |
| CatBoost | Global | target_entry_v1 | S1 | 0.9294 | 0.8684 | 0.3332 |
| CatBoost | Global | target_entry_v1 | S2 | 0.9300 | 0.8696 | 0.3321 |
| CatBoost | Global | target_entry_v1 | S2i | 0.9297 | 0.8689 | 0.3328 |
| CatBoost | Global | target_entry_v1 | SD | 0.8519 | 0.6818 | 0.4579 |
| CatBoost | Song | target_entry_v1 | S0 | 0.8722 | 0.8461 | 0.4405 |
| CatBoost | Song | target_entry_v1 | S1 | 0.9177 | 0.9110 | 0.3613 |
| CatBoost | Song | target_entry_v1 | S2 | 0.9192 | 0.9127 | 0.3582 |
| CatBoost | Song | target_entry_v1 | S2i | 0.9189 | 0.9119 | 0.3591 |
| CatBoost | Song | target_entry_v1 | SD | 0.9150 | 0.8972 | 0.3963 |
| CatBoost | Ming | target_entry_v1 | S0 | 0.8173 | 0.6764 | 0.4407 |
| CatBoost | Ming | target_entry_v1 | S1 | 0.9116 | 0.7921 | 0.3322 |
| CatBoost | Ming | target_entry_v1 | S2 | 0.9116 | 0.7931 | 0.2441 |
| CatBoost | Ming | target_entry_v1 | S2i | 0.9123 | 0.7932 | 0.3317 |
| CatBoost | Ming | target_entry_v1 | SD | 0.7978 | 0.5327 | 0.4969 |
| LogisticRegression | Global | target_entry_v1 | S0 | 0.9004 | 0.8208 | 0.3904 |
| LogisticRegression | Global | target_entry_v1 | S1 | 0.9146 | 0.8459 | 0.3662 |
| LogisticRegression | Global | target_entry_v1 | S2 | 0.9153 | 0.8465 | 0.3649 |
| LogisticRegression | Global | target_entry_v1 | SD | 0.8229 | 0.6286 | 0.4965 |
| LogisticRegression | Song | target_entry_v1 | S0 | 0.8675 | 0.8323 | 0.4487 |
| LogisticRegression | Song | target_entry_v1 | S1 | 0.8970 | 0.8750 | 0.4058 |
| LogisticRegression | Song | target_entry_v1 | S2 | 0.8990 | 0.8759 | 0.4015 |
| LogisticRegression | Song | target_entry_v1 | SD | 0.8593 | 0.8088 | 0.4576 |
| LogisticRegression | Ming | target_entry_v1 | S0 | 0.8164 | 0.6724 | 0.4436 |
| LogisticRegression | Ming | target_entry_v1 | S1 | 0.9006 | 0.7728 | 0.3540 |
| LogisticRegression | Ming | target_entry_v1 | S2 | 0.9016 | 0.7745 | 0.3533 |
| LogisticRegression | Ming | target_entry_v1 | SD | 0.7819 | 0.4536 | 0.5418 |
| CatBoost | Global | target_entry_v2a | S0 | 0.8845 | 0.7409 | 0.4168 |
| CatBoost | Global | target_entry_v2a | S1 | 0.9139 | 0.7962 | 0.3660 |
| CatBoost | Global | target_entry_v2a | S2 | 0.9146 | 0.7978 | 0.3647 |
| CatBoost | Global | target_entry_v2a | S2i | 0.9142 | 0.7968 | 0.3654 |
| CatBoost | Global | target_entry_v2a | SD | 0.8135 | 0.4922 | 0.4131 |
| CatBoost | Song | target_entry_v2a | S0 | 0.8714 | 0.8346 | 0.4396 |
| CatBoost | Song | target_entry_v2a | S1 | 0.9214 | 0.9076 | 0.3522 |
| CatBoost | Song | target_entry_v2a | S2 | 0.9228 | 0.9080 | 0.3492 |
| CatBoost | Song | target_entry_v2a | S2i | 0.9223 | 0.9086 | 0.3485 |
| CatBoost | Song | target_entry_v2a | SD | 0.9127 | 0.8881 | 0.5287 |
| CatBoost | Ming | target_entry_v2a | S0 | 0.8507 | 0.7175 | 0.3821 |
| CatBoost | Ming | target_entry_v2a | S1 | 0.9389 | 0.8361 | 0.1760 |
| CatBoost | Ming | target_entry_v2a | S2 | 0.9388 | 0.8360 | 0.1759 |
| CatBoost | Ming | target_entry_v2a | S2i | 0.9386 | 0.8354 | 0.1762 |
| CatBoost | Ming | target_entry_v2a | SD | 0.8247 | 0.5287 | 0.4685 |
| LogisticRegression | Global | target_entry_v2a | S0 | 0.8801 | 0.7317 | 0.4233 |
| LogisticRegression | Global | target_entry_v2a | S1 | 0.8977 | 0.7666 | 0.3960 |
| LogisticRegression | Global | target_entry_v2a | S2 | 0.8989 | 0.7678 | 0.3949 |
| LogisticRegression | Global | target_entry_v2a | SD | 0.7868 | 0.4388 | 0.5454 |
| LogisticRegression | Song | target_entry_v2a | S0 | 0.8682 | 0.8251 | 0.4460 |
| LogisticRegression | Song | target_entry_v2a | S1 | 0.9010 | 0.8734 | 0.3964 |
| LogisticRegression | Song | target_entry_v2a | S2 | 0.9030 | 0.8741 | 0.3914 |
| LogisticRegression | Song | target_entry_v2a | SD | 0.8625 | 0.8191 | 0.4579 |
| LogisticRegression | Ming | target_entry_v2a | S0 | 0.8473 | 0.7095 | 0.3863 |
| LogisticRegression | Ming | target_entry_v2a | S1 | 0.9309 | 0.8201 | 0.2813 |
| LogisticRegression | Ming | target_entry_v2a | S2 | 0.9310 | 0.8200 | 0.2810 |
| LogisticRegression | Ming | target_entry_v2a | SD | 0.8075 | 0.4327 | 0.5174 |
| CatBoost | Global | target_entry_v2b | S0 | 0.8834 | 0.7263 | 0.4194 |
| CatBoost | Global | target_entry_v2b | S1 | 0.9129 | 0.7860 | 0.3686 |
| CatBoost | Global | target_entry_v2b | S2 | 0.9135 | 0.7868 | 0.3676 |
| CatBoost | Global | target_entry_v2b | S2i | 0.9131 | 0.7858 | 0.3683 |
| CatBoost | Global | target_entry_v2b | SD | 0.8103 | 0.4715 | 0.5188 |
| CatBoost | Song | target_entry_v2b | S0 | 0.8745 | 0.8290 | 0.4367 |
| CatBoost | Song | target_entry_v2b | S1 | 0.9225 | 0.9031 | 0.3490 |
| CatBoost | Song | target_entry_v2b | S2 | 0.9239 | 0.9042 | 0.3462 |
| CatBoost | Song | target_entry_v2b | S2i | 0.9238 | 0.9049 | 0.3447 |
| CatBoost | Song | target_entry_v2b | SD | 0.9103 | 0.8768 | 0.5109 |
| CatBoost | Ming | target_entry_v2b | S0 | 0.8504 | 0.7094 | 0.3850 |
| CatBoost | Ming | target_entry_v2b | S1 | 0.9385 | 0.8321 | 0.2664 |
| CatBoost | Ming | target_entry_v2b | S2 | 0.9389 | 0.8327 | 0.2657 |
| CatBoost | Ming | target_entry_v2b | S2i | 0.9387 | 0.8325 | 0.2657 |
| CatBoost | Ming | target_entry_v2b | SD | 0.8240 | 0.5192 | 0.4721 |
| LogisticRegression | Global | target_entry_v2b | S0 | 0.8785 | 0.7157 | 0.4260 |
| LogisticRegression | Global | target_entry_v2b | S1 | 0.8973 | 0.7552 | 0.3977 |
| LogisticRegression | Global | target_entry_v2b | S2 | 0.8980 | 0.7563 | 0.3967 |
| LogisticRegression | Global | target_entry_v2b | SD | 0.7843 | 0.4215 | 0.5483 |
| LogisticRegression | Song | target_entry_v2b | S0 | 0.8711 | 0.8188 | 0.4417 |
| LogisticRegression | Song | target_entry_v2b | S1 | 0.9035 | 0.8691 | 0.3912 |
| LogisticRegression | Song | target_entry_v2b | S2 | 0.9051 | 0.8703 | 0.3870 |
| LogisticRegression | Song | target_entry_v2b | SD | 0.8629 | 0.8090 | 0.4565 |
| LogisticRegression | Ming | target_entry_v2b | S0 | 0.8458 | 0.6944 | 0.3908 |
| LogisticRegression | Ming | target_entry_v2b | S1 | 0.9300 | 0.8159 | 0.2846 |
| LogisticRegression | Ming | target_entry_v2b | S2 | 0.9300 | 0.8162 | 0.2841 |
| LogisticRegression | Ming | target_entry_v2b | SD | 0.8089 | 0.4277 | 0.5193 |
| CatBoost | Global | target_posting | S0 | 0.8466 | 0.8071 | 0.4706 |
| CatBoost | Global | target_posting | S1 | 0.8925 | 0.8586 | 0.4064 |
| CatBoost | Global | target_posting | S2 | 0.8929 | 0.8588 | 0.4081 |
| CatBoost | Global | target_posting | S2i | 0.8928 | 0.8586 | 0.4082 |
| CatBoost | Global | target_posting | SD | 0.7641 | 0.6686 | 0.5714 |
| CatBoost | Song | target_posting | S0 | 0.7880 | 0.6583 | 0.5495 |
| CatBoost | Song | target_posting | S1 | 0.8453 | 0.7417 | 0.4828 |
| CatBoost | Song | target_posting | S2 | 0.8479 | 0.7473 | 0.4798 |
| CatBoost | Song | target_posting | S2i | 0.8471 | 0.7448 | 0.4816 |
| CatBoost | Song | target_posting | SD | 0.8591 | 0.7501 | 0.4434 |
| CatBoost | Ming | target_posting | S0 | 0.7938 | 0.5871 | 0.4942 |
| CatBoost | Ming | target_posting | S1 | 0.8884 | 0.7754 | 0.4130 |
| CatBoost | Ming | target_posting | S2 | 0.8887 | 0.7756 | 0.4129 |
| CatBoost | Ming | target_posting | S2i | 0.8889 | 0.7760 | 0.3792 |
| CatBoost | Ming | target_posting | SD | 0.8215 | 0.7175 | 0.4621 |
| LogisticRegression | Global | target_posting | S0 | 0.8413 | 0.8013 | 0.4850 |
| LogisticRegression | Global | target_posting | S1 | 0.8669 | 0.8308 | 0.4565 |
| LogisticRegression | Global | target_posting | S2 | 0.8684 | 0.8320 | 0.4547 |
| LogisticRegression | Global | target_posting | SD | 0.6800 | 0.5680 | 0.6162 |
| LogisticRegression | Song | target_posting | S0 | 0.7849 | 0.6541 | 0.5548 |
| LogisticRegression | Song | target_posting | S1 | 0.8040 | 0.6905 | 0.5401 |
| LogisticRegression | Song | target_posting | S2 | 0.8112 | 0.6999 | 0.5326 |
| LogisticRegression | Song | target_posting | SD | 0.7865 | 0.6206 | 0.5682 |
| LogisticRegression | Ming | target_posting | S0 | 0.7913 | 0.5834 | 0.5419 |
| LogisticRegression | Ming | target_posting | S1 | 0.8705 | 0.7536 | 0.4472 |
| LogisticRegression | Ming | target_posting | S2 | 0.8707 | 0.7534 | 0.4471 |
| LogisticRegression | Ming | target_posting | SD | 0.7974 | 0.6697 | 0.5230 |
| CatBoost | Global | target_posting | S2p | 0.8945 | 0.8606 | 0.4027 |
| CatBoost | Song | target_posting | S2p | 0.8503 | 0.7493 | 0.4760 |
| CatBoost | Ming | target_posting | S2p | 0.8894 | 0.7768 | 0.3790 |

For the posting target, S2 uses relatives' ENTRY capital; relatives' posting features appear only in the separately labeled S2p sensitivity. No focal posting outcome/count/missingness is a predictor.

## Paired statistical validation

| Split | Comparison | Observed Δ AUC | 95% CI | Fraction >0 | Unit | Small magnitude |
| --- | --- | --- | --- | --- | --- | --- |
| primary | G5−G4 | -0.0004 | [-0.0007, -0.0001] | 0.0000 | stratified_individual | True |
| primary | F2−F1 | 0.0023 | [0.0019, 0.0026] | 1.0000 | stratified_individual | True |
| primary | F3−F2 | 0.0007 | [0.0005, 0.0009] | 1.0000 | stratified_individual | True |
| primary | F4−F2 | 0.0003 | [0.0001, 0.0005] | 1.0000 | stratified_individual | True |
| primary | D6−D5 | 0.0005 | [0.0003, 0.0006] | 1.0000 | stratified_individual | True |
| primary | D6i−D5 | 0.0001 | [-0.0000, 0.0003] | 0.9520 | stratified_individual | True |
| primary | M4−M3 | 0.0007 | [0.0004, 0.0009] | 1.0000 | stratified_individual | True |
| family | F2−F1 | 0.0024 | [0.0019, 0.0029] | 1.0000 | family_group_id | True |
| family | F3−F2 | 0.0007 | [0.0003, 0.0012] | 1.0000 | family_group_id | True |
| family | F4−F2 | -0.0011 | [-0.0016, -0.0006] | 0.0000 | family_group_id | True |
| spatial | G5−G4 | -0.0100 | [-0.0178, -0.0006] | 0.0220 | spatial_group_id | False |

A statistically stable ∼0.001 AUC difference remains practically small; statistical sign stability is not substantive importance.

## Calibration

| Population | Model | Variant | Calibration | Brier | LogLoss | ECE | Mean−rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Global | G5 | balanced | raw | 0.1186 | 0.3797 | 0.0784 | 0.0784 |
| Global | G5 | balanced | validation_sigmoid | 0.1099 | 0.3532 | 0.0022 | -0.0001 |
| Global | F2 | balanced | raw | 0.1030 | 0.3333 | 0.0681 | 0.0681 |
| Global | F2 | balanced | validation_sigmoid | 0.0959 | 0.3104 | 0.0040 | -0.0007 |
| Global | F3 | balanced | raw | 0.1026 | 0.3319 | 0.0680 | 0.0680 |
| Global | F3 | balanced | validation_sigmoid | 0.0954 | 0.3089 | 0.0038 | -0.0006 |
| Global | D0 | balanced | raw | 0.1471 | 0.4579 | 0.0975 | 0.0975 |
| Global | D0 | balanced | validation_sigmoid | 0.1357 | 0.4243 | 0.0012 | -0.0001 |
| Global | D6 | balanced | raw | 0.0970 | 0.3140 | 0.0647 | 0.0647 |
| Global | D6 | balanced | validation_sigmoid | 0.0900 | 0.2921 | 0.0034 | -0.0011 |
| Global | D6i | balanced | raw | 0.0973 | 0.3148 | 0.0649 | 0.0649 |
| Global | D6i | balanced | validation_sigmoid | 0.0903 | 0.2928 | 0.0037 | -0.0009 |
| Song | G5 | balanced | raw | 0.1424 | 0.4409 | 0.0183 | 0.0149 |
| Song | G5 | balanced | validation_sigmoid | 0.1420 | 0.4401 | 0.0107 | 0.0035 |
| Song | F2 | balanced | raw | 0.1116 | 0.3613 | 0.0120 | 0.0116 |
| Song | F2 | balanced | validation_sigmoid | 0.1113 | 0.3607 | 0.0071 | 0.0014 |
| Song | F3 | balanced | raw | 0.1097 | 0.3570 | 0.0115 | 0.0114 |
| Song | F3 | balanced | validation_sigmoid | 0.1095 | 0.3565 | 0.0099 | 0.0021 |
| Song | D0 | balanced | raw | 0.1205 | 0.3963 | 0.0865 | 0.0211 |
| Song | D0 | balanced | validation_sigmoid | 0.1115 | 0.3579 | 0.0043 | 0.0022 |
| Song | D6 | unweighted | raw | 0.0929 | 0.3057 | 0.0083 | 0.0032 |
| Song | D6 | unweighted | validation_sigmoid | 0.0929 | 0.3057 | 0.0073 | -0.0001 |
| Song | D6i | balanced | raw | 0.0938 | 0.3079 | 0.0112 | 0.0098 |
| Song | D6i | balanced | validation_sigmoid | 0.0935 | 0.3074 | 0.0084 | -0.0002 |
| Ming | G5 | unweighted | raw | 0.0968 | 0.3211 | 0.0029 | 0.0004 |
| Ming | G5 | unweighted | validation_sigmoid | 0.0968 | 0.3210 | 0.0011 | 0.0009 |
| Ming | F2 | balanced | raw | 0.1066 | 0.3323 | 0.1399 | 0.1399 |
| Ming | F2 | balanced | validation_sigmoid | 0.0735 | 0.2448 | 0.0033 | 0.0002 |
| Ming | F3 | unweighted | raw | 0.0732 | 0.2439 | 0.0035 | 0.0003 |
| Ming | F3 | unweighted | validation_sigmoid | 0.0732 | 0.2439 | 0.0041 | -0.0000 |
| Ming | D0 | balanced | raw | 0.1692 | 0.4969 | 0.2063 | 0.2063 |
| Ming | D0 | balanced | validation_sigmoid | 0.1128 | 0.3626 | 0.0040 | -0.0000 |
| Ming | D6 | balanced | raw | 0.1019 | 0.3211 | 0.1347 | 0.1347 |
| Ming | D6 | balanced | validation_sigmoid | 0.0708 | 0.2376 | 0.0021 | 0.0002 |
| Ming | D6i | unweighted | raw | 0.0708 | 0.2378 | 0.0033 | 0.0004 |
| Ming | D6i | unweighted | validation_sigmoid | 0.0708 | 0.2378 | 0.0029 | 0.0004 |

Sigmoid diagnostics are fitted on validation only and evaluated on test. Balanced class weights can shift probability levels even when ranking metrics improve; raw probabilities should not automatically be treated as calibrated historical probabilities.

## Candidate models — no automatic SHAP lock

| Candidate | Model | Interpretation | SHAP status |
| --- | --- | --- | --- |
| historical_raw_candidate | G4 | Personal plus raw historical geography and train-only unsupervised regional density. | candidate_pending_human_review |
| documentation_controlled_candidate | D6i | Documentation-controlled model with train-observed inductive family capital. | candidate_pending_human_review |
| record_structure_upper_bound | D6 | Upper-bound predictor using documentation and full-record cross-sectional family outcomes. | no_without_explicit_record_structure_framing |

No formal SHAP, GNN, PageRank, Optuna, Bayesian optimization, or large grid search was run. Candidate selection requires human review, with the record-structure upper bound unsuitable for substantive interpretation unless explicitly framed as database recording prediction.
