# Phase 3.1 pre-submission review, Round 1

## 1. Overall assessment

This is a careful and unusually transparent data-mining study of a difficult historical database. The manuscript correctly makes ENTRY-record presence, rather than latent historical entry, its prediction target. It also separates a structural benchmark, a documentation-aware main model, and a database-internal upper bound. The frozen splits, leakage registry, grouped ablations, multi-seed checks, matched-support spatial analysis, calibration audit, source-group feasibility gate, and local figure provenance provide a strong reproducibility foundation.

The current version is not yet submission-ready. One uncertainty interval in Table 4 is not demonstrated to correspond to the reported Physical Geography contrast. The semantic statements relating $E$, $P$, and $T$ are written as person-level inequalities rather than non-equivalence of constructs. Figure 1 also imposes an overly simple latent-state-to-database pathway. These are blocking scientific-reporting issues because they affect the validity of an advertised inferential result and the central measurement definition. The Related Work, EDA, limitations, captions, probability-metric labels, and main-text page audit require substantial revision. The KDD-style 2026 footer must be replaced because it can be read as false conference metadata.

The study is promising as a course research submission after the corrections below. It should not be positioned as a new predictive-model contribution. Its strongest contribution is the documentation-aware evaluation design and the empirical separation of conditional feature information from database record structure.

## 2. Summary of contributions

1. The manuscript defines a person-level supervised task over 661,124 CBDB-covered individuals with $E=1$ when at least one `ENTRY_DATA` record is present.
2. It implements an explicit leakage policy and a locked hierarchy comprising H_STRUCT, D5_MAIN, and D6_UPPER. D5_MAIN is the main predictive model and obtains Global ROC-AUC 0.936956 and PR-AUC 0.882535 on the frozen primary test.
3. It uses grouped ablation, paired bootstrap where exact paired predictions were retained, five-seed stability, family holdout, and matched-support spatial shift to distinguish predictive discrimination from transportability and practical importance.
4. It treats documentation-linked variables as substantive parts of the record-generation process. The reported evidence indicates that family observability and topology carry much more conditional predictive information than recorded family political capital.
5. It provides a reproducibility chain that links frozen source data, feature policy, model hashes, figure-input snapshots, generated figures, and review artifacts.

## 3. Major concerns

### R1-M1. Physical Geography interval and contrast identity

**Classification** Blocking submission

**Claim pointer** Table 4 reports the Global Physical Geography contrast as A3 minus A2 with paired 95% intervals.

**Evidence pointer** `paper/tables/table4_ablation.tex`; `paper/tables/tableA3_full_ablation.tex`; `outputs/phase2_5/tables/geography_decomposition_predictions.csv`; `outputs/phase2_5/tables/paired_bootstrap_results.csv`.

**Concern** The point estimates are explicitly A3 minus A2, but the current paper does not prove that the intervals were computed from the same A2 and A3 predictions on identical test IDs. The Global PR point estimate, -0.000343, also lies outside the printed interval [-0.0016, -0.0004]. Ming has the same internal-containment failure in both metrics in the appendix. A point estimate outside its stated interval is direct evidence that the interval and estimate do not represent the same empirical contrast.

**Why it matters** Table 4 is presented as primary evidence of conditional feature contribution. A mismatched paired interval invalidates that row's uncertainty statement and undermines confidence in the table.

**Resolution test** Recompute the A3 minus A2 paired ROC-AUC and PR-AUC distributions from retained A2 and A3 predictions on exactly matching person IDs, with 500 or 1,000 seed-42 resamples. If the exact pair does not exist, replace the intervals with dashes and state that exact paired predictions were not retained. Add an automated containment and model-contrast identity test.

### R1-M2. Construct non-equivalence is expressed as individual inequality

**Classification** Blocking submission

**Claim pointer** The task definition states $E\ne T$, $P\ne T$, and $E\ne P$ after defining person-level indicators.

**Evidence pointer** Data and Task Definition, equations 1 to 3; Figure 1; Appendix Schema, Targets, and ENTRY Taxonomy.

**Concern** The intended claim is semantic non-equivalence of the three constructs. As typeset, the notation can be read as asserting that every person's observed ENTRY and posting indicators differ from the person's latent historical state and from one another. The observed 2 by 2 contingency itself shows many individuals with $E=P$.

**Why it matters** This notation conflicts with the manuscript's central measurement argument and the displayed data.

**Resolution test** Use $E\not\equiv T$, $P\not\equiv T$, and $E\not\equiv P$, or state in prose that $E$, $P$, and $T$ are not semantically equivalent. Apply the same definition in the abstract, body, figure, captions, and appendix.

### R1-M3. Figure 1 oversimplifies the historical and documentation process

**Classification** Blocking submission

**Claim pointer** Figure 1 presents latent historical entry $T$ as flowing through one preservation-and-encoding node into both ENTRY and posting observations.

