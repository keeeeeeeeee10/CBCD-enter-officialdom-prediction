# Final Interpretation and Limitations

## Scientific scope

The target is presence of at least one CBDB `ENTRY_DATA` record. It is not actual government-entry probability, actual office holding, or an estimate for the historical population of China. ENTRY credentials and routes are not equivalent to a verified posting.

## Selection and documentation

CBDB is a selected historical database. Survival of sources, editorial attention, lineage documentation, address recording, biography density, and institutional coverage vary sharply across periods and social groups. Consequently, strong discrimination and strong documentation bias can coexist.

H_STRUCT reduces explicit documentation-linked content, but address and family observability can still encode record survival. D5_MAIN is deliberately a documentation-linked predictor. D6_UPPER uses relatives’ complete recorded outcomes and is only a database-internal record-structure upper bound.

## Time and family ambiguity

Full-record family ENTRY/posting outcomes are cross-sectional and temporally ambiguous. Train-observed family outcomes restrict whose records are visible but are not strict pre-entry measures. Pre-birth lineage coverage is sparse and is not equivalent to matched pre-entry family capital.

## Geography and transport

Historical administrative categories, address observability, physical coordinates, and address-record semantics are separate constructs. `addr_type_name` is documentation-linked. Matched spatial holdout tests distribution shift to unseen historical region groups; it is not a causal experiment and does not establish geographic effects.

## SAFE birth information

SAFE birth-year coverage is low. When CatBoost already sees a missing-aware value, the explicit flag can be redundant. Therefore P3−P2≈0 means only that the explicit indicator adds little under that representation; it does not mean birth-year availability has no predictive information.

## Calibration and interpretation

Balanced class weights can shift raw probabilities. Validation-fitted sigmoid results are diagnostic. Neither raw nor calibrated values should be described as an individual's real probability of entering government.

SHAP explains attribution within a fitted predictive model, not causal effect. “Gender causes ENTRY,” “prefecture causes entry,” and “father ENTRY causes child ENTRY” are unsupported statements. Global results describe the assembled CBDB population, not the overall population of historical China.
