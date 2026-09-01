#!/usr/bin/env python3
"""Generate audited LaTeX tables, author/anonymous papers, and Chinese summary."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src.phase3 import PHASE3_DOCS, PHASE3_TABLES, ROOT, environment_payload, ensure_phase3_dirs, write_json
from src.utils import sha256_file


TABLE_DIR = ROOT / "paper/tables"
GENERATED_DIR = ROOT / "scripts/generated_tables"


def esc(value: object) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "--"
    text = str(value)
    for old, new in [("\\", "\\textbackslash{}"), ("_", "\\_"), ("%", "\\%"), ("&", "\\&"), ("#", "\\#")]:
        text = text.replace(old, new)
    return text


def write_table(name: str, body: str) -> None:
    for directory in [TABLE_DIR, GENERATED_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
        (directory / name).write_text(body.rstrip() + "\n", encoding="utf-8")


def table_dataset() -> None:
    data = pd.read_csv(PHASE3_TABLES / "dataset_target_summary.csv")
    rows = []
    for row in data.itertuples(index=False):
        value = f"{int(row.value):,}" if float(row.value).is_integer() and row.value > 1 else f"{row.value:.4f}"
        rows.append(f"{esc(row.quantity)} & {value} & {esc(row.definition)} \\\\")
    write_table("table1_dataset.tex", """\\begin{table*}[t]
\\caption{Dataset and observed targets. Counts and shares are generated from the frozen person target and E--P contingency tables.}
\\label{tab:dataset}
\\centering
\\begin{tabular}{lrl}
\\toprule
Quantity & Value & Operational definition \\\\
\\midrule
""" + "\n".join(rows) + """
\\bottomrule
\\end{tabular}
\\end{table*}""")


def table_features() -> None:
    features = pd.read_csv(ROOT / "outputs/phase2_6/tables/final_model_feature_lists.csv")
    rows = []
    roles = {
        "H_STRUCT": "Historical structural benchmark",
        "D5_MAIN": "Main predictive model",
        "D6_UPPER": "Record-structure upper bound",
    }
    for model in ["H_STRUCT", "D5_MAIN", "D6_UPPER"]:
        part = features.loc[features["model_id"].eq(model)]
        count = int(part["feature"].nunique())
        policy = {
            "H_STRUCT": "No general documentation, address type, local target prior, or relative outcomes",
            "D5_MAIN": "Documentation and topology; no relative outcomes",
            "D6_UPPER": "D5 plus full-record relative ENTRY/posting outcomes",
        }[model]
        rows.append(f"\\texttt{{{esc(model)}}} & {count} & {roles[model]} & {policy} \\\\")
    write_table("table2_features.tex", """\\begin{table*}[t]
\\caption{Locked model roles and leakage boundary. Feature counts are read from the Phase 2.6 lock artifact.}
\\label{tab:features}
\\centering
\\resizebox{\\textwidth}{!}{%
\\begin{tabular}{lrll}
\\toprule
Model & Features & Role & Boundary \\\\
\\midrule
""" + "\n".join(rows) + """
\\bottomrule
\\end{tabular}}
\\end{table*}""")


def table_performance() -> None:
    data = pd.read_csv(PHASE3_TABLES / "main_model_performance.csv")
    order = pd.Categorical(data["model_id"], ["Logistic M6", "H_STRUCT", "D5_MAIN", "D6_UPPER"], ordered=True)
    data = data.assign(_order=order).sort_values(["population", "_order"], key=lambda x: x.map({"Global": 0, "Song": 1, "Ming": 2}) if x.name == "population" else x)
    rows = []
    for row in data.itertuples(index=False):
        model = f"\\textbf{{{esc(row.model_id)}}}" if row.model_id == "D5_MAIN" else esc(row.model_id)
        ece = "--" if pd.isna(row.calibrated_ece) else f"{row.calibrated_ece:.4f}"
        rows.append(f"{row.population} & {model} & {row.roc_auc:.4f} & {row.pr_auc:.4f} & {row.log_loss:.4f} & {row.brier_score:.4f} & {ece} \\\\")
    write_table("table3_performance.tex", """\\begin{table*}[t]
\\caption{Frozen primary-test performance. ECE is after a validation-fitted sigmoid; the earlier logistic artifact did not retain a directly comparable calibrated ECE. D5\_MAIN is the designated main result.}
\\label{tab:performance}
\\centering
\\begin{tabular}{llrrrrr}
\\toprule
Population & Model & ROC-AUC & PR-AUC & LogLoss & Brier & Cal. ECE \\\\
\\midrule
""" + "\n".join(rows) + """
\\bottomrule
\\end{tabular}
\\end{table*}""")


def table_ablation() -> None:
    data = pd.read_csv(PHASE3_TABLES / "grouped_ablation_summary.csv")
    data = data.loc[data["population"].eq("Global")]
    rows = []
    for row in data.itertuples(index=False):
        roc_ci = "--" if pd.isna(row.roc_ci_lower) else f"[{row.roc_ci_lower:.4f}, {row.roc_ci_upper:.4f}]"
        pr_ci = "--" if pd.isna(row.pr_ci_lower) else f"[{row.pr_ci_lower:.4f}, {row.pr_ci_upper:.4f}]"
        rows.append(f"{esc(row.feature_block)} & {row.delta_roc_auc:+.4f} & {roc_ci} & {row.delta_pr_auc:+.4f} & {pr_ci} \\\\")
    write_table("table4_ablation.tex", """\\begin{table*}[t]
