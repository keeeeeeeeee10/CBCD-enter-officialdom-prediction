# D5_MAIN: Main Predictive Model

**Intended use:** Main prediction of ENTRY record presence.

**Target:** CBDB ENTRY_DATA record presence.

**Canonical protocol:** seed 42, frozen Primary split, validation-controlled early stopping/class weights/threshold.

**Known limitation:** Contains documentation-linked predictors and a fold-safe local prior; it is not a pure historical-mechanism model.

## Test metrics

| Population | Model | ROC-AUC | PR-AUC | LogLoss | Brier | Raw ECE | Model SHA256 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Global | D5_MAIN | 0.936956 | 0.882535 | 0.315106 | 0.097356 | 0.065097 | ef37ca9a7e5c93263ad8d27f8ab7b17163f51ec09008bfe7cecfb5398de20957 |
| Song | D5_MAIN | 0.938351 | 0.939838 | 0.308890 | 0.093986 | 0.011699 | f808ac8d28f98a3999c831a7e3fa290804da5329f37457a24f580b03bf79503c |
| Ming | D5_MAIN | 0.916395 | 0.800527 | 0.322947 | 0.102572 | 0.135699 | 1c71cc3c21eec28d5dbb0bd3e0bb1905be2316fe97e422211566a25e4fc7bfae |

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

## Interpretation

SHAP and feature importance describe prediction attribution, not causal effects. The model must be interpreted only according to its stated scientific role.
