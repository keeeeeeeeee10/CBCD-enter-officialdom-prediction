# Phase 2.6 Final Model Report

## Target and protocol

Target V1 is `ENTRY_DATA` record presence. All canonical models use seed 42 and the unchanged frozen Primary train/validation/test person IDs. Validation alone controls early stopping, class-weight choice, threshold selection, and the optional diagnostic sigmoid calibration. Test data are not used for selection.

No hyperparameter search, GNN, or PageRank was run. Seeds 202, 2024, 2025, and 2026 are stability checks only; no best seed was selected.

## Locked canonical models

| Population | Model | ROC-AUC | PR-AUC | LogLoss | Brier | Raw ECE | Model SHA256 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Global | H_STRUCT | 0.926721 | 0.858211 | 0.339298 | 0.104816 | 0.069024 | 17dfaeb59ac96429ef5463d6094c8e249f571c8229d5810209213a49c60b5cc7 |
| Global | D5_MAIN | 0.936956 | 0.882535 | 0.315106 | 0.097356 | 0.065097 | ef37ca9a7e5c93263ad8d27f8ab7b17163f51ec09008bfe7cecfb5398de20957 |
| Global | D6_UPPER | 0.937421 | 0.883128 | 0.313950 | 0.096938 | 0.064628 | 3c46501d70b674b90cb4b5b6ee12c510d69c7fc3d1a7b2725a73cd72a76c4645 |
| Song | H_STRUCT | 0.918350 | 0.911650 | 0.360396 | 0.111199 | 0.011958 | 18c979ef9e993ba367e5819e5b252152ab1857797ede3299048284858a87a1e2 |
| Song | D5_MAIN | 0.938351 | 0.939838 | 0.308890 | 0.093986 | 0.011699 | f808ac8d28f98a3999c831a7e3fa290804da5329f37457a24f580b03bf79503c |
| Song | D6_UPPER | 0.939798 | 0.941195 | 0.305452 | 0.092799 | 0.013161 | 5917056924c8c6327061b57e34cfc411493f2b41b178827f2e768f2e811c0c43 |
| Ming | H_STRUCT | 0.910657 | 0.779909 | 0.346308 | 0.109660 | 0.141709 | 795c1f66d44c301d1f37fa2e3bd0f0a51e332a98530757f10497f65fb555621c |
| Ming | D5_MAIN | 0.916395 | 0.800527 | 0.322947 | 0.102572 | 0.135699 | 1c71cc3c21eec28d5dbb0bd3e0bb1905be2316fe97e422211566a25e4fc7bfae |
| Ming | D6_UPPER | 0.916696 | 0.801196 | 0.322401 | 0.102311 | 0.135729 | f49d7c69af34488fbb678a62c982d6f3255e6599202b56f5f652f89629daaa99 |

- **H_STRUCT:** historical structural prediction associations; excludes `addr_type_name`, general documentation, supervised target priors, and relatives’ outcomes.
- **D5_MAIN:** main predictive model; includes documentation-linked fields and a fold-safe local prior, but no relatives’ ENTRY/posting outcomes.
- **D6_UPPER:** D5 plus explicitly allowlisted full-record cross-sectional family outcomes; a record-structure upper bound, not a strict pre-entry model.

## Five-seed stability

| Population | Comparison | Mean ΔAUC | SD | Range | Positive seeds | Practical magnitude |
| --- | --- | --- | --- | --- | --- | --- |
| Global | F3 - F2 | +0.000620 | 0.000086 | [+0.000520, +0.000720] | 5/5 | small |
| Global | F4 - F2 | +0.000329 | 0.000082 | [+0.000247, +0.000457] | 5/5 | small |
| Global | D6 - D5 | +0.000407 | 0.000102 | [+0.000270, +0.000539] | 5/5 | small |
| Global | D6i - D5 | +0.000247 | 0.000177 | [+0.000105, +0.000458] | 5/5 | small |
| Song | F3 - F2 | +0.002295 | 0.000305 | [+0.001821, +0.002674] | 5/5 | not_flagged |
| Song | F4 - F2 | +0.001188 | 0.000306 | [+0.000902, +0.001603] | 5/5 | small |
| Song | D6 - D5 | +0.000803 | 0.000203 | [+0.000545, +0.001088] | 5/5 | small |
| Song | D6i - D5 | +0.000283 | 0.000212 | [-0.000074, +0.000467] | 4/5 | small |
| Ming | F3 - F2 | +0.000496 | 0.000714 | [-0.000319, +0.001189] | 3/5 | small |
| Ming | F4 - F2 | +0.000005 | 0.000440 | [-0.000394, +0.000632] | 2/5 | small |
| Ming | D6 - D5 | +0.000517 | 0.000259 | [+0.000216, +0.000861] | 5/5 | small |
| Ming | D6i - D5 | +0.000241 | 0.000452 | [-0.000342, +0.000685] | 3/5 | small |