\\caption{Global grouped ablation evidence. Intervals are 500-resample paired bootstrap intervals where the exact paired predictions were retained; dashes identify contrasts without a retained exact prediction pair, not zero uncertainty.}
\\label{tab:ablation}
\\centering
\\begin{tabular}{lrrrr}
\\toprule
Feature block & $\\Delta$ROC & 95\\% CI & $\\Delta$PR & 95\\% CI \\\\
\\midrule
""" + "\n".join(rows) + """
\\bottomrule
\\end{tabular}
\\end{table*}""")


def table_robustness() -> None:
    data = pd.read_csv(PHASE3_TABLES / "robustness_summary.csv")
    selected = pd.concat([
        data.loc[(data["protocol"].eq("Matched-support spatial")) & data["population"].eq("Global")],
        data.loc[(data["protocol"].eq("Family-group holdout")) & data["population"].isin(["Global", "Ming"])],
        data.loc[data["protocol"].isin(["SAFE temporal", "Qing dynasty holdout", "Source group"])],
    ])
    rows = []
    for row in selected.itertuples(index=False):
        def f(value: object) -> str:
            return "--" if pd.isna(value) else f"{float(value):.4f}"
        rows.append(f"{esc(row.protocol)} & {esc(row.population)} & {esc(row.model_id)} & {f(row.shift_roc_auc)} & {f(row.delta_roc_auc)} & {esc(row.status)} \\\\")
    write_table("table5_robustness.tex", """\\begin{table*}[t]
\\caption{Distribution-shift evidence and its availability. Missing performance is labeled explicitly; Phase 3 did not create post-hoc temporal or Qing performance.}
\\label{tab:robustness}
\\centering
\\resizebox{\\textwidth}{!}{%
\\begin{tabular}{lllrrl}
\\toprule
Protocol & Population & Model & Shift ROC & $\\Delta$ROC & Status \\\\
\\midrule
""" + "\n".join(rows) + """
\\bottomrule
\\end{tabular}}
\\end{table*}""")


def longtable(name: str, caption: str, label: str, columns: str, header: str, rows: list[str]) -> None:
    body = """\\begin{longtable}{%s}
