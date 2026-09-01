#!/usr/bin/env python3
"""Create Phase 3.1.1 final LaTeX sources without altering Phase 3.1."""

from __future__ import annotations

import shutil
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVISED = ROOT / "paper/revised"
FINAL = ROOT / "paper/final"
DOCS = ROOT / "docs/phase3_1_1"
POP_ORDER = {"Global": 0, "Song": 1, "Ming": 2, "Qing": 3}


def require_replace(text: str, old: str, new: str) -> str:
    if old not in text:
        raise RuntimeError(f"Required manuscript source text was not found: {old[:120]!r}")
    return text.replace(old, new)


def copy_inputs() -> None:
    (FINAL / "tables").mkdir(parents=True, exist_ok=True)
    (FINAL / "figures").mkdir(parents=True, exist_ok=True)
    for source in sorted((REVISED / "tables").glob("*.tex")):
        shutil.copy2(source, FINAL / "tables" / source.name)
    shutil.copy2(REVISED / "references_revised.bib", FINAL / "references_final.bib")
    shutil.copy2(REVISED / "reference_audit_revised.csv", FINAL / "reference_audit_final.csv")


def reorder_table_rows(path: Path, key) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    indices = [
        index for index, line in enumerate(lines)
        if any(line.startswith(population + " &") for population in POP_ORDER)
    ]
    if not indices:
        raise RuntimeError(f"No population rows in {path}")
    rows = [lines[index] for index in indices]
    ordered = sorted(rows, key=key)
    for index, row in zip(indices, ordered):
        lines[index] = row
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def reorder_appendix_tables() -> None:
    a2 = FINAL / "tables/tableA2_full_metrics.tex"
    model_order = {"Logistic M6": 0, "H\\_STRUCT": 1, "D5\\_MAIN": 2, "D6\\_UPPER": 3}
    reorder_table_rows(
        a2,
        lambda line: (
            POP_ORDER[line.split(" & ", 1)[0]],
            model_order[line.split(" & ")[1]],
        ),
    )
    a3 = FINAL / "tables/tableA3_full_ablation.tex"
    source_lines = [
        line for line in a3.read_text(encoding="utf-8").splitlines()
        if any(line.startswith(population + " &") for population in POP_ORDER)
    ]
    block_order = {}
    for line in source_lines:
        block = line.split(" & ")[1]
        block_order.setdefault(block, len(block_order))
    reorder_table_rows(
        a3,
        lambda line: (
            block_order[line.split(" & ")[1]],
            POP_ORDER[line.split(" & ", 1)[0]],
        ),
    )
    a4 = FINAL / "tables/tableA4_full_robustness.tex"
    protocol_order = {
        "Matched-support spatial": 0,
        "Family-group holdout": 1,
        "SAFE temporal": 2,
        "Qing dynasty holdout": 3,
        "Source group": 4,
    }
    reorder_table_rows(
        a4,
        lambda line: (
            protocol_order[line.split(" & ")[2]],
            POP_ORDER.get(line.split(" & ", 1)[0], 9),
            line.split(" & ")[1],
        ),
    )
    a4_text = a4.read_text(encoding="utf-8")
    a4_text = a4_text.replace(
        "\\begin{longtable}{p{0.06\\textwidth}p{0.12\\textwidth}p{0.13\\textwidth}rrrrp{0.16\\textwidth}}",
        "\\begingroup\n\\setlength{\\tabcolsep}{3pt}\n"
        "\\begin{longtable}{>{\\raggedright\\arraybackslash}p{1.60cm}>{\\raggedright\\arraybackslash}p{2.00cm}"
        ">{\\raggedright\\arraybackslash}p{2.60cm}"
        ">{\\centering\\arraybackslash}p{1.45cm}>{\\centering\\arraybackslash}p{1.45cm}"
        ">{\\centering\\arraybackslash}p{1.45cm}>{\\centering\\arraybackslash}p{1.45cm}"
        ">{\\raggedright\\arraybackslash}p{3.60cm}}",
    )
    a4_text = a4_text.replace("\\end{longtable}\n", "\\end{longtable}\n\\endgroup\n")
    a4_text = a4_text.replace(
        "H\\_STRUCT/D5\\_MAIN & Source group",
        "H\\_\\allowbreak STRUCT/\\allowbreak D5\\_\\allowbreak MAIN & Source group",
    )
    a4.write_text(a4_text, encoding="utf-8")
    table5 = FINAL / "tables/table5_robustness.tex"
    text = table5.read_text(encoding="utf-8")
    text = text.replace(
        "Distribution-shift evidence and its availability. Missing performance is labeled explicitly; Phase 3 did not create post-hoc temporal or Qing performance.",
        "Distribution-shift evidence and its availability. Whole-family rows apply only to the frozen F2 structural comparator in Global and Ming; missing performance is labeled explicitly.",
    )
    table5.write_text(text, encoding="utf-8")