Statistical detectability, seed stability, and practical importance are distinct. A consistent increment below 0.002 ROC-AUC is explicitly labeled small.

## Matched-support spatial sensitivity

| Population | Model | Random AUC/PR | Spatial AUC/PR | Δ spatial−random AUC/PR |
| --- | --- | --- | --- | --- |
| Global | D5_MAIN | 0.919748/0.914904 | 0.897571/0.879052 | -0.022177/-0.035853 |
| Global | H_STRUCT | 0.903153/0.891718 | 0.872439/0.831291 | -0.030714/-0.060427 |
| Ming | D5_MAIN | 0.939115/0.926314 | 0.932692/0.920740 | -0.006423/-0.005574 |
| Ming | H_STRUCT | 0.930107/0.905660 | 0.922810/0.895060 | -0.007297/-0.010600 |
| Song | D5_MAIN | 0.918267/0.960131 | 0.893811/0.933361 | -0.024455/-0.026770 |
| Song | H_STRUCT | 0.872719/0.929921 | 0.810654/0.852220 | -0.062065/-0.077701 |

The random and spatial test IDs differ, so no paired individual bootstrap is claimed.

## Calibration

Raw balanced-weight probabilities are not assumed calibrated. `final_model_calibration.csv` reports raw ECE/Brier/LogLoss and a validation-fitted sigmoid diagnostic evaluated on test. The calibrated probability is diagnostic, not selected on test.

## Grouped SHAP

| Population | Model | Group | Share of total |SHAP| | Rank |
| --- | --- | --- | --- | --- |
| Global | D5_MAIN | personal_gender | 19.46% | 1 |
| Global | D5_MAIN | other | 15.75% | 2 |
| Global | D5_MAIN | family_topology | 13.45% | 3 |
| Global | D6_UPPER | personal_gender | 18.20% | 1 |
| Global | D6_UPPER | other | 15.41% | 2 |
| Global | D6_UPPER | family_topology | 13.27% | 3 |
| Global | H_STRUCT | personal_gender | 19.76% | 1 |
| Global | H_STRUCT | family_topology | 16.89% | 2 |
| Global | H_STRUCT | other | 16.41% | 3 |
| Ming | D5_MAIN | personal_gender | 31.95% | 1 |
| Ming | D5_MAIN | family_topology | 20.55% | 2 |
| Ming | D5_MAIN | address_record_semantics | 13.96% | 3 |
| Ming | D6_UPPER | personal_gender | 30.40% | 1 |
| Ming | D6_UPPER | family_topology | 17.05% | 2 |
| Ming | D6_UPPER | family_observability | 14.34% | 3 |
| Ming | H_STRUCT | personal_gender | 34.30% | 1 |
| Ming | H_STRUCT | family_topology | 26.01% | 2 |
| Ming | H_STRUCT | family_observability | 11.94% | 3 |
| Song | D5_MAIN | supervised_local_prior | 21.13% | 1 |
| Song | D5_MAIN | documentation_general | 17.01% | 2 |
| Song | D5_MAIN | family_topology | 16.07% | 3 |
| Song | D6_UPPER | supervised_local_prior | 21.25% | 1 |
| Song | D6_UPPER | documentation_general | 17.23% | 2 |
| Song | D6_UPPER | family_topology | 14.28% | 3 |
| Song | H_STRUCT | administrative_geography | 23.35% | 1 |
| Song | H_STRUCT | family_topology | 20.43% | 2 |
| Song | H_STRUCT | continuous_geography | 18.85% | 3 |

Native CatBoost SHAP was computed for the nine seed-42 model/population combinations on shared frozen-test samples. Additivity is checked in raw-logit space. Group shares sum to one within tolerance.

**SHAP explains model prediction attribution, not causal effect.** H_STRUCT, D5_MAIN, and D6_UPPER answer different questions and their attributions must not be merged into a single historical conclusion.

## Reproduction

Run `bash scripts/run_phase2_6.sh`. Exact features, parameters, model hashes, prediction hashes, thresholds, and best iterations are saved in `outputs/phase2_6/tables/` and `outputs/phase2_6/models/canonical_model_metadata.json`.
