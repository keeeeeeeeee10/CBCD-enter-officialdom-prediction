# Phase 2 feature engineering

The master table retains 661,124 unique CBDB people and the unchanged V1 label. Model matrices are selected from `configs/phase2_features.yaml`; no script automatically treats every master-table column as a predictor.

## Personal

`safe_birth_year` is copied only from valid SAFE provenance `01 — Based on Birth Year`; `safe_birth_decade` is its floor-to-decade representation. Raw birth and raw/safe index year are not simultaneously modeled. Missing SAFE birth years are not globally imputed.

## Geography

Primary background address selection, historical hierarchy matching, coordinates, canonical-capital approximation, and non-target local density are documented in `docs/audit/geography_feature_definition.md`. `local_entry_prior` is created only after loading a frozen split: training rows receive OOF encodings and validation/test receive a train-fitted mapping.

## Family

Family Structural features contain relationship/coverage counts only. Cross-sectional `ever_*` variables use relatives' lifetime CBDB ENTRY/posting records and carry temporal ambiguity. Pre-birth variables require both a SAFE focal birth year and a valid relative event year earlier than birth; missing relative event years stay missing.

## Documentation

M5 contains only the six domain flags and documentation intensity. These variables are excluded from M0–M4 and enter historical models only in M6.

Automated validation status: **PASS**. Single-feature AUC >0.95 warnings: none.