def compress_main_text(text: str) -> tuple[str, int, int]:
    before = len(re.findall(r"\b[\w'-]+\b", text[:text.index("\\label{mainend}")]))
    related_old = """\\textbf{Computational prosopography.} CBDB structures biographical information from heterogeneous historical texts for statistical, network, spatial, and reference uses \\cite{tsui2020harvesting,chenwang2022cbdb}. Its relational network representation supports kinship and association analysis, while historical GIS connects person-level records to spatial aggregation \\cite{fullerwang2021networks,bol2012gis}. The official guide documents schema and export procedures rather than supplying evidence of complete historical coverage \\cite{fuller2024}.

\\textbf{Tabular prediction.} Tree ensembles remain strong baselines on many heterogeneous tabular tasks \\cite{grinsztajn2022tabular}. CatBoost handles categorical variables through ordered target-statistic procedures designed to limit target leakage \\cite{prokhorenkova2018catboost}. We use these established methods but do not treat the learner, SHAP, or calibration as methodological novelty.

\\textbf{Structured generalization.} Random holdout can understate error when observations share spatial, temporal, or hierarchical dependence \\cite{roberts2017cv}. Covariate shift also breaks the assumption that ordinary validation represents the deployment distribution \\cite{sugiyama2007covariate}. WILDS formalizes naturally occurring shifts, while transport research shows why predictive mechanisms can fail across changed environments \\cite{koh2021wilds,subbaswamy2019transport}. Our family and spatial tests assess transport under stated shifts, not external historical truth.

\\textbf{Documentation and measurement.} Administrative records inherit institutional selection and data-generation processes \\cite{hand2018administrative}. Measurement work distinguishes latent constructs from their operationalizations, and label-noise research describes how imperfect labels change classification evidence \\cite{jacobs2021measurement,frenay2014label}. We use this literature conceptually: $E$ is an explicit proxy, not an assumed random corruption of $T$. Dataset documentation should also expose collection, composition, and recommended use \\cite{gebru2021datasheets}.

\\textbf{Attribution and calibration.} SHAP provides additive model attributions, but Shapley values are not context-free feature importance or causal effects \\cite{lundberg2017shap,kumar2020shap}. Probability calibration is a separate diagnostic that must use held-out fitting data rather than test labels \\cite{niculescu2005probabilities,guo2017calibration}. These boundaries determine how we report both analyses."""
    related_new = """\\textbf{Computational prosopography.} CBDB supports statistical, network, spatial, kinship, and reference analysis of heterogeneous historical texts \\cite{tsui2020harvesting,chenwang2022cbdb,fullerwang2021networks,bol2012gis}. Its official guide documents schema and export procedures, not complete historical coverage \\cite{fuller2024}.

\\textbf{Prediction and generalization.} Tree ensembles are strong heterogeneous-tabular baselines, and CatBoost limits target leakage in categorical statistics \\cite{grinsztajn2022tabular,prokhorenkova2018catboost}. Random holdout can be optimistic under structured dependence, while covariate shift can invalidate ordinary validation \\cite{roberts2017cv,sugiyama2007covariate}. WILDS and transport research motivate explicitly bounded shift tests \\cite{koh2021wilds,subbaswamy2019transport}.

\\textbf{Measurement, attribution, and calibration.} Administrative data inherit selection processes; operational measures need not equal latent constructs, and imperfect labels alter classification evidence \\cite{hand2018administrative,jacobs2021measurement,frenay2014label}. Dataset documentation should expose these boundaries \\cite{gebru2021datasheets}. SHAP is neither context-free importance nor causal evidence, and calibration requires held-out fitting data \\cite{lundberg2017shap,kumar2020shap,niculescu2005probabilities,guo2017calibration}."""
    text = require_replace(text, related_old, related_new)
    text = require_replace(
        text,
        "CBDB coverage and $E$ prevalence vary sharply across the five largest dynastic groups (Figure~\\ref{fig:dynasty}). Tang contains 57,477 covered people with 3.17\\% $E$ prevalence, whereas Song contains 83,373 with 48.27\\%. Yuan contains 25,310 with 9.21\\%, Ming contains 225,403 with 19.93\\%, and Qing contains 237,423 with 54.54\\%. These contrasts can reflect historical institutions, corpus composition, database projects, and source survival. The present data cannot identify their separate effects.",
        "Across Tang, Song, Yuan, Ming, and Qing, CBDB coverage ranged from 25,310 to 237,423 people and $E$ prevalence from 3.17\\% to 54.54\\% (Figure~\\ref{fig:dynasty}). Historical institutions, corpus composition, database projects, and source survival remain inseparable explanations.",
    )
    text = require_replace(
        text,
        "Recorded gender is equally imbalanced. Globally, 87.55\\% of covered people are male; $E$ prevalence is 37.96\\% for recorded men, 1.22\\% for recorded women, and 0.79\\% for unknown gender. These values show a strong predictive partition, not a historical comparison of opportunity. Gendered source production, inclusion, and encoding remain plausible alternatives to institutional explanations.",
        "Recorded gender is also imbalanced: 87.55\\% of covered people are male, and $E$ prevalence is 37.96\\% for men, 1.22\\% for women, and 0.79\\% for unknown gender. This predictive partition is not a historical comparison of opportunity.",
    )
    text = require_replace(
        text,
        "ENTRY pathways also change across dynasties (Figure~\\ref{fig:pathways}). Examination or degree records dominate several groups, while schooling, recommendation, privilege, military, and appointment pathways vary. Person-level categories are nonexclusive, so their prevalence can exceed a compositional total. The display establishes heterogeneous label construction but cannot determine whether that heterogeneity reflects historical access, changing terminology, or differential source processing.",
        "ENTRY pathways vary across dynasties (Figure~\\ref{fig:pathways}). Examination, schooling, recommendation, privilege, military, and appointment categories are nonexclusive at person level. Their heterogeneity may reflect historical access, terminology, or source processing.",
    )
    text = require_replace(
        text,
        "Observability varies across feature families. Addresses are recorded for 59.83\\% of people, any kin for 43.29\\%, and core family for 33.94\\%. Valid coordinates cover 57.82\\%, but safe birth years cover only 9.05\\%. Mean documentation intensity is 1.21 recorded domains globally and differs across Song, Ming, and Qing. Its association with $E$ is nonlinear, which indicates mixed source regimes rather than a single monotone completeness scale. Together, these distributions show why models can learn the production of records alongside historical attributes.",
        "Observability differs by feature: addresses cover 59.83\\% of people, any kin 43.29\\%, core family 33.94\\%, valid coordinates 57.82\\%, and safe birth years 9.05\\%. Documentation intensity also varies by population, allowing models to learn record production alongside historical attributes.",
    )
    text = require_replace(
        text,
        "Personal features comprise recorded gender, historical regime, and audited birth cohort. Geographic features separate address observability, historical administrative identifiers, valid coordinates, distance to a dynasty capital, training-region density, address-record semantics, and the supervised local prior. Family features separate observability, identified relations, topology, and political-capital summaries. Documentation flags describe whether association, status, text, or institutional relations are recorded.",
        "Features separate personal attributes; address observability, administrative and physical geography, density, semantics, and local prior; family observability, topology, and capital; and general documentation flags.",
    )
    text = require_replace(
        text,
        "Each grouping has an interpretation boundary. Administrative identifiers may encode both historical place and editorial normalization. Address and kin flags measure database observability directly. Family topology is partly transductive because relations connect people in the same database snapshot. Full-record political capital uses relatives' lifetime outcomes; the train-observed alternative restricts whose outcomes are visible but is still not strictly pre-entry. These distinctions are preserved in grouped ablations rather than collapsed into one feature-importance ranking.",
        "Administrative identifiers mix place and normalization; address and kin flags directly measure observability; family topology is partly transductive; and relatives' outcomes are not strictly pre-entry. Grouped ablations preserve these boundaries.",
    )
    text = require_replace(
        text,
        "Grouped SHAP passed additivity checks for all nine population-model pairs. Figure~\\ref{fig:shap} shows that personal gender, historical regime, administrative geography, family topology, and documentation-linked groups redistribute attribution across populations. The canonical group name \\texttt{historical\\_regime} replaces the ambiguous label \\texttt{other}; only the label and aggregation output changed, not models or SHAP values.",
        "Grouped SHAP passed additivity checks for all nine population-model pairs (Figure~\\ref{fig:shap}). Attribution shifted across populations; renaming \\texttt{other} to \\texttt{historical\\_regime} changed only the display aggregation.",
    )
    text = require_replace(
        text,
        "The comparison also exposes why attribution is subordinate to ablation. Song's supervised local prior receives a sizable SHAP share although its conditional ablation increment is near zero. D6\\_UPPER assigns \\DsiFamilyShare{} of Global absolute attribution to full-record family capital, yet that group's independent performance increment is small. Correlated or substitutable predictors can receive attribution without adding comparable conditional information. SHAP attribution is therefore neither an independent contribution nor a causal effect \\cite{lundberg2017shap,kumar2020shap}.",
        "Song's local prior receives substantial SHAP share despite a near-zero conditional increment, and D6\\_UPPER assigns \\DsiFamilyShare{} of Global attribution to family capital despite its small increment. Correlated predictors can redistribute attribution, so SHAP is neither independent contribution nor causal effect \\cite{lundberg2017shap,kumar2020shap}.",
    )
    discussion_old = """Taken together, the results establish strong within-database prediction and a narrower interpretive conclusion. Structural attributes and database observability are entangled in CBDB, but grouped ablations make parts of that entanglement visible. The high H\\_STRUCT result does not remove documentation bias because its geography and family blocks include observability. The D5\\_MAIN gain shows that additional documentation-linked structure improves prediction, while D6\\_UPPER shows little remaining discrimination from relatives' lifetime records.

This reading connects prosopographical analysis with broader concerns about administrative data and operational measurement \\cite{hand2018administrative,jacobs2021measurement}. The relevant contribution is not that CatBoost predicts well. It is an auditable separation between label semantics, structural benchmarks, documentation-linked increments, political-capital increments, and shift boundaries. Spatial degradation further shows that random primary-test performance does not summarize transport to unseen historical regions. Whole-family evidence is narrower: it supports only the frozen F2 comparator in Global and Ming, not D5\\_MAIN.

The evidence cannot identify which historical institutions or source practices caused these patterns. A strong gender or regime signal can reflect historical stratification, textual survival, editorial selection, encoding, or combinations of them. Likewise, family topology can summarize relational structure and database completeness simultaneously. These alternatives require source-specific or temporally anchored designs beyond the current record snapshot."""
    discussion_new = """The results establish strong within-database prediction while exposing its documentary basis. H\\_STRUCT retains observable geography and kin structure, D5\\_MAIN gains from additional documentation-linked signals, and D6\\_UPPER adds little discrimination from relatives' lifetime records.

The contribution is an auditable separation of label semantics, structural and documentation-linked increments, family-capital increments, and shift boundaries \\cite{hand2018administrative,jacobs2021measurement}. Spatial degradation limits random-holdout transport, while whole-family evidence supports only F2 in Global and Ming, not D5\\_MAIN.

Gender, regime, and family signals may reflect historical stratification, textual survival, editorial selection, encoding, or their combination. Source-specific or temporally anchored designs are needed to distinguish these explanations."""
    text = require_replace(text, discussion_old, discussion_new)
    text = require_replace(
        text,
        "$E$ measures ENTRY-record presence rather than $T$, while $P$ is also incomplete historical ground truth. ENTRY categories combine credentials, education, recommendation, privilege, military, appointment, and ambiguous pathways. The models therefore classify a heterogeneous operational label. Bootstrap intervals quantify resampling variability for that label but omit uncertainty in its definition and historical validity.",
        "$E$ measures heterogeneous ENTRY-record presence, not $T$; $P$ is also incomplete. Bootstrap intervals cover test-sample variation for $E$, not its definition or historical validity.",
    )
    text = require_replace(
        text,
        "CBDB is a nonrandom sample shaped by surviving sources, source-specific projects, and editorial encoding. Coverage is uneven across period, region, gender, relation type, and documentation intensity. These processes may affect both predictors and $E$, so high discrimination cannot be interpreted as population prevalence or historical mechanism. Source coverage remains especially important because confirmation was infeasible under the prespecified full-coverage connected-component protocol.",
        "CBDB selection varies across period, region, gender, relations, and documentation. Because these processes affect predictors and $E$, discrimination is neither population prevalence nor historical mechanism. Source confirmation was infeasible under the prespecified full-coverage connected-component protocol.",
    )
    text = require_replace(
        text,
        "D5\\_MAIN is retrospective classification, not strict prospective prediction. Safe birth years cover only 9.05\\% globally, which prevents broad pre-entry temporal anchoring. Some family topology is transductive within the database snapshot, and relatives' lifetime outcomes have temporal ambiguity. D6\\_UPPER and full-record family-capital results must therefore remain database-internal bounds.",
        "D5\\_MAIN is retrospective, and 9.05\\% safe-birth coverage prevents broad pre-entry anchoring. Family topology is partly transductive and relatives' lifetime outcomes are temporally ambiguous, restricting D6\\_UPPER and family capital to database-internal bounds.",
    )
    text = require_replace(
        text,
        "Matched-support spatial performance declined, and calibration need not remain stable under a changed distribution. Temporal and Qing conclusions lack frozen locked-model performance, while source-group confirmation was infeasible under the prespecified full-coverage connected-component protocol. Whole-family performance applies only to the F2 structural comparator in Global and Ming; D5\\_MAIN was not directly evaluated under family-group holdout. The primary test was viewed across multiple project phases, creating researcher-adaptation risk despite frozen models and no test-set tuning. SHAP remains non-causal, and its stability does not resolve these generalization boundaries.",
        "Spatial shift weakened performance, while temporal, Qing, and source-group locked performance is unavailable. Whole-family performance applies only to F2 in Global and Ming, not D5\\_MAIN. Repeated project-phase test viewing creates adaptation risk; SHAP remains non-causal.",
    )
    text = require_replace(
        text,
        "CBDB ENTRY-record presence is highly predictable on the frozen primary test. Grouped evidence locates that predictability in personal structure, historical regime, geography, family observability, topology, and documentation. Family-capital increments are small after observability and topology and are uncertain in Ming, while unseen-region transport is weaker. Whole-family robustness evidence is limited to the F2 structural comparator. This is an account of structured record presence, not true historical entry or causal office access.",
        "CBDB ENTRY-record presence is highly predictable within the frozen database. Observability and topology dominate small, Ming-uncertain family-capital increments, and unseen-region transport is weaker. Whole-family evidence is F2-only. These results concern structured records, not true entry or causal office access.",
    )
    text = require_replace(
        text,
        "This study reuses third-party CBDB data available through the official project and SQLite release channel \\cite{cbdb2026,fuller2024}. The assignment brief reports approximately 515,488 people, whereas the verified release used in this study contains 661,124 \\texttt{BIOG\\_MAIN} person records. CBDB counts are release-specific; all results here refer only to \\texttt{cbdb\\_20260829.sqlite3}. The downloader verifies this release against the SHA256 recorded in the package manifest. Raw and working SQLite files are not redistributed, and users remain responsible for CBDB access terms. The review artifact contains final test predictions, tables, and figure-source snapshots. Excluded feature matrices and regenerable intermediates can be rebuilt from the verified release. Neither the source data nor the package is represented as a historical census.",
        "This study reuses third-party CBDB data from the official release channel \\cite{cbdb2026,fuller2024}. The brief reports about 515,488 people; the verified \\texttt{cbdb\\_20260829.sqlite3} release contains 661,124 \\texttt{BIOG\\_MAIN} records. Counts are release-specific, and all results use that release. Its SHA256 is verified. SQLite files are not redistributed; the package provides predictions, tables, figure sources, and regeneration code under CBDB access terms.",
    )
    text = require_replace(
        text,
        "The package contains hash verification, preprocessing, frozen splits, feature construction, evaluation, figures, environments, and tests. Code and documentation use the MIT License, which grants no CBDB redistribution rights. No repository DOI or accession is claimed.",
        "The package contains verification, preprocessing, frozen splits, features, evaluation, figures, environments, and tests. Its MIT License grants no CBDB redistribution rights, and no repository identifier is claimed.",
    )
    text = require_replace(
        text,
        "Seed 42 and person-level splits are frozen; test labels selected neither hyperparameters nor calibration. The package records versions, features, parameters, model and artifact hashes, and corrections. Run \\texttt{bash scripts/run\\_phase3\\_1\\_1\\_final\\_polish.sh} from the frozen artifacts.",
        "Seed 42 and person splits are frozen; test labels selected neither hyperparameters nor calibration. Versions, parameters, hashes, and corrections are recorded. Run \\texttt{bash scripts/run\\_phase3\\_1\\_1\\_final\\_polish.sh}.",
    )
    after = len(re.findall(r"\b[\w'-]+\b", text[:text.index("\\label{mainend}")]))
    return text, before, after