**Evidence pointer** Figure 1 and its caption; Data and Task Definition.

**Concern** ENTRY records include examinations, credentials, schools, recommendation, privilege, and appointment-related pathways, while postings record a semantically different office-holding process. A single $T$ parent can therefore imply that $E$ and $P$ are two noisy measurements of the same event. That is stronger than the database definitions support.

**Why it matters** The figure is the conceptual anchor for the paper. Its current causal-looking topology obscures rather than clarifies the distinction the manuscript seeks to establish.

**Resolution test** Redraw the figure with separate historical entry or credential events, posting or office-holding events, and broader biographical processes. Route these through source survival and selection, then editorial extraction and database encoding, before the observed $E$ and $P$ labels. Retain the data-derived 2 by 2 contingency and mark $T$ as latent.

### R1-M4. Related Work does not establish the study's position

**Classification** Should fix

**Claim pointer** The manuscript frames its contribution as documentation-aware historical data mining with grouped transport and proxy-label concerns.

**Evidence pointer** Related Work; `paper/reference_audit.csv`.

**Concern** The section is one paragraph and the full paper contains only 10 audited references. It mentions CBDB, historical GIS, tabular models, SHAP, calibration, distribution shift, and administrative data, but does not synthesize relevant work on prosopography and computational history, historical networks, group holdout or transportability, proxy labels or label noise, and data or documentation bias. It therefore does not show which parts are established practice and which combination is distinctive here.

**Why it matters** The paper's novelty is methodological framing and evidence design rather than a new algorithm. That contribution cannot be evaluated without a fuller, claim-matched literature basis.

**Resolution test** Expand to a selective 16 to 25 verified references across the required topic clusters. Each added reference must be checked against an official or publisher record and connected to a specific manuscript claim.

### R1-M5. The main-text evidence chain is too compressed

**Classification** Should fix

**Claim pointer** The manuscript presents a comprehensive documentation-aware analysis within a reported four-page main-text count.

**Evidence pointer** Exploratory Data Analysis, Experimental Results, Documentation Bias and Robustness, Limitations; `outputs/phase3/tables/paper_quality_check.json`.

**Concern** The EDA is a single paragraph, the results interpretation is compressed around crowded figures, and the limitations are a numbered list of 15 items. The current page audit counts four author-version main-content pages because `\label{mainend}\clearpage` is placed before outstanding floats. The visible manuscript actually places Table 4, Table 5, and Figure 8 on the next page before references. The existing audit is therefore not a reliable content-page count.

**Why it matters** Readers cannot adequately evaluate alternative historical and data-generation explanations, uncertainty boundaries, or the relation between ablation, SHAP, and shift evidence. The faulty page count also weakens the packaging claim.

**Resolution test** Move the main-end label after a float barrier and clear page. Expand the EDA and evidence interpretation without changing frozen results, organize limitations into four thematic paragraphs, and keep the corrected main text within six to seven pages and no more than eight.

## 4. Minor concerns

### R1-m1. Probability metrics mix raw and calibrated quantities

**Classification** Should fix

**Evidence pointer** Table 3; Experimental Results; Appendix Table A2.

Table 3 prints raw LogLoss and Brier beside validation-calibrated ECE without stating the distinction in each column header. Rename the columns Raw LogLoss, Raw Brier, and Validation-calibrated ECE. If space permits, report raw versus calibrated probability metrics in the appendix.

### R1-m2. SHAP group name `other` is not interpretable

**Classification** Should fix

**Evidence pointer** Model Interpretation; Figure 8; `outputs/phase2_6/shap/shap_group_summary.csv`.

The prose explains that `other` is dynasty, but a catch-all group label is misleading. Rename the group `historical_regime` throughout regenerated summaries, figures, captions, and the appendix. No retraining is necessary if existing SHAP values are re-aggregated.

### R1-m3. Conference metadata is misleading

**Classification** Blocking packaging

**Evidence pointer** Author and anonymous PDF footers; `\acmConference` in both LaTeX sources.

Replace `KDD-style 2026, 2026, Shanghai, China` with neutral course-report metadata or use a non-ACM metadata mode while preserving the two-column layout. Do not imply submission to or association with KDD 2026.

### R1-m4. Source feasibility language should be protocol-bound

**Classification** Should fix

**Evidence pointer** Abstract; Documentation Bias and Robustness; `docs/phase3/source_holdout_feasibility.md`.

The evidence supports infeasibility of full-coverage source-group confirmation under the prespecified connected-component protocol. It does not establish that every form of source-level validation is impossible. Use the protocol-bound formulation consistently and reserve a selective single-primary-source subset for future-work discussion.

### R1-m5. Figure captions are not consistently self-contained

**Classification** Should fix

**Evidence pointer** Figures 2 to 8.

