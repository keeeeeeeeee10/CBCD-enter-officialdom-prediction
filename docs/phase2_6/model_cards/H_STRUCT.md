# H_STRUCT: Historical Structural Model

**Intended use:** Historical structural prediction associations.

**Target:** CBDB ENTRY_DATA record presence.

**Canonical protocol:** seed 42, frozen Primary split, validation-controlled early stopping/class weights/threshold.

**Known limitation:** No general documentation, address-record type, supervised local prior, or relatives’ outcomes.

## Test metrics

| Population | Model | ROC-AUC | PR-AUC | LogLoss | Brier | Raw ECE | Model SHA256 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Global | H_STRUCT | 0.926721 | 0.858211 | 0.339298 | 0.104816 | 0.069024 | 17dfaeb59ac96429ef5463d6094c8e249f571c8229d5810209213a49c60b5cc7 |
| Song | H_STRUCT | 0.918350 | 0.911650 | 0.360396 | 0.111199 | 0.011958 | 18c979ef9e993ba367e5819e5b252152ab1857797ede3299048284858a87a1e2 |
| Ming | H_STRUCT | 0.910657 | 0.779909 | 0.346308 | 0.109660 | 0.141709 | 795c1f66d44c301d1f37fa2e3bd0f0a51e332a98530757f10497f65fb555621c |

## Resolved features

| Feature | Role |
| --- | --- |
| dynasty_name | categorical |
| gender | categorical |
| safe_birth_decade | categorical |
| province_id | categorical |
| prefecture_id | categorical |
| county_id | categorical |
| has_safe_birth_year | numeric |
| has_geography | numeric |
| has_valid_coordinates | numeric |
| latitude | numeric |
| longitude | numeric |
| distance_to_dynasty_capital_km | numeric |
| train_region_person_count | numeric |
| train_region_log_density | numeric |
| has_kin | numeric |
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
