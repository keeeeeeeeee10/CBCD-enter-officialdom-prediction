# Phase 3.1 manuscript restructuring record

## One-sentence argument

In the selectively documented CBDB population, we show that ENTRY-record presence is highly predictable using a frozen, leakage-controlled tabular workflow, but grouped ablations, family and spatial shift tests, calibration, and grouped attribution demonstrate that the resulting discrimination combines historical structure with documentation processes and therefore does not recover latent historical entry.

## Argument chain

1. **Field-scale need.** Prosopographical databases enable large-scale historical analysis.
2. **Unresolved bottleneck.** These databases are selected records rather than random censuses, so a predictive target may encode documentation as well as historical structure.
3. **Proposed move.** Define ENTRY-record presence explicitly as a proxy label, enforce leakage boundaries, compare a structural benchmark, main predictor, and database-internal upper bound, then test conditional feature information and transport.
4. **Decisive evidence.** D5_MAIN reaches Global ROC-AUC 0.936956 and PR-AUC 0.882535; documentation and observability groups contribute strongly; recorded family political capital adds only small increments; matched-support spatial performance falls; SHAP shares do not equal independent gains.
5. **Implication.** High discrimination is informative about structured record presence within CBDB, not a direct reconstruction of historical truth.
6. **Boundary.** $E$, $P$, and $T$ are semantically distinct; CBDB is selected; family and temporal features have ambiguity; calibration may shift; the source-group protocol is infeasible at full coverage; the primary test has been inspected repeatedly.

## Terminology ledger

| Canonical term | Definition on first use | Variants removed or restricted | Decision |
| --- | --- | --- | --- |
| ENTRY-record presence | at least one `ENTRY_DATA` record for a person | true entry prediction; actual entry probability | Primary observed target $E$ |
| recorded ENTRY share | proportion with $E=1$ | entry rate; true entry rate | Always specify denominator |
| CBDB-covered individuals | people represented in `BIOG_MAIN` | historical Chinese population; CBDB-listed people | Population scope term |
| documentation-linked features | predictors reflecting record coverage or encoding | documentation features; database features | Use for D5_MAIN interpretation |
| family observability | whether and how much kin information is recorded | kin coverage when used as a model block | Separate from topology and capital |
| family topology | recorded kin-network structure | family structure when ambiguous | May include transductive information |
| recorded family political capital | relatives' recorded ENTRY or posting outcomes | family capital when first introduced | Cross-sectional and temporally ambiguous |
| matched-support spatial shift | random-versus-unseen-region comparison on identical reliable-prefecture support | spatial validation; geographic effect | Test people differ, so not person-paired |
| database-internal upper bound | D6_UPPER with full-record relative outcomes | best historical model; main model | Never headline historical mechanism model |
| historical structural benchmark | H_STRUCT | unbiased historical model; pure structural model | Must note residual address and kin observability |
| historical regime | SHAP group containing `dynasty_name` | other; dynasty group | Canonical SHAP group label |
| Validation-calibrated ECE | ECE after validation-fitted sigmoid | Cal. ECE; ECE without qualifier | Distinguish from raw LogLoss and Brier |
| latent historical entry state | $T_i$ | historical truth when used as an observed label | Unobserved in this study |
| observed posting label | $P_i$ | posting ground truth | Auxiliary, incomplete observation |

## Section and paragraph map

### Abstract

1. Measurement problem and exact task.
2. Frozen evaluation design and main result.
3. Decisive conditional-contribution and shift findings.
4. Bounded implication, high discrimination of record presence does not recover $T$.

### Introduction

1. Prosopographical databases support computation at historical scale.
2. Selection and documentation make high AUC insufficient.
3. The exact gap is separation of structural prediction from record-generation signals.
4. RQ1 to RQ5, followed by three evidence-based contributions.

### Related Work

Topic synthesis rather than a single compressed paragraph.

1. CBDB, prosopography, computational history, historical GIS, and historical networks.
2. Tabular learning and categorical boosting.
3. Dataset shift, group holdout, and transportability.
4. Documentation or administrative-data bias, proxy labels, and label noise.
5. Calibration and SHAP, with explicit interpretation boundaries.

### Data and Measurement Problem

1. CBDB as a selective relational record system.
2. $T_i$, $E_i$, and $P_i$ with semantic non-equivalence, not individual inequality.
3. Heterogeneous ENTRY pathways and why $E=0$ means no located ENTRY record.
4. ENTRY by Posting quadrants and what each can and cannot establish.

### Task Definition and Leakage Control

1. Estimand $\Pr(E_i=1\mid X_i)$ and person-level aggregation.
2. Forbidden direct target or posting fields and split-safe derived predictors.
3. Family and temporal ambiguity, including H_STRUCT's residual observability.

### Exploratory Data Analysis

1. Dynasty coverage and recorded ENTRY share for Tang, Song, Yuan, Ming, and Qing.
2. Gender differences with selection and historical explanations kept unresolved.
3. ENTRY pathway composition and nonexclusive person-level categories.
4. Address coverage, kin coverage, and documentation intensity as evidence of a record-generation process.

Each EDA paragraph follows `observation -> plausible explanations -> non-identifiable alternatives`.

### Feature Construction

1. Personal and regime features.
2. Address observability, administrative geography, physical geography, and address-record semantics.
3. Family observability, topology, and recorded family political capital.
4. Documentation intensity and split-safe local prior.

### Models and Evaluation Protocol

1. Logistic baseline and CatBoost role, without claiming algorithmic novelty.
2. H_STRUCT, D5_MAIN, and D6_UPPER roles.
3. Frozen splits, validation-only choices, metrics and prevalence.
4. Exact-pair bootstrap, multi-seed stability, group shift, calibration, and source feasibility gate.