\\caption{%s}\\label{%s}\\\\
\\toprule
%s \\\\
\\midrule
\\endfirsthead
\\toprule
%s \\\\
\\midrule
\\endhead
%s
\\bottomrule
\\end{longtable}""" % (columns, caption, label, header, header, "\n".join(rows))
    write_table(name, body)


def appendix_tables() -> None:
    model_config = yaml.safe_load((ROOT / "configs/phase2_6_models.yaml").read_text())
    cb = model_config["catboost"]
    parameter_rows = [
        f"{esc(key)} & {esc(value)} \\\\"
        for key, value in [
            ("canonical_seed", model_config["canonical_seed"]),
            ("iterations", cb["iterations"]),
            ("learning_rate", cb["learning_rate"]),
            ("depth", cb["depth"]),
            ("loss_function", cb["loss_function"]),
            ("eval_metric", cb["eval_metric"]),
            ("l2_leaf_reg", cb["l2_leaf_reg"]),
            ("early_stopping_rounds", cb["early_stopping_rounds"]),
            ("class_weight_candidates", str(cb["class_weight_candidates"])),
            ("bootstrap_resamples", model_config["bootstrap_resamples"]),
            ("calibration_bins", model_config["calibration_bins"]),
        ]
    ]
    longtable(
        "tableA1_model_parameters.tex",
        "Frozen CatBoost and evaluation parameters. Validation chooses early stopping, class weighting, and thresholds; the test does not.",
        "tab:app-parameters", "ll", "Parameter & Frozen value", parameter_rows,
    )

    performance = pd.read_csv(PHASE3_TABLES / "main_model_performance.csv")
    metric_rows = []
    for row in performance.itertuples(index=False):
        ece = "--" if pd.isna(row.calibrated_ece) else f"{row.calibrated_ece:.6f}"
        metric_rows.append(
            f"{esc(row.population)} & {esc(row.model_id)} & {row.test_positive_rate:.4f} & "
            f"{row.roc_auc:.6f} & {row.pr_auc:.6f} & {row.balanced_accuracy:.6f} & "
            f"{row.f1:.6f} & {row.log_loss:.6f} & {row.brier_score:.6f} & {ece} \\\\"
        )
    longtable(
        "tableA2_full_metrics.tex",
        "Full-precision locked primary-test metrics. Prevalence accompanies PR-AUC; ECE follows validation-fitted sigmoid calibration.",
        "tab:app-metrics", "llrrrrrrrr", "Population & Model & Prev. & ROC & PR & Bal. Acc. & F1 & LogLoss & Brier & ECE", metric_rows,
    )

    ablation = pd.read_csv(PHASE3_TABLES / "grouped_ablation_summary.csv")
    ablation_rows = []
    for row in ablation.itertuples(index=False):
        roc_ci = "--" if pd.isna(row.roc_ci_lower) else f"[{row.roc_ci_lower:.4f},{row.roc_ci_upper:.4f}]"
        pr_ci = "--" if pd.isna(row.pr_ci_lower) else f"[{row.pr_ci_lower:.4f},{row.pr_ci_upper:.4f}]"
        ablation_rows.append(
            f"{esc(row.population)} & {esc(row.feature_block)} & {esc(row.comparison)} & "
            f"{row.delta_roc_auc:+.6f} & {roc_ci} & {row.delta_pr_auc:+.6f} & {pr_ci} \\\\"
        )
    longtable(
        "tableA3_full_ablation.tex",
        "All grouped ablation contrasts. Intervals are shown only where the exact paired predictions were retained.",
        "tab:app-ablation", "lllrlll", "Population & Block & Contrast & $\\Delta$ROC & ROC CI & $\\Delta$PR & PR CI", ablation_rows,
    )

    robustness = pd.read_csv(PHASE3_TABLES / "robustness_summary.csv")
    robust_rows = []
    for row in robustness.itertuples(index=False):
        def value(x: object) -> str:
            return "--" if pd.isna(x) else f"{float(x):.6f}"
        breakable_status = esc(row.status).replace("\\_", "\\_\\allowbreak ")
        robust_rows.append(
            f"{esc(row.population)} & {esc(row.model_id)} & {esc(row.protocol)} & {value(row.shift_roc_auc)} & "
            f"{value(row.delta_roc_auc)} & {value(row.shift_pr_auc)} & {value(row.delta_pr_auc)} & {breakable_status} \\\\"
        )
    longtable(
        "tableA4_full_robustness.tex",
        "Complete distribution-shift evidence. Dashes preserve experiments that were unavailable or infeasible rather than inventing estimates.",
        "tab:app-robustness",
        "p{0.06\\textwidth}p{0.12\\textwidth}p{0.13\\textwidth}rrrrp{0.16\\textwidth}",
        "Population & Model & Protocol & Shift ROC & $\\Delta$ROC & Shift PR & $\\Delta$PR & Status",
        robust_rows,
    )

    features = pd.read_csv(ROOT / "outputs/phase2_6/tables/final_model_feature_lists.csv")
    feature_rows = [
        f"{esc(row.model_id)} & {esc(row.feature)} & {esc(row.role)} \\\\"
        for row in features.itertuples(index=False)
    ]
    longtable(
        "tableA5_feature_registry.tex",
        "Complete frozen feature registry. Repeated features document the exact membership of each locked model.",
        "tab:app-features", "lll", "Model & Feature & Role", feature_rows,
    )


def macros() -> None:
    perf = pd.read_csv(PHASE3_TABLES / "main_model_performance.csv")
    row = perf.loc[perf["population"].eq("Global") & perf["model_id"].eq("D5_MAIN")].iloc[0]
    source = json.loads((PHASE3_TABLES / "source_holdout_status.json").read_text())
    shap = pd.read_csv(ROOT / "outputs/phase2_6/shap/shap_group_summary.csv")
    capital = shap.loc[(shap["population"].eq("Global")) & (shap["model_id"].eq("D6_UPPER")) & (shap["feature_group"].eq("family_full_record_capital"))].iloc[0]
    content = f"""% Generated by scripts/57_write_final_paper.py from Phase 3 CSVs.