def build_body() -> None:
    text = (REVISED / "main_body_revised.tex").read_text(encoding="utf-8")
    text = text.replace("\\bibliography{references_revised}", "\\bibliography{references_final}")
    text = require_replace(
        text,
        "Full-coverage source grouping was not completed because \\SourceLargest{} of \\SourceEligible{} eligible people formed one connected component.",
        "Full-coverage source-group confirmation was infeasible under the prespecified connected-component protocol because 448,632 of 452,035 eligible people belonged to a single connected component.",
    )
    text = require_replace(
        text,
        "This selection creates a specific prediction problem.",
        "This study combines open-ended exploratory analysis of dynastic, gender, ENTRY-pathway, geographic, and kin-observability patterns with predictive modeling of ENTRY-record presence.\n\nThis selection creates a specific prediction problem.",
    )
    text = require_replace(
        text,
        "\\texttt{cbdb\\_20260829.sqlite3}. CBDB is a selectively assembled",
        "\\texttt{cbdb\\_20260829.sqlite3}. The assignment brief reports approximately 515,488 people, whereas the verified release used in this study contains 661,124 \\texttt{BIOG\\_MAIN} person records. CBDB counts are release-specific; all results here refer only to \\texttt{cbdb\\_20260829.sqlite3}. CBDB is a selectively assembled",
    )
    text = require_replace(
        text,
        "E, P, and T are not semantically equivalent.",
        "E, P, and T are distinct constructs and are not semantically equivalent.",
    )
    text = require_replace(
        text,
        "\\caption{\\textbf{Observed database labels and latent historical concepts.} \\textbf{a}, Historical entry or credential events, posting or office-holding events, and other biographical processes pass through source survival, editorial extraction, and database encoding. $T$ denotes latent true historical entry; $E$ and $P$ are semantically distinct incomplete observations. \\textbf{b}, Frozen contingency for all \\NPeople{} CBDB-covered people.}",
        "\\caption{\\textbf{Constructs, historical events, and recorded labels.} \\textbf{a}, $T$ is latent true historical entry. Credential, education, recommendation, privilege, and other entry-related events are not $T$; posting or office-holding events are related to, but not equivalent to, $T$. Source survival, extraction, and encoding produce the observed $E$ and $P$ relations. $E$, $P$, and $T$ are distinct constructs and are not interchangeable. \\textbf{b}, Frozen contingency for all \\NPeople{} CBDB-covered people.}",
    )
    text = require_replace(
        text,
        "\\textbf{RQ4} asks whether models transport to unseen families and historical regions.",
        "\\textbf{RQ4} asks how the frozen F2 structural comparator changes under whole-family grouping and how locked models transport to unseen historical regions.",
    )
    text = require_replace(
        text,
        "Regional density is fitted on training people only, while the local ENTRY prior is out-of-fold on training data and transformed forward.",
        "Regional density is fitted on training people only. The local ENTRY prior groups the exact \\texttt{addr\\_id} key, applies five-fold deterministic out-of-fold encoding with smoothing strength 20 on training people, and transforms validation or test people from the complete-training mapping; unseen keys use the relevant training mean.",
    )
    text = require_replace(
        text,
        "A source-group model was conditional on a feasibility gate and was not fitted when that gate failed.",
        "A source-group model was conditional on a feasibility gate and was not fitted because full-coverage confirmation was infeasible under the prespecified full-coverage connected-component protocol.",
    )
    text = require_replace(
        text,
        "\\subsection{Locked discrimination establishes the predictive ceiling}",
        "\\subsection{Locked models establish strong within-database discrimination}",
    )
    text = require_replace(text, "Physical Geography changed ROC-AUC", "Physical geography changed ROC-AUC")
    text = require_replace(
        text,
        "Its exact A2/A3 paired predictions were not retained, so no valid confidence interval is reported.",
        "Its exact A2/A3 paired predictions were not retained, so no valid confidence interval is reported. Because the grouped ablations follow a prespecified nested order, every increment is conditional on the blocks already entered. The increments are therefore order-dependent and cannot be interpreted as unique contributions or causal effects.",
    )
    text = require_replace(
        text,
        "Whole-family holdout produced smaller degradation for the F2 structural comparator (Table~\\ref{tab:robustness}). Family observability dominated topology and both political-capital variants across the three populations (Figure~\\ref{fig:family}). This decomposition argues against treating family-capital association as the main independent signal.",
        "Whole-family robustness was evaluated only for the frozen F2 structural comparator in Global and Ming. Family-group robustness of D5\\_MAIN was not directly evaluated. Globally and in Song, family-capital increments were small and mostly positive. The full-record F3--F2 ROC-AUC increment was +0.000701 globally and +0.001821 in Song. In Ming, the full-record increment was -0.000319 (95\\% CI [-0.0009, 0.0002]) and the train-observed F4--F2 increment was -0.000394 (95\\% CI [-0.0010, 0.0002]); the corresponding Ming PR-AUC intervals also included zero. Across populations, family observability and topology contributed much more predictive information than family-capital summaries (Figure~\\ref{fig:family}).",
    )
    text = require_replace(
        text,
        "Full-coverage source-group confirmation was infeasible under the prespecified connected-component protocol.",
        "Full-coverage source-group confirmation was infeasible under the prespecified full-coverage connected-component protocol.",
    )
    text = require_replace(
        text,
        "This result does not establish that every form of source validation is impossible.",
        "This protocol result does not rule out a narrower source-specific validation design.",
    )
    text = require_replace(
        text,
        "\\caption{\\textbf{Grouped mean absolute SHAP shares.} Global, Song, and Ming panels compare H\\_STRUCT, D5\\_MAIN, and D6\\_UPPER. Blank cells denote groups absent from a model. Shares are fitted-model attributions, not conditional gains or causal effects.}",
        "\\caption{\\textbf{Grouped mean absolute SHAP shares.} Global, Song, and Ming panels compare H\\_STRUCT, D5\\_MAIN, and D6\\_UPPER. Physical geography comprises latitude, longitude, and distance to the dynasty-specific capital. Blank cells denote groups absent from a model. Shares are fitted-model attributions, not conditional gains or causal effects.}",
    )
    text = require_replace(
        text,
        "Spatial degradation further shows that random primary-test performance does not summarize transport to unseen historical regions.",
        "Spatial degradation further shows that random primary-test performance does not summarize transport to unseen historical regions. Whole-family evidence is narrower: it supports only the frozen F2 comparator in Global and Ming, not D5\\_MAIN.",
    )
    text = require_replace(
        text,
        "Source coverage remains especially important because full-coverage connected-component grouping failed its feasibility gate.",
        "Source coverage remains especially important because confirmation was infeasible under the prespecified full-coverage connected-component protocol.",
    )
    text = require_replace(
        text,
        "Temporal and Qing conclusions lack frozen locked-model performance, while source-group confirmation was infeasible under the full-coverage protocol.",
        "Temporal and Qing conclusions lack frozen locked-model performance, while source-group confirmation was infeasible under the prespecified full-coverage connected-component protocol. Whole-family performance applies only to the F2 structural comparator in Global and Ming; D5\\_MAIN was not directly evaluated under family-group holdout.",
    )
    text = require_replace(
        text,
        "Recorded family political capital adds little after those blocks, while unseen-region transport is weaker.",
        "Family-capital increments are small after observability and topology and are uncertain in Ming, while unseen-region transport is weaker. Whole-family robustness evidence is limited to the F2 structural comparator.",
    )
    text = require_replace(
        text,
        "The input was \\texttt{cbdb\\_20260829.sqlite3}; the downloader verifies it against the official SHA256 recorded in the review manifest.",
        "The assignment brief reports approximately 515,488 people, whereas the verified release used in this study contains 661,124 \\texttt{BIOG\\_MAIN} person records. CBDB counts are release-specific; all results here refer only to \\texttt{cbdb\\_20260829.sqlite3}. The downloader verifies this release against the SHA256 recorded in the package manifest.",
    )
    text = require_replace(
        text,
        "Run \\texttt{bash scripts/run\\_phase3\\_1\\_nature\\_revision.sh} from the frozen artifacts.",
        "Run \\texttt{bash scripts/run\\_phase3\\_1\\_1\\_final\\_polish.sh} from the frozen artifacts.",
    )
    text, words_before, words_after = compress_main_text(text)
    text = text.replace(
        "Run \\texttt{bash scripts/run\\_phase3\\_1\\_1\\_final\\_polish.sh}.",
        "Run \\texttt{bash} \\path{scripts/run_phase3_1_1_final_polish.sh}.",
    )
    text = text.replace(
        "From the project root, run \\texttt{bash scripts/run\\_phase3\\_1\\_1\\_final\\_polish.sh}.",
        "From the project root, run \\texttt{bash} \\path{scripts/run_phase3_1_1_final_polish.sh}.",
    )
    text = text.replace("\\usepackage{array}", "\\usepackage{array}\n\\setlength{\\emergencystretch}{1.5em}")
    text = require_replace(
        text,
        """\\clearpage
\\label{appendixstart}
\\appendix
\\setcounter{figure}{0}
\\setcounter{table}{0}
\\renewcommand{\\thefigure}{A\\arabic{figure}}
\\renewcommand{\\thetable}{A\\arabic{table}}
""",
        """\\clearpage
\\label{appendixstart}
\\appendix
\\onecolumn
\\setcounter{figure}{0}
\\setcounter{table}{0}
\\renewcommand{\\thefigure}{A\\arabic{figure}}
\\renewcommand{\\thetable}{A\\arabic{table}}
""",
    )
    before_appendix, appendix = text.split("\\label{appendixstart}", maxsplit=1)
    appendix = appendix.replace("\\begin{figure*}[h]", "\\begin{figure}[!htbp]")
    appendix = appendix.replace("\\end{figure*}", "\\end{figure}")
    appendix = appendix.replace(
        "\\includegraphics[width=\\textwidth]{figures/figA",
        "\\includegraphics[width=0.84\\textwidth]{figures/figA",
    )
    text = before_appendix + "\\label{appendixstart}" + appendix
    local_method = r"""
\section{Exact Local Target-Prior Construction}
For population-specific training data, let \(r_i\) be the exact \texttt{addr\_id} key for person \(i\); missing keys are mapped to the literal group \texttt{\_\_MISSING\_\_}. With smoothing strength \(\alpha=20\), regional target sum \(s_r\), regional count \(n_r\), and fitting-sample target mean \(\mu\), the encoder is
\begin{equation}
\widehat p_r=\frac{s_r+\alpha\mu}{n_r+\alpha}.
\end{equation}
Training values use five deterministic out-of-fold partitions. A person's fold is the little-endian integer represented by the first eight bytes of \(\operatorname{SHA256}(\texttt{42|person\_id})\), modulo five. For a row held out in fold \(f\), \(s_{r,-f}\), \(n_{r,-f}\), and \(\mu_{-f}\) use only other folds; a key unseen outside \(f\) receives \(\mu_{-f}\). The row's own label and all labels in its fold are therefore excluded.

After producing training OOF values, the encoder is fitted on the complete training partition. Validation and test transformations read region keys but no held-out labels; unseen keys receive the complete-training mean. Encoders are fitted separately for Global, Song, and Ming and refitted within primary, matched-random, and matched-spatial protocols. There is no hierarchical geographic backoff, minimum-count pooling, coordinate-nearest fallback, or external prior. The machine-readable specification is distributed as \texttt{local\_target\_prior\_spec.json}.
"""
    text = require_replace(
        text,
        "\\section{Additional Diagnostics}",
        local_method + "\n\\section{Additional Diagnostics}",
    )
    text = require_replace(
        text,
        "\n\\clearpage\n\\onecolumn\n\\section{Frozen Parameters and Full Results}\n\\small\n\\input{tables/tableA1_model_parameters}",
        "\n\\FloatBarrier\n\\section{Frozen Parameters and Full Results}\n\\input{tables/tableA1_model_parameters}\n\\begingroup\n\\renewcommand{\\thetable}{A1b}\n\\renewcommand{\\theHtable}{A1b}\n\\input{tables/tableA1b_operating_parameters}\n\\endgroup\n\\setcounter{table}{1}",
    )
    text = require_replace(
        text,
        "From the project root, run \\texttt{bash scripts/run\\_phase3\\_1\\_nature\\_revision.sh}. The runner verifies frozen inputs, rebuilds Phase 3.1 tables and figures, compiles both manuscripts, runs audits and tests, packages the deliverables, and validates both archives.",
        "From the project root, run \\texttt{bash scripts/run\\_phase3\\_1\\_1\\_final\\_polish.sh}. The runner verifies the Phase 3.1 baseline, rebuilds only Phase 3.1.1 tables and figures, compiles both manuscripts, renders every PDF page, runs audits and tests, packages the deliverables, and validates both archives.",
    )
    banned = [
        "predictive ceiling", "source grouping was not completed",
        "every form of source validation is impossible", "gate failed",
    ]
    present = [phrase for phrase in banned if phrase in text]
    if present:
        raise RuntimeError(f"Banned final wording remains: {present}")
    (FINAL / "main_body_final.tex").write_text(text, encoding="utf-8")
    (DOCS / "nature_polishing_audit.md").write_text(
        "# Nature-polishing audit\n\n"
        "Scientific facts, metrics, method definitions, and evidence boundaries were frozen before this pass. "
        "The pass removed repeated background, display narration, and duplicated boundary statements without "
        "changing any frozen numerical value.\n\n"
        "## Main-text discipline audit\n\n"
        f"- Main-text word count before compression: {words_before}\n"
        f"- Main-text word count after compression: {words_after}\n"
        f"- Net change: {words_after - words_before}\n"
        "- Kept in main text: construct boundary, headline metrics, Physical geography CI absence, F2-only family scope, Ming intervals crossing zero, spatial transport, source-protocol infeasibility, and adaptive-test limitation.\n"
        "- Compressed: literature catalogue, EDA values already visible in figures, repeated SHAP explanation, Discussion replay, and availability boilerplate.\n"
        "- Relocated/retained in appendix: exact local-prior formula, complete tables, calibration, multiseed, and robustness-support details.\n"
        "- Typography: no font, margin, or line-spacing reduction was used.\n",
        encoding="utf-8",
    )


