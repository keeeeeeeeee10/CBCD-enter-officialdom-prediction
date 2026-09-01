# D6_UPPER: Record-Structure Upper Bound

**Intended use:** Database-internal predictive upper bound.

**Target:** CBDB ENTRY_DATA record presence.

**Canonical protocol:** seed 42, frozen Primary split, validation-controlled early stopping/class weights/threshold.

**Known limitation:** Adds full-record cross-sectional relatives’ ENTRY/posting outcomes and is not strict pre-entry.

## Test metrics

| Population | Model | ROC-AUC | PR-AUC | LogLoss | Brier | Raw ECE | Model SHA256 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Global | D6_UPPER | 0.937421 | 0.883128 | 0.313950 | 0.096938 | 0.064628 | 3c46501d70b674b90cb4b5b6ee12c510d69c7fc3d1a7b2725a73cd72a76c4645 |
| Song | D6_UPPER | 0.939798 | 0.941195 | 0.305452 | 0.092799 | 0.013161 | 5917056924c8c6327061b57e34cfc411493f2b41b178827f2e768f2e811c0c43 |
| Ming | D6_UPPER | 0.916696 | 0.801196 | 0.322401 | 0.102311 | 0.135729 | f49d7c69af34488fbb678a62c982d6f3255e6599202b56f5f652f89629daaa99 |

## Resolved features

| Feature | Role |
| --- | --- |
| dynasty_name | categorical |
| gender | categorical |
| safe_birth_decade | categorical |
| province_id | categorical |
| prefecture_id | categorical |
| county_id | categorical |
| addr_type_name | categorical |
| has_address | numeric |
| has_kin | numeric |
| has_assoc | numeric |
| has_status | numeric |
| has_text | numeric |
| has_institution | numeric |
| documentation_intensity | numeric |
| has_safe_birth_year | numeric |
| has_geography | numeric |
| has_valid_coordinates | numeric |
| latitude | numeric |
| longitude | numeric |
| distance_to_dynasty_capital_km | numeric |
| train_region_person_count | numeric |
| train_region_log_density | numeric |
| local_target_prior | numeric |
| has_core_family | numeric |
| father_identified | numeric |
| mother_identified | numeric |
| any_grandfather_identified | numeric |
| n_known_parents | numeric |
| n_known_grandparents | numeric |
| n_known_ancestors | numeric |
| n_known_same_generation | numeric |
| n_known_descendants | numeric |
| n_known_core_kin | numeric |
| family_group_size | numeric |
| father_ever_entry | numeric |
| father_ever_posting | numeric |
| paternal_grandfather_ever_entry | numeric |
| paternal_grandfather_ever_posting | numeric |
| maternal_grandfather_ever_entry | numeric |
| maternal_grandfather_ever_posting | numeric |
| n_older_kin_ever_entry | numeric |
| n_older_kin_ever_posting | numeric |
| older_kin_entry_ratio | numeric |
| older_kin_posting_ratio | numeric |

## Interpretation

SHAP and feature importance describe prediction attribution, not causal effects. The model must be interpreted only according to its stated scientific role.