\\newcommand{{\\NPeople}}{{661{{,}}124}}
\\newcommand{{\\NEntry}}{{220{{,}}627}}
\\newcommand{{\\GlobalDfiveRoc}}{{{row.roc_auc:.6f}}}
\\newcommand{{\\GlobalDfivePr}}{{{row.pr_auc:.6f}}}
\\newcommand{{\\GlobalDfiveLogLoss}}{{{row.log_loss:.6f}}}
\\newcommand{{\\GlobalDfiveBrier}}{{{row.brier_score:.6f}}}
\\newcommand{{\\GlobalDfiveEce}}{{{row.calibrated_ece:.6f}}}
\\newcommand{{\\SourceEligible}}{{{source['eligible_people']:,}}}
\\newcommand{{\\SourceGroups}}{{{source['source_groups']:,}}}
\\newcommand{{\\SourceLargest}}{{{source['largest_group_people']:,}}}
\\newcommand{{\\SourceLargestPct}}{{{100*source['largest_group_fraction']:.2f}\\%}}
\\newcommand{{\\DsiFamilyShare}}{{{100*capital.group_share_of_total_abs_shap:.2f}\\%}}
"""
    write_table("result_macros.tex", content)


PAPER_BODY = r"""
\begin{document}
\title{Who Leaves a Recorded Path into Government?\\A Documentation-Aware Data Mining Study of CBDB}
AUTHOR_BLOCK
\begin{abstract}
The China Biographical Database (CBDB) supports large-scale study of historical people, yet its records arise from selective source survival, editorial projects, and database encoding.  We study \NPeople{} person records and predict whether a person has at least one \texttt{ENTRY\_DATA} record.  This observed database label, $E$, is not the latent historical state of true entry into government, $T$; our models estimate $\Pr(E=1\mid X)$ rather than reconstructing historical truth.  We compare a frozen logistic baseline with CatBoost models, grouped ablations, family- and spatial-shift tests, five-seed stability, calibration, and grouped SHAP.  The designated D5\_MAIN model obtains Global ROC-AUC \GlobalDfiveRoc{} and PR-AUC \GlobalDfivePr{} on the frozen primary test.  Gender, historical regime, address and kin observability, administrative geography, family topology, and documentation structure carry substantial predictive information.  In contrast, recorded family political capital adds only small conditional increments once observability and topology are included.  Matched-support tests show weaker transport to unseen historical regions.  A source-level audit finds \SourceEligible{} eligible people but a giant connected source component containing \SourceLargest{} (\SourceLargestPct{}), making leakage-free source-group confirmation infeasible under a prespecified 20\% cap.  High discrimination therefore characterizes CBDB record presence, not true historical entry; documentation bias, selection, and distribution shift remain central limitations.
\end{abstract}
\ccsdesc[500]{Computing methodologies~Supervised learning by classification}
\ccsdesc[300]{Applied computing~Digital libraries and archives}
\keywords{computational history, prosopography, documentation bias, distribution shift, CBDB}

\maketitle
\hypersetup{pdftitle={Who Leaves a Recorded Path into Government? A Documentation-Aware Data Mining Study of CBDB},pdfauthor={PDF_AUTHOR}}

\section{Introduction}
Prosopographical databases make collective historical patterns computationally tractable \cite{bol2012gis,tsui2020harvesting}.  They also turn traces from heterogeneous sources into structured observations.  CBDB is a freely available relational database designed for statistical, network, spatial, and biographical analysis \cite{cbdb2026,fuller2024}.  The same design creates a measurement problem: a model can learn both historical structure and the process by which people and relations became documented.

We ask five questions: how predictable is ENTRY-record presence; which personal, geographic, family, and documentation groups contain predictive information; whether recorded family political capital adds information after observability and topology; how models transport across families, regions, periods, dynasties, and sources; and how much high performance reflects documentation and selection.  Our contributions are: (1) a reproducible, person-level feature system with explicit leakage policy; (2) frozen logistic/CatBoost comparisons with grouped ablation and shift analyses; and (3) a documentation-aware interpretation in which D5\_MAIN is the main predictive model, H\_STRUCT is the historical structural benchmark, and D6\_UPPER is only a database-internal upper bound.

\section{Related Work}
CBDB represents biographical factoids, relations, places, offices, kin, and texts rather than an error-free census of past lives \cite{fuller2024,tsui2020harvesting}.  Quantitative history has combined its prosopographical records with historical GIS \cite{bol2012gis}.  Methodologically, tree ensembles remain strong tabular baselines \cite{grinsztajn2022tabular}; CatBoost handles categorical variables and ordered target statistics \cite{prokhorenkova2018catboost}.  We use SHAP only as additive attribution \cite{lundberg2017shap}, calibration as a separate diagnostic \cite{guo2017calibration}, and held-out groups as distribution-shift tests rather than external truth validation \cite{koh2021wilds}.  Administrative data demand attention to the selection processes that generated them \cite{hand2018administrative}; that concern is substantive here, not boilerplate.

\section{Data and Task Definition}
The frozen release is \texttt{cbdb\_20260829.sqlite3}.  Relation tables were first aggregated by person and only then joined, preventing multi-table fan-out.  The population contains \NPeople{} CBDB-covered people, of whom \NEntry{} have $E=1$ (Table~\ref{tab:dataset}).  Let
\begin{align}
T_i&=\mathbb{1}(\text{person }i\text{ truly entered government}),\\
E_i&=\mathbb{1}(i\text{ appears in ENTRY\_DATA}),\\
P_i&=\mathbb{1}(i\text{ has a valid posting record}).
\end{align}
$T$ is latent; $E$ is the primary observed proxy; $P$ is an auxiliary observed label.  Thus $E\ne T$, $P\ne T$, and $E\ne P$.  The estimand is $\Pr(E_i=1\mid X_i)$.

\begin{figure*}[t]
\centering\includegraphics[width=\textwidth]{figures/fig1_task_ep_t.pdf}
\caption{Observed labels and latent historical state. Counts in the $E\times P$ matrix are generated from the frozen person table. Neither observed label is $T$.}\Description{A measurement diagram links latent true historical entry through preservation and database encoding to ENTRY and posting records, beside a two-by-two count matrix.}\label{fig:ept}
\end{figure*}
\input{tables/table1_dataset}

