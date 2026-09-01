# Final claim--evidence map

| claim_id | paper_section | claim_text | evidence_type | source_table_or_reference | supported | caveat |
| --- | --- | --- | --- | --- | --- | --- |
| C01 | Data and Measurement Problem | The estimand is Pr(E=1\|X), not Pr(T=1\|X). | database definition | BIOG_MAIN; ENTRY_DATA; paper Figure 1 | YES | T is latent and E is a heterogeneous record-presence proxy. |
| C02 | Data and Measurement Problem | E, P, and T are not semantically equivalent. | construct audit | entry_vs_posting_contingency.csv; Fuller 2024 | YES | Neither observed relation is complete historical ground truth. |
| C03 | Experimental Results | Global D5_MAIN reaches ROC-AUC 0.936956 and PR-AUC 0.882535. | frozen test metrics | final_metric_recomputation.csv; Table 3 | YES | Retrospective record-presence prediction only. |
| C04 | Experimental Results | D6_UPPER improves only marginally over D5_MAIN. | frozen model comparison | final_metric_recomputation.csv; Table 3 | YES | D6 uses temporally ambiguous relatives' lifetime outcomes. |
| C05 | Ablation | Gender, address observability, administrative geography, and family observability provide the largest conditional increments. | grouped ablation | grouped_ablation_corrected.csv; Figure 5 | YES | Increment order is conditional on the frozen nesting. |
| C06 | Ablation | No exact interval is reported for A3-A2 Physical Geography. | artifact audit | statistical_correction_manifest.csv; Table 4 | YES | Exact paired A2/A3 predictions were not retained. |
| C07 | Family Decomposition | Recorded family political capital adds little after observability and topology. | paired ablation and five-seed stability | grouped_ablation_corrected.csv; multiseed_delta_summary.csv | YES | Small positive increments are not evidence of a causal mechanism. |
| C08 | Distribution Shift | Discrimination weakens on matched-support unseen historical regions. | matched-support spatial test | matched_random_vs_spatial_results.csv; Figure 6 | YES | The random and spatial tests share support, not identical people. |
| C09 | Robustness | Full-coverage source grouping is infeasible under the prespecified component protocol. | feasibility gate | source_holdout_status.json; Table 5 | YES | This does not rule out a selective, narrower source subset. |
| C10 | Model Interpretation | SHAP shares are attribution, not independent gains or causal effects. | method literature and empirical contrast | Lundberg and Lee 2017; Kumar et al. 2020; Figure 8 | YES | Correlated and substitutable features redistribute attribution. |
| C11 | Calibration | Reported ECE uses a validation-fitted sigmoid, whereas Table 3 log loss and Brier are raw. | calibration audit | raw_vs_validation_calibrated_metrics.csv; Table 3 | YES | Calibration may not transport under shift. |
| C12 | Limitations | SAFE birth year covers 9.05% of CBDB-covered people. | frozen coverage summary | final_feature_coverage.csv | YES | Broad prospective temporal anchoring is not available. |
| C13 | Limitations | The primary test was viewed across project phases. | workflow disclosure | Phase 1--3 reports | YES | This creates researcher-adaptation risk despite no test-set tuning. |
| C14 | Data Availability | Raw and working CBDB SQLite files are not redistributed. | package and licence audit | data_availability_inventory.csv; DATA_USAGE.md | YES | Users must obtain CBDB through official channels. |
| C15 | Related Work | CBDB supports relational, network, and spatial prosopographical analysis. | verified literature | Bol 2012; Fuller and Wang 2021; Chen and Wang 2022 | YES | The sources do not imply complete historical coverage. |

## Phase 3.1.1 additions and scope corrections

| claim_id | claim_type | final claim | evidence | boundary |
| --- | --- | --- | --- | --- |
| P311-01 | Data snapshot scope | The assignment brief and verified release have different person counts; every result uses cbdb_20260829.sqlite3 with 661,124 BIOG_MAIN rows. | README.md; Section 3; Data Availability; baseline_sha256.tsv | Release-specific count, not a claim that either count is universally correct. |
| P311-02 | T/E/P boundary | T is latent true historical entry; entry-related events, posting events, E, and P are distinct constructs. | Figure 1; entry_vs_posting_contingency.csv; target audit | E and P are incomplete observed relations and are not interchangeable with T. |
| P311-03 | Local target prior | local_target_prior uses exact addr_id groups, alpha=20, five-fold deterministic OOF training encoding, and training-mean fallback. | local_target_prior_spec.json; src/geography.py; configs/phase2_6_features.yaml; method tests | No hierarchy or minimum-count pooling; held-out labels are never used. |
| P311-04 | Family holdout scope | Whole-family performance was evaluated only for frozen F2 in Global and Ming; D5_MAIN was not directly evaluated. | robustness_summary.csv; Table 5; Table A4 | Cannot generalize F2 family robustness to D5_MAIN. |
| P311-05 | Ming family capital | Ming F3-F2 and F4-F2 ROC-AUC intervals and corresponding PR-AUC intervals include zero. | Table A3; paired_bootstrap_results.csv; Figure 7 | Absence of clear incremental evidence is not proof of no effect. |
| P311-06 | Nested ablation order | Every grouped increment is conditional on the frozen nested order. | Table A3; grouped_ablation_corrected.csv; Methods | Not a unique contribution, permutation importance, or causal effect. |
| P311-07 | Operating points and shift support | Selected thresholds, retained weighting schemes, sigmoid parameters, and all shift supports are reported from existing artifacts. | operating_parameters.csv; split_support_summary.csv; shift_support_summary.csv; Table A1b | Numeric class weights and Logistic calibrators are NOT_RETAINED rather than reconstructed. |