Several captions omit the population, split, denominator, metric direction, uncertainty definition, or meaning of missing cells. Figure 4 does not state that the results come from the frozen primary test. Figure 5 does not identify Global in the caption. Figure 6 combines two analyses without defining the matched-support comparator. Captions should allow the display to be interpreted without searching the body.

### R1-m6. H_STRUCT is not free of documentation signals

**Classification** Should fix

**Evidence pointer** Table 2; Features and Leakage Control; Appendix Table A5.

The role label “Historical structural benchmark” is acceptable only with an immediate qualification that address and kin observability remain in the feature set. Avoid calling it an unbiased or purely historical model.

### R1-m7. EDA interpretations need explicit uncertainty boundaries

**Classification** Should fix

**Evidence pointer** Exploratory Data Analysis; Figures 2 and 3.

The section should discuss Tang, Song, Yuan, Ming, and Qing coverage and ENTRY prevalence, gender, pathway composition, address and kin coverage, and documentation intensity. For each pattern, distinguish the observed database pattern, plausible historical or record-generation explanations, and explanations that cannot be identified from these data.

### R1-m8. Anonymous and author pagination differ

**Classification** Optional optimization

**Evidence pointer** `outputs/phase3/tables/paper_quality_check.json`.

The author and anonymous builds report different main and reference page counts. After correcting the float boundary, check that both versions have coherent section boundaries and visually comparable layouts.

## 5. Statistical concerns

1. The Physical Geography intervals fail the most basic consistency check for the Global PR contrast and appendix Ming contrasts. This is the priority correction.
2. Table 3 must distinguish raw probability losses from validation-calibrated ECE. The calibrator must remain validation-fitted only.
3. PR-AUC should always be interpreted with prevalence. Prevalence is present in Appendix Table A2 but absent from the headline table and prose comparison.
4. The paper should distinguish paired bootstrap intervals from comparisons in which test individuals differ. The matched random versus spatial analysis correctly notes different test IDs, but that caveat belongs in the caption and table notes.
5. Five-seed ranges measure algorithmic stability under the selected seeds. They are not confidence intervals and should not be described as sampling uncertainty.
6. Increments on the order of $10^{-3}$ must remain labeled small even when intervals exclude zero or all five seeds have the same sign.
7. Bootstrap intervals quantify conditional test-sample variation only. They do not cover target-definition uncertainty, database inclusion, source survival, or researcher adaptation after repeated test inspection.

## 6. Presentation concerns

The main figures are legible at screen scale, but several single-column panels contain small axis labels and compact legends. Figure 3 is particularly dense. Figure 8 is clearer at full width, but `other` obscures its substantive meaning. Negative deltas in Figure 6 need a stronger visual distinction from positive increments. The first figure's clean design cannot compensate for its misleading process topology. Tables 4 and 5 occupy a separate page after the current main-content label, which exposes the page-audit flaw. The reference page is visually sparse because the manuscript has only 10 references. Neutral conference metadata is required in both versions.

## 7. Required revisions

The following changes are required before submission.

1. Recompute or remove the exact Physical Geography paired intervals and add automatic contrast and containment tests.
2. Replace construct inequalities with semantic non-equivalence and revise all $E/P/T$ wording consistently.
3. Redraw Figure 1 using distinct historical processes and data-generation stages.
4. Remove false KDD-style 2026 conference metadata.
5. Correct the float boundary and page-count audit.
6. Make raw and validation-calibrated metric labels explicit.
7. Expand and verify Related Work with claim-level reference auditing.
8. Rename SHAP `other` to `historical_regime` and regenerate affected summaries and displays.
9. Expand the EDA, results interpretation, and thematic limitations without inventing new experiments.
10. Use protocol-bound source-group language, improve captions, and complete data and code availability statements.

## 8. Optional revisions

1. Move built-in feature importance entirely to the appendix if it remains in the package.
2. Combine closely related visual panels when this improves single-column readability without hiding denominators or uncertainty.
3. Add a compact appendix comparison of raw and validation-calibrated LogLoss, Brier, and ECE from the existing calibration artifact.
4. Add a short future-work statement on a selective single-primary-source subset, clearly noting that it would not represent the full CBDB-covered population.

## 9. Tentative recommendation

**MAJOR REVISION**

The dataset construction, frozen evaluation hierarchy, leakage controls, and documentation-aware framing support a credible course research paper. The current version should not be submitted because a headline ablation interval is internally inconsistent and the central $E/P/T$ semantics are not stated rigorously. If the required revisions are completed without changing the frozen experimental conclusions, the paper is likely to become acceptable for course submission.

## 10. Confidence

**High, 0.92**

The assessment used both compiled PDFs, both LaTeX sources, Phase 2.5 and Phase 2.6 reports, generated tables, figure inputs and manifest, reference audit, Phase 3 invariants, and the source feasibility report. Confidence is lower on historical novelty because the Related Work is currently too short to support a complete field-positioning judgment.