### Experimental Results

1. Locked discrimination hierarchy with D5_MAIN as the headline.
2. Grouped ablations as primary conditional-contribution evidence.
3. Family decomposition and practical magnitude.

### Documentation Bias and Distribution Shift

1. Matched-support spatial losses and their non-causal interpretation.
2. Family holdout as a narrower group-generalization check.
3. SAFE temporal, Qing, and source-group boundaries, with no invented performance.

### Model Interpretation

1. Grouped SHAP patterns using `historical_regime`.
2. SHAP as dependent attribution rather than independent gain or causal effect.
3. Local-prior and family-capital examples that separate SHAP share from ablation increments.

### Discussion and Limitations

Discussion synthesis leads into four thematic limitation paragraphs.

1. Measurement and label validity.
2. Selection and documentation bias.
3. Temporal and transductive information.
4. Generalization and adaptive test use.

### Conclusion

One bounded synthesis. No new data, citations, experiments, or promises.

### Reproducibility and Data Availability

Data availability, code availability, and reproducibility are separated and later audited by `nature-data`.

## Main-text result allocation

| Result | Class | Effect on central interpretation | Destination |
| --- | --- | --- | --- |
| D5_MAIN Global ROC-AUC and PR-AUC | core discovery | Establishes high within-CBDB discrimination | Main text and Table 3 |
| H_STRUCT and D6_UPPER hierarchy | necessary support | Separates model roles | Main text, Table 3, Figure 4 |
| Grouped ablation | core discovery | Identifies conditional predictive information | Main text, Table 4, Figure 5 |
| Exact retained paired intervals | necessary support | Quantifies conditional test-sample uncertainty | Table 4 and appendix |
| Physical Geography unavailable CI | qualification | Prevents false precision | Main text caption and Table 4 |
| Five-seed stability | robustness | Separates small stable increments from importance | Appendix with concise main-text pointer |
| Matched-support spatial shift | qualification | Materially limits geographic transport | Main text, Table 5, Figure 6 |
| Family holdout | robustness | Bounds family generalization | Main text briefly, full appendix |
| Grouped SHAP | necessary support | Describes attribution redistribution | Main text, Figure 8 |
| Built-in importance | alternative inference | Not needed for central claim | Appendix or package only |
| Calibration comparison | qualification | Prevents probability overinterpretation | Table 3 labels and appendix |
| SAFE temporal composition | edge case | No locked performance, so no temporal claim | Appendix and limitation |
| Qing descriptive context | heterogeneity | No prespecified holdout | EDA or appendix only |
| Source component feasibility | edge case | Bounds source-group confirmation | Main text briefly and appendix |
| Full feature registry and hashes | provenance detail | Enables reproduction | Appendix and review package |

## Shortest sufficient evidence chain

1. D5_MAIN discriminates ENTRY-record presence on the frozen primary test.
2. Ablations show that observability and documentation-linked groups provide substantial conditional information, while recorded family political capital provides small increments.
3. Spatial shift reduces performance on unseen historical regions, which bounds transportability.
4. SHAP attribution redistributes across groups but does not identify independent or causal effects.
5. Label semantics, source selection, temporal ambiguity, calibration shift, and adaptive test use bound the historical interpretation.

## Planned replacement and relocation log

| Current element | Action | Reason |
| --- | --- | --- |
| One-paragraph Related Work | Replace with five topic-linked paragraphs | Current novelty positioning is not assessable |
| One-paragraph EDA | Replace with three evidence-led paragraphs | Current text describes rather than interprets distributions |
| 15-item limitations checklist | Replace with four thematic paragraphs | Explain consequences for claims instead of listing caveats |
| Repeated source counts in Abstract and Results | Compress | Preserve one key feasibility statistic and protocol-bound wording |
| Built-in importance references | Keep outside main evidence chain | Grouped ablation and SHAP have clearer roles |
| Full multi-seed details | Relocate to appendix | Robustness supports but does not lead the main claim |
| Full calibration comparison | Relocate to appendix | Headline table retains only explicit raw/calibrated labels |
| `E \ne T` style statements | Replace globally | Construct non-equivalence is the intended claim |
| `other` SHAP label | Replace globally with `historical_regime` | The group contains `dynasty_name` |
| `KDD-style 2026` metadata | Replace with neutral course metadata | Avoid false conference association |

## Claim-repetition map

| Claim | Abstract | Introduction | Results | Discussion or limitations | Conclusion |
| --- | --- | --- | --- | --- | --- |
| ENTRY-record presence is highly predictable | Introduce with headline numbers | Motivate RQ1, no detailed result | Demonstrate | Interpret with documentation evidence | Synthesize briefly |
| Documentation contributes to performance | Introduce as boundary | State central gap | Demonstrate by ablation and shift | Interpret with rival historical explanations | Synthesize |
| Recorded family political capital adds little | One support sentence | Motivate RQ3 | Demonstrate with deltas and stability | Bound as predictive, not causal | Mention once |
| Spatial transport is weaker | One boundary sentence | Motivate RQ4 | Demonstrate | Generalization boundary | Mention once |
| $E$, $P$, and $T$ are semantically distinct | Define | Establish measurement problem | Do not repeat per paragraph | Measurement limitation | Final boundary |

## Nature-writing decision record

Accepted recommendations are the evidence-first Results order, the five-question Introduction, topic-synthesized Related Work, thematic limitations, explicit model roles, and main-versus-appendix allocation. The generic algorithm-paper template was rejected where it would treat CatBoost or SHAP as a novel method. No claim, model, result, or reference was added beyond the frozen artifacts and later verified literature.