def write_wrappers() -> None:
    (FINAL / "main_author_final.tex").write_text(
        "\\newif\\ifanonymous\n\\anonymousfalse\n"
        "\\newcommand{\\PaperAuthorName}{Xiaoke Lu}\n"
        "\\newcommand{\\PaperInstitution}{ShanghaiTech University}\n"
        "\\input{main_body_final}\n",
        encoding="utf-8",
    )
    (FINAL / "main_anonymous_final.tex").write_text(
        "\\newif\\ifanonymous\n\\anonymoustrue\n\\input{main_body_final}\n",
        encoding="utf-8",
    )


def write_claim_map() -> None:
    existing = (ROOT / "docs/phase3_1/final_claim_evidence_map.md").read_text(encoding="utf-8")
    rows = [
        ("P311-01", "Data snapshot scope", "The assignment brief and verified release have different person counts; every result uses cbdb_20260829.sqlite3 with 661,124 BIOG_MAIN rows.", "README.md; Section 3; Data Availability; baseline_sha256.tsv", "Release-specific count, not a claim that either count is universally correct."),
        ("P311-02", "T/E/P boundary", "T is latent true historical entry; entry-related events, posting events, E, and P are distinct constructs.", "Figure 1; entry_vs_posting_contingency.csv; target audit", "E and P are incomplete observed relations and are not interchangeable with T."),
        ("P311-03", "Local target prior", "local_target_prior uses exact addr_id groups, alpha=20, five-fold deterministic OOF training encoding, and training-mean fallback.", "local_target_prior_spec.json; src/geography.py; configs/phase2_6_features.yaml; method tests", "No hierarchy or minimum-count pooling; held-out labels are never used."),
        ("P311-04", "Family holdout scope", "Whole-family performance was evaluated only for frozen F2 in Global and Ming; D5_MAIN was not directly evaluated.", "robustness_summary.csv; Table 5; Table A4", "Cannot generalize F2 family robustness to D5_MAIN."),
        ("P311-05", "Ming family capital", "Ming F3-F2 and F4-F2 ROC-AUC intervals and corresponding PR-AUC intervals include zero.", "Table A3; paired_bootstrap_results.csv; Figure 7", "Absence of clear incremental evidence is not proof of no effect."),
        ("P311-06", "Nested ablation order", "Every grouped increment is conditional on the frozen nested order.", "Table A3; grouped_ablation_corrected.csv; Methods", "Not a unique contribution, permutation importance, or causal effect."),
        ("P311-07", "Operating points and shift support", "Selected thresholds, retained weighting schemes, sigmoid parameters, and all shift supports are reported from existing artifacts.", "operating_parameters.csv; split_support_summary.csv; shift_support_summary.csv; Table A1b", "Numeric class weights and Logistic calibrators are NOT_RETAINED rather than reconstructed."),
    ]
    lines = [
        existing.rstrip(), "", "## Phase 3.1.1 additions and scope corrections", "",
        "| claim_id | claim_type | final claim | evidence | boundary |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    (DOCS / "final_claim_evidence_map.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    FINAL.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    copy_inputs()
    reorder_appendix_tables()
    build_body()
    write_wrappers()
    write_claim_map()
    print("PASS: Phase 3.1.1 final manuscript sources and claim map prepared")


if __name__ == "__main__":
    main()