\section{Exploratory Data Analysis}
Figure~\ref{fig:dynasty} shows both coverage and the recorded ENTRY share among CBDB-covered individuals.  It is not the historical entry rate of China's population.  Gender differences remain large within dynasty, while male-only sensitivity shows that gender is not the sole signal.  Figure~\ref{fig:pathways} separates ENTRY records into exam, schooling, recommendation, privilege, military, appointment, and other pathways.  Person categories are nonexclusive, so their prevalence may sum above 100\%.

\begin{figure}[t]\centering\includegraphics[width=\columnwidth]{figures/fig2_dynasty_gender.pdf}\caption{Coverage and recorded ENTRY share by dynasty and gender. Denominators are CBDB-covered people.}\Description{Bars show population counts and grouped rates by gender.}\label{fig:dynasty}\end{figure}
\begin{figure}[t]\centering\includegraphics[width=\columnwidth]{figures/fig3_entry_pathways.pdf}\caption{ENTRY pathway composition at record and unique-person levels. Person-level categories are nonexclusive.}\Description{Horizontal stacked bars compare pathway composition across five dynasties.}\label{fig:pathways}\end{figure}

\section{Features and Leakage Control}
The raw SQLite archive is read-only.  Direct ENTRY fields, the focal person's posting outcomes, entry/posting counts, raw index year, and \texttt{family\_group\_id} are forbidden predictors.  Safe birth information requires audited provenance.  Regional density is fitted on train only; the local ENTRY prior is out-of-fold on train and transformed forward.  Documentation indicators are grouped rather than silently mixed into historical interpretation.  Full-record family outcomes (F3) are cross-sectional and temporally ambiguous; train-observed family capital (F4) limits whose outcomes are visible but is not strictly pre-entry.  Frozen splits and validation-only early stopping keep test labels outside direct fitting and threshold choice.

The primary split was frozen and not used for direct parameter fitting, although later analyses were designed after observing earlier benchmark results; distribution-shift robustness is therefore reported separately.  Table~\ref{tab:features} states the final hierarchy.
\input{tables/table2_features}

\section{Models and Evaluation}
Balanced logistic regression is the linear baseline.  CatBoost is appropriate for mixed categorical, missing, and nonlinear tabular structure \cite{prokhorenkova2018catboost}.  All final models use seed 42, 500 maximum iterations, depth 7, learning rate 0.05, validation early stopping, and the locked class-weight candidate rule.  No Phase 3 tuning, GNN, or PageRank run occurred.

We report ROC-AUC, PR-AUC, balanced accuracy, F1, LogLoss, Brier score, and ECE.  PR-AUC is paired with prevalence, especially for Ming.  Validation-fitted sigmoid calibration never uses test labels.  Bootstrap intervals quantify test-sample variability only: they do not cover label definition, selection, source coverage, or CBDB's nonrandom population.  The protocol includes the frozen primary and family splits, matched-support unseen-region tests, SAFE temporal split diagnostics, descriptive Qing analysis, five-seed stability, and a prespecified source feasibility gate.

\section{Experimental Results}
Table~\ref{tab:performance} and Figure~\ref{fig:models} show the locked hierarchy.  D5\_MAIN reaches ROC-AUC \GlobalDfiveRoc{} and PR-AUC \GlobalDfivePr{} globally, with LogLoss \GlobalDfiveLogLoss{} and Brier \GlobalDfiveBrier{}.  The calibrated ECE is \GlobalDfiveEce{}.  D6\_UPPER is marginally higher in discrimination, but its relatives' lifetime ENTRY/posting features make it a record-structure upper bound rather than the main historical model.
\input{tables/table3_performance}
\begin{figure}[t]\centering\includegraphics[width=\columnwidth]{figures/fig4_locked_models.pdf}\caption{Primary-test ROC-AUC and PR-AUC. D5\_MAIN is the main model; D6\_UPPER is an upper bound.}\Description{Grouped bars compare a logistic baseline and three locked CatBoost models.}\label{fig:models}\end{figure}

\section{Documentation Bias and Robustness}
Ablation is the primary evidence of conditional contribution.  Figure~\ref{fig:ablation} shows large increments for gender, address observability, administrative geography, and family observability; physical coordinates and local prior are near zero once other geography is present.  Address-record semantics is documentation-linked, not physical geography.  Family observability and topology dominate full-record or train-observed political-capital increments (Figure~\ref{fig:family}).  A small, stable increment is not substantively large.

