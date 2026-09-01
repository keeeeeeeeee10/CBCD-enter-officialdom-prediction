# Phase 3.1 literature support search

## Search scope

- Search date: 2026-09-01
- Journal scope: peer-reviewed literature and official project or proceedings pages, without a CNS-only restriction
- User language: Chinese notes with English scholarly search queries
- Search policy: title and structured metadata were used for discovery; only candidates whose abstract, full text, official project page, or publisher proceedings page was checked were retained
- Target: 16 to 25 references that support claims actually made in the revised manuscript

The selected set contains 20 references. It is exported as RIS at `outputs/phase3_1/tables/nature_citation_candidates.ris`. The interactive screening artifact is `outputs/phase3_1/citation_review/nature_citation_candidates.html`.

## Segment-to-reference correspondence

### S001. CBDB, prosopography, and computational history

**Source claim.** CBDB structures biographical facts from heterogeneous historical sources for quantitative prosopographical, network, and spatial analysis. Its contents reflect ongoing source extraction, disambiguation, and editorial encoding rather than a census of past lives.

**Search queries.** `China Biographical Database prosopography relational database`; `CBDB historical network source extraction`; `CBDB computational history data model`.

**Selected support.**

1. Chen and Wang, 2022, *China Biographical Database (CBDB): A Relational Database for Prosopographical Research of Pre-Modern China*, *Journal of Open Humanities Data*, DOI `10.5334/johd.68`.
   - Support grade: **strong support**.
   - Evidence basis: publisher abstract and data-paper overview.
   - Supports: CBDB scope, relational design, extraction from disparate sources, statistical/network/spatial use, and continuous disambiguation.
2. Tsui and Wang, 2020, *Harvesting Big Biographical Data for Chinese History: The China Biographical Database (CBDB)*, *Journal of Chinese History*, DOI `10.1017/jch.2020.21`.
   - Support grade: **strong background support**.
   - Evidence basis: publisher article page and abstract.
   - Supports: automated and editorial harvesting of biographical data for Chinese history.
3. Fuller and Wang, 2021, *Structuring, Recording, and Analyzing Historical Networks in the China Biographical Database*, *Journal of Historical Network Research*, DOI `10.25517/jhnr.v5i1.123`.
   - Support grade: **strong support**.
   - Evidence basis: peer-reviewed journal abstract and publisher page.
   - Supports: CBDB as digital prosopography, recorded kinship/social networks, and the role of extraction from historical corpora.
4. Fuller, 2024, *The China Biographical Database User's Guide*.
   - Support grade: **strong technical support**.
   - Evidence basis: official CBDB guide.
   - Supports: schema, query, export, and analytical capabilities. It is not used as primary evidence for broad methodological claims.
5. China Biographical Database Project, 2026, official project and download pages.
   - Support grade: **official source support**.
   - Supports: project identity, current access route, release context, and data-use instructions.

**Insertion.** Introduction, Related Work, Data and Measurement Problem, and Data Availability.

### S002. Historical GIS and historical network analysis

**Source claim.** Prosopographical data can be aggregated for spatial and network analysis while preserving links to individual records, but the resulting patterns depend on what the database records.

**Search queries.** `CBDB GIS prosopography history`; `historical network analysis China Biographical Database`; `prosopographical network relational database Chinese history`.

**Selected support.**

1. Bol, 2012, *GIS, Prosopography and History*, *Annals of GIS*, DOI `10.1080/19475683.2011.647077`.
   - Support grade: **strong support**.
   - Evidence basis: publisher full text.
   - Supports: combining CBDB prosopography with GIS while retaining person-level traceability and the methodological value of spatial aggregation.
2. Fuller and Wang, 2021, DOI `10.25517/jhnr.v5i1.123`.
   - Support grade: **strong support**.
   - Supports: the database's network structures and analytic uses.
3. Chen and Wang, 2022, DOI `10.5334/johd.68`.
   - Support grade: **background support**.
   - Supports: CBDB's network and spatial export capabilities.

**Insertion.** Related Work. The text does not claim that GIS or network analysis itself is novel.

### S003. Tabular machine learning and CatBoost

**Source claim.** Tree ensembles are strong baselines for heterogeneous tabular data, and CatBoost provides a documented approach to categorical predictors and target-statistic leakage control. The present paper uses these methods rather than introducing a new learner.

**Search queries.** `tree based models typical tabular data NeurIPS`; `CatBoost categorical features ordered target statistics`; `tabular data tree ensemble baseline`.

**Selected support.**

1. Prokhorenkova et al., 2018, *CatBoost: Unbiased Boosting with Categorical Features*, NeurIPS 31.
   - Support grade: **strong method support**.
   - Evidence basis: official NeurIPS proceedings page.
2. Grinsztajn, Oyallon, and Varoquaux, 2022, *Why Do Tree-Based Models Still Outperform Deep Learning on Typical Tabular Data?*, NeurIPS 35, DOI `10.52202/068431-0037`.
   - Support grade: **background support**.
   - Evidence basis: official proceedings metadata and paper.

**Insertion.** Related Work and Models. Avoid innovation language based on model choice.

### S004. Dataset shift, grouped holdout, and transportability

**Source claim.** Randomly held-out performance can be optimistic for structured data, and predictive relationships may fail when the data-generating distribution changes. Grouped spatial or family holdouts therefore test transport under a stated shift rather than external historical truth.

**Search queries.** `block cross validation spatial hierarchical structured data`; `dataset shift transport predictive models`; `covariate shift cross validation`; `in-the-wild distribution shifts benchmark`.

**Selected support.**

1. Roberts et al., 2017, *Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure*, *Ecography*, DOI `10.1111/ecog.02881`.
   - Support grade: **strong support**.
   - Evidence basis: publisher full text.
   - Supports: block validation for spatial or hierarchical dependence and the risk of optimistic random validation.