\begin{figure}[t]\centering\includegraphics[width=\columnwidth]{figures/fig5_grouped_ablation.pdf}\caption{Global grouped ablations. Block increments are conditional on the preceding feature set.}\Description{Horizontal bars show ROC and PR increments for nine feature blocks.}\label{fig:ablation}\end{figure}
\begin{figure}[t]\centering\includegraphics[width=\columnwidth]{figures/fig6_spatial_transport.pdf}\caption{Address decomposition and matched-support spatial shift. Administrative and observability blocks dominate; all unseen-region deltas are negative.}\Description{Two horizontal bar charts compare address increments and spatial transport losses.}\label{fig:spatial}\end{figure}
\begin{figure}[t]\centering\includegraphics[width=\columnwidth]{figures/fig7_family_decomposition.pdf}\caption{Family decomposition. Observability is the largest conditional family block; political-capital increments are much smaller.}\Description{Grouped bars show family-block ROC and PR increments for Global, Song, and Ming.}\label{fig:family}\end{figure}

Matched-support spatial ROC-AUC falls for both locked models in Global, Song, and Ming (Figure~\ref{fig:spatial}); this shows weaker transport to unseen historical regions, not a geographic effect.  Whole-family holdout causes smaller degradation for a structural comparator.  The SAFE temporal split contains only 59,851 eligible people and no frozen Phase 2.6 locked-model performance artifact; Qing likewise has no prespecified holdout artifact.  We report those absences instead of adding post-hoc splits.

The source audit scans the actual SQLite schema.  The \texttt{BIOG\_\allowbreak SOURCE\_\allowbreak DATA} table explicitly marks primary sources, but 40,360 people have multiple marked primaries.  Target-independent connected components of marked-primary person--source edges yield \SourceGroups{} groups; the largest includes \SourceLargest{} of \SourceEligible{} people (\SourceLargestPct{}), failing the preregistered 20\% ceiling.  Source-group confirmation is therefore not feasible and no source model was trained.

\input{tables/table4_ablation}
\input{tables/table5_robustness}

\section{Model Interpretation}
Grouped SHAP passed additivity checks for all nine population--model pairs.  Figure~\ref{fig:shap} shows gender, dynasty (the ``other'' group), administrative geography, family topology, and documentation-linked groups redistributing attribution across populations.  D6\_UPPER assigns \DsiFamilyShare{} of Global absolute attribution to full-record family capital.  Song local prior has a sizable SHAP share even though its ablation increment is near zero, illustrating overlap among correlated predictors.  SHAP attribution is neither independent ablation gain nor a causal effect \cite{lundberg2017shap}.

\begin{figure*}[t]\centering\includegraphics[width=\textwidth]{figures/fig8_grouped_shap.pdf}\caption{Grouped mean absolute SHAP shares for locked models. Blank cells denote feature groups absent from a model. Shares are attributions, not conditional gains or causal effects.}\Description{Three heatmaps compare feature-group attribution shares across populations and models.}\label{fig:shap}\end{figure*}

\section{Limitations}
The analysis has at least fifteen limitations. (1) $E$ is ENTRY-record presence, not $T$. (2) Posting is also incomplete ground truth. (3) CBDB is not a random sample of historical populations. (4) Selection into surviving sources is uneven. (5) Documentation intensity affects both features and labels. (6) Dynasty, region, and source coverage are unbalanced. (7) D5\_MAIN is retrospective record classification, not strict prospective prediction. (8) Some family topology is database-internal and transductive. (9) Relatives' lifetime outcomes have temporal ambiguity. (10) Safe birth-year coverage is only 9.05\% globally. (11) Repeated analysis of the primary test creates researcher-adaptation risk. (12) Source holdout is infeasible because of the giant component. (13) SHAP has no causal interpretation. (14) Calibration may not transport beyond similar data. (15) Bootstrap intervals omit label, coverage, and inclusion uncertainty.

\section{Reproducibility and Data Availability}
The verified database SHA256 is \texttt{f620ca1a4c794411\allowbreak b81d5039adf5756d\allowbreak f129fb9aa0f4509b\allowbreak 4c843bb66e0caa2a}.  Python, SQLite, CatBoost, SHAP, and package versions are recorded in the review bundle.  Seed 42, split hashes, feature lists, model hashes, figure input hashes, and one-command scripts are included.  No full SQLite database or 661,124-row feature table is redistributed.  The official release can be downloaded and verified with the supplied script; CBDB remains available through its official project \cite{cbdb2026}.

\section{Conclusion}
ENTRY-record presence is highly predictable within CBDB.  The evidence points to gender, regime, address and kin observability, administrative geography, family topology, and documentation processes as major predictive signals.  Recorded family political capital has limited additional information after those controls.  Spatial shift weakens transport, while temporal, Qing, and source-level claims remain bounded by missing frozen performance or infeasible grouping.  These results characterize structured documentation in CBDB; they do not reconstruct true historical entry or establish causes.

\label{mainend}\clearpage
\bibliographystyle{ACM-Reference-Format}
\bibliography{references}

\clearpage\appendix\label{appendixstart}
\section{Schema, Targets, and ENTRY Taxonomy}
The person-level grain begins with \texttt{BIOG\_MAIN}.  \texttt{ENTRY\_DATA} and \texttt{POSTING\_DATA} define the distinct observed labels $E$ and $P$; address, kin, association, status, text, institution, and source relations are separately aggregated by \texttt{c\_personid} before their one-row summaries are joined.  The source audit uses \texttt{BIOG\_SOURCE\_DATA}, \texttt{TEXT\_CODES}, and \texttt{TEXT\_BIBLCAT\_CODES}.  This aggregation order prevents join fan-out.

Target V1 is all-record $E$.  V2a and V2b are respectively broad and high-confidence formal entry/credential sensitivities; $P$ remains auxiliary posting presence and $T$ remains latent.  The audited ENTRY taxonomy is \texttt{exam\_degree}, \texttt{school\_or\_student\_status}, \texttt{recommendation}, \texttt{hereditary\_or\_yin\_privilege}, \texttt{military\_entry}, \texttt{purchase\_or\_donation}, \texttt{direct\_appointment}, \texttt{other\_clear\_entry}, \texttt{failed\_entry}, and \texttt{ambiguous}.  A person may occupy several categories.  Focal ENTRY/posting fields are never predictors.

\section{Additional Diagnostics}
\begin{figure}[h]\centering\includegraphics[width=\columnwidth]{figures/figA1_calibration.pdf}\caption{Raw and validation-calibrated ECE for locked models.}\Description{Grouped bar charts compare calibration errors.}\end{figure}
\begin{figure}[h]\centering\includegraphics[width=\columnwidth]{figures/figA2_multiseed.pdf}\caption{Five-seed stability; ranges are minima and maxima across seeds.}\Description{Points and error bars show incremental ROC-AUC stability.}\end{figure}
\begin{figure}[h]\centering\includegraphics[width=\columnwidth]{figures/figA3_robustness_scope.pdf}\caption{SAFE temporal split composition and source-group dominance.}\Description{Bars show temporal partition sizes and the largest source component.}\end{figure}

\section{Complete Evaluation Notes}
Family holdout keeps connected family groups disjoint.  Matched spatial comparisons restrict random and spatial tests to identical reliable-prefecture support, although the individuals differ, so those confidence intervals are not paired-individual intervals.  The SAFE temporal split uses whole years (train through 1729, validation through 1821, test thereafter) and leaves 601,273 people ineligible.  Qing results are descriptive because no frozen Qing holdout exists.  Source-group results are absent by design after the feasibility gate failed.

Calibration uses a validation-fitted sigmoid and ten ECE bins.  Paired bootstrap intervals use 500 stratified resamples where exact paired predictions were retained.  Grouped SHAP uses 10,000-person samples for each of the nine population--model combinations; all additivity checks pass.  The complete 102-row grouped attribution table, feature-level summaries, signed direction summaries, and additivity JSON are distributed with the review bundle.  SHAP remains attribution, not conditional ablation or causality.

\clearpage\onecolumn
\section{Frozen Parameters and Full Results}
\small
\input{tables/tableA1_model_parameters}
\input{tables/tableA2_full_metrics}
\input{tables/tableA3_full_ablation}
\input{tables/tableA4_full_robustness}

\section{Complete Frozen Feature Registry and Leakage Policy}
The registry below is generated directly from the Phase 2.6 lock.  In addition to its model membership, the global policy forbids person and family identifiers, all target columns, ENTRY/posting counts, focal posting presence, raw index-year fields, and unsafe/unknown year fields.  Regional density is train-only; the supervised local prior is out-of-fold on train and then transformed forward.  F3 uses full-record relatives' outcomes and is cross-sectional/transductive; F4 restricts outcomes to train-observed relatives but is not strictly pre-entry.  Test labels select neither features, hyperparameters, thresholds, nor calibration.
\input{tables/tableA5_feature_registry}

\section{Data Quality and Reproduction Detail}
Key uncertainties are missing or unsafe birth provenance, heterogeneous address semantics, multiple primary sources per person, uneven dynasty/region/source coverage, nonexclusive ENTRY categories, and nonrandom inclusion in CBDB.  Machine-readable target taxonomies, code-level review, split manifests, model hashes, figure-input hashes, and environment versions are included in the submission and review archives.  The raw and working SQLite databases and full feature master are deliberately excluded.

\section{Reproduction Command}
From the project root, run \texttt{bash scripts/run\_phase3.sh}.  The runner checks frozen hashes before work, rebuilds all Phase 3 tables and figures, compiles both papers, runs QA and tests, and validates both ZIP archives.
\label{appendixend}
"""


def build_tex(anonymous: bool) -> str:
    document_class = r"\documentclass[sigconf,anonymous,review]{acmart}" if anonymous else r"\documentclass[sigconf]{acmart}"
    author = (
        r"\author{Anonymous Author(s)}\affiliation{\institution{Anonymous Institution}}"
        if anonymous
        else r"\author{Xiaoke Lu}\affiliation{\institution{ShanghaiTech University}\city{Shanghai}\country{China}}"
    )
    pdf_author = "Anonymous" if anonymous else "Xiaoke Lu"
    preamble = document_class + r"""