2. Koh et al., 2021, *WILDS: A Benchmark of in-the-Wild Distribution Shifts*, ICML, PMLR 139.
   - Support grade: **strong background support**.
   - Evidence basis: official PMLR abstract.
3. Sugiyama, Krauledat, and Müller, 2007, *Covariate Shift Adaptation by Importance Weighted Cross Validation*, *JMLR* 8.
   - Support grade: **partial method support**.
   - Evidence basis: official JMLR abstract.
   - Supports: why ordinary validation assumptions fail under covariate shift. The manuscript does not claim to implement importance weighting.
4. Subbaswamy, Schulam, and Saria, 2019, *Preventing Failures Due to Dataset Shift: Learning Predictive Models That Transport*, AISTATS, PMLR 89.
   - Support grade: **background support**.
   - Evidence basis: official PMLR abstract.
   - Supports: transport failure when data-generating mechanisms differ. The manuscript does not claim causal transport invariance.

**Insertion.** Related Work, Evaluation Protocol, and Documentation Bias and Distribution Shift.

### S005. Documentation bias, administrative data, labels, and proxy measurement

**Source claim.** Structured databases inherit selection and measurement processes from their sources and institutions. An observed operational label can diverge from the latent construct of interest, and noisy or incomplete labels can affect predictive evaluation.

**Search queries.** `administrative transaction data selection bias`; `measurement model latent construct operationalization machine learning`; `classification label noise survey`; `dataset documentation collection process`.

**Selected support.**

1. Hand, 2018, *Statistical Challenges of Administrative and Transaction Data*, *Journal of the Royal Statistical Society Series A*, DOI `10.1111/rssa.12315`.
   - Support grade: **strong background support**.
   - Evidence basis: publisher article metadata and abstract.
   - Supports: selection and data-generation challenges in administrative and transaction records.
2. Jacobs and Wallach, 2021, *Measurement and Fairness*, FAccT, DOI `10.1145/3442188.3445901`.
   - Support grade: **strong conceptual support**.
   - Evidence basis: ACM abstract.
   - Supports: mismatch between latent constructs and observed operationalizations. It is not cited as direct evidence about CBDB.
3. Frénay and Verleysen, 2014, *Classification in the Presence of Label Noise: A Survey*, *IEEE TNNLS* 25(5), DOI `10.1109/TNNLS.2013.2292894`.
   - Support grade: **partial background support**.
   - Evidence basis: abstract and institutional publication record.
   - Supports: consequences and taxonomy of label noise. CBDB's $E$ is an explicit proxy label, not assumed to be a random corruption of $T$.
4. Gebru et al., 2021, *Datasheets for Datasets*, *Communications of the ACM* 64(12), DOI `10.1145/3458723`.
   - Support grade: **strong documentation support**.
   - Evidence basis: author and publisher-affiliated page and abstract.
   - Supports: documenting dataset motivation, composition, collection process, and recommended use.

**Insertion.** Related Work, Data and Measurement Problem, Limitations, and Reproducibility.

### S006. SHAP and probability calibration

**Source claim.** SHAP is an additive attribution framework, but its values should not be read as causal effects or context-free independent feature contributions. Post-hoc calibration is a separate probability diagnostic and must be fitted without test labels.

**Search queries.** `SHAP additive feature attribution NeurIPS`; `Shapley feature importance limitations ICML`; `probability calibration supervised learning Platt scaling`; `expected calibration error modern neural networks`.

**Selected support.**

1. Lundberg and Lee, 2017, *A Unified Approach to Interpreting Model Predictions*, NeurIPS 30.
   - Support grade: **strong method support**.
   - Evidence basis: official proceedings page.
2. Kumar et al., 2020, *Problems with Shapley-value-based explanations as feature importance measures*, ICML, PMLR 119.
   - Support grade: **strong limiting support**.
   - Evidence basis: official PMLR abstract.
   - Supports: restricting the interpretation of Shapley-based importance and the need for causal reasoning for causal claims.
3. Guo et al., 2017, *On Calibration of Modern Neural Networks*, ICML, PMLR 70.
   - Support grade: **background support**.
   - Evidence basis: official PMLR abstract.
4. Niculescu-Mizil and Caruana, 2005, *Predicting Good Probabilities with Supervised Learning*, ICML, DOI `10.1145/1102351.1102430`.
   - Support grade: **strong method support**.
   - Evidence basis: conference metadata and abstract.
   - Supports: held-out-data post-hoc calibration of classifier probabilities. The revised paper specifies that its sigmoid calibrator is validation-fitted.

**Insertion.** Related Work, Evaluation Protocol, Model Interpretation, and calibration captions.

## Candidate decisions

All 20 selected references are relevant to a statement retained in the revised paper. No blog, screenshot, secondary citation index, or metadata-only record is used to support a scientific claim. General fairness and label-noise sources are used only for measurement or label concepts, not as evidence about CBDB's historical coverage. No citation supports a claim that $E=T$, that $P$ is complete ground truth, or that SHAP identifies causes.

## Export and review artifacts

- Interactive browser: `outputs/phase3_1/citation_review/nature_citation_candidates.html`
- RIS export: `outputs/phase3_1/tables/nature_citation_candidates.ris`
- Machine-readable screening: `outputs/phase3_1/citation_review/nature_citation_candidates.json`
- Screening table: `outputs/phase3_1/citation_review/nature_citation_candidates.tsv`

One DOI, `10.25517/jhnr.v5i1.123`, was absent from Crossref's lookup response. It was retained only after direct verification on the peer-reviewed Journal of Historical Network Research page. This exception is recorded for the independent reference-verification stage.