\usepackage{booktabs}
\usepackage{amsmath}
\usepackage{graphicx}
\usepackage{longtable}
\settopmatter{printacmref=false}
\setcopyright{none}
\acmConference[KDD-style 2026]{Reproducible Research Manuscript}{2026}{Shanghai, China}
\acmBooktitle{Reproducible Research Manuscript}
\acmDOI{}
\acmISBN{}
""" + r"\input{tables/result_macros}" + "\n"
    body = PAPER_BODY.replace("AUTHOR_BLOCK", author).replace("PDF_AUTHOR", pdf_author)
    return preamble + body + "\n\\end{document}\n"


def write_chinese_summary() -> None:
    performance = pd.read_csv(PHASE3_TABLES / "main_model_performance.csv")
    d5 = performance.loc[performance["population"].eq("Global") & performance["model_id"].eq("D5_MAIN")].iloc[0]
    source = json.loads((PHASE3_TABLES / "source_holdout_status.json").read_text())
    text = f"""# 谁会留下入仕记录？——CBDB 最终科研摘要

## 任务与数据

本项目在冻结的 `cbdb_20260829.sqlite3` 上分析 661,124 个 CBDB 人物记录。主标签 **E** 是人物是否至少一次出现在 `ENTRY_DATA`；辅助标签 **P** 是是否存在有效任官记录；**T** 是不可直接观测的历史真实入仕状态。始终有 `E != T`、`P != T`、`E != P`，模型估计的是 `Pr(E=1|X)`，不是历史真实入仕概率。

## 方法与主要结果

项目比较冻结的 Logistic baseline、H_STRUCT、D5_MAIN 与 D6_UPPER，并使用分组消融、family holdout、matched-support spatial shift、五随机种子、校准和 grouped SHAP。主模型 D5_MAIN 的 Global ROC-AUC 为 {d5.roc_auc:.6f}，PR-AUC 为 {d5.pr_auc:.6f}，LogLoss 为 {d5.log_loss:.6f}，Brier 为 {d5.brier_score:.6f}，验证集拟合校准后的 ECE 为 {d5.calibrated_ece:.6f}。

主要预测信息来自性别、时代、地址与亲属记录可观测性、历史行政区、家族拓扑和 documentation process。经纬度、首都距离与 local prior 在已有地域变量之后的条件增量很小。亲属政治资本在控制可观测性和拓扑之后只有很小的独立增量，不能解释为家族政治资本具有大的历史效应。

## 稳健性与来源审计

匹配支持集上的未见地区测试显示 Global、Song、Ming 均有迁移性能下降；family-group holdout 的下降较小。SAFE temporal 只有冻结切分而没有 Phase 2.6 锁定模型性能产物；Qing 也没有预先冻结的 holdout，因此 Phase 3 没有事后补建结果。

来源层面实际审计了 `BIOG_SOURCE_DATA.c_main_source`。{source['eligible_people']:,} 名合格人物形成 {source['source_groups']:,} 个主来源连通组，但最大组含 {source['largest_group_people']:,} 人，占 {source['largest_group_fraction']:.2%}，超过 20% 预设门槛。因此状态为 `SOURCE_GROUP_CONFIRMATION_NOT_FEASIBLE`，未训练任何来源 confirmation 模型。

## 局限

CBDB 不是古代人口随机样本；史料保存、编辑选择和数据库编码共同影响标签与特征。D5_MAIN 是回顾性数据库记录分类器，不是严格前瞻预测。部分家族结构是数据库内部或 transductive，亲属 lifetime outcome 存在时间歧义，安全出生年覆盖低，primary test 曾在多阶段被查看。SHAP 不是独立消融增量，更不是因果效应；bootstrap 也不覆盖标签定义、收录与史料不确定性。
"""
    (PHASE3_DOCS / "final_report_chinese_summary.md").write_text(text, encoding="utf-8")


def main() -> None:
    ensure_phase3_dirs()
    table_dataset(); table_features(); table_performance(); table_ablation(); table_robustness(); appendix_tables(); macros()
    (ROOT / "paper/main_author.tex").write_text(build_tex(False), encoding="utf-8")
    (ROOT / "paper/main_anonymous.tex").write_text(build_tex(True), encoding="utf-8")
    write_chinese_summary()
    env = environment_payload()
    write_json(PHASE3_TABLES / "environment_versions.json", env)
    (PHASE3_DOCS / "environment_versions.txt").write_text("\n".join(f"{k}: {v}" for k, v in env.items()) + "\n", encoding="utf-8")
    provenance = []
    for path in sorted(TABLE_DIR.glob("*.tex")):
        provenance.append({"table_file": path.relative_to(ROOT).as_posix(), "sha256": sha256_file(path), "generator": "scripts/57_write_final_paper.py"})
    pd.DataFrame(provenance).to_csv(PHASE3_TABLES / "latex_table_manifest.csv", index=False)
    print("Wrote author and anonymous acmart sources, ten generated tables, macros, and Chinese summary.")


if __name__ == "__main__":
    main()
