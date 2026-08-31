#!/usr/bin/env python3
"""Render the final Phase 2 report from generated tables and locked outputs."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import load_yaml
from src.utils import atomic_write_text, markdown_escape, setup_logging


POPULATIONS = ["Global", "Song", "Ming", "Qing"]
PRIMARY_POPULATIONS = ["Global", "Song", "Ming"]
FEATURE_ORDER = ["M0", "M0b", "M1", "M2", "M3", "M4", "M5", "M6"]


def fmt_number(value: object, digits: int = 3) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    return f"{float(value):.{digits}f}"


def fmt_pct(value: object) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    return f"{100 * float(value):.2f}%"


def table(headers: list[str], rows: list[list[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(markdown_escape(value) for value in row) + " |")
    return "\n".join(lines)


def population_section(summary: pd.DataFrame) -> str:
    subset = summary.loc[summary["population"].isin(POPULATIONS)].copy()
    rows = []
    for row in subset.itertuples():
        rows.append([
            row.population,
            f"{int(row.n_people):,}",
            f"{int(row.entry_v1_positive):,}",
            fmt_pct(row.entry_v1_rate),
            f"{int(row.entry_v2a_positive):,}",
            fmt_pct(row.entry_v2a_rate),
            fmt_pct(row.posting_rate),
        ])
    return table(
        ["Population", "N", "V1 positive", "V1 rate", "V2a positive", "V2a rate", "Posting rate"],
        rows,
    )


def coverage_section() -> str:
    columns = [
        "person_id", "dynasty_name", "gender", "safe_birth_year", "has_geography",
        "latitude", "father_identified", "paternal_grandfather_identified",
        "father_ever_entry", "paternal_grandfather_ever_entry",
        "father_entry_before_birth", "any_older_kin_entry_before_birth",
        "documentation_intensity",
    ]
    frame = pd.read_parquet(PROJECT_ROOT / "data/modeling/person_phase2_features.parquet", columns=columns)
    definitions = [
        ("Personal", "gender", ["gender"]),
        ("Personal", "safe_birth_year", ["safe_birth_year"]),
        ("Geography", "has_geography", ["has_geography"]),
        ("Geography", "latitude", ["latitude"]),
        ("Family structural", "father_identified", ["father_identified"]),
        ("Family structural", "paternal_grandfather_identified", ["paternal_grandfather_identified"]),
        ("Family capital", "father_ever_entry", ["father_ever_entry"]),
        ("Family capital", "paternal_grandfather_ever_entry", ["paternal_grandfather_ever_entry"]),
        ("Pre-birth lineage", "father_entry_before_birth", ["father_entry_before_birth"]),
        ("Pre-birth lineage", "any_older_kin_entry_before_birth", ["any_older_kin_entry_before_birth"]),
        ("Documentation", "documentation_intensity", ["documentation_intensity"]),
    ]
    rows = []
    for group, label, feature_columns in definitions:
        row = [group, label]
        for population in POPULATIONS:
            subset = frame if population == "Global" else frame.loc[frame["dynasty_name"].eq(population)]
            values = subset[feature_columns[0]]
            row.append(fmt_pct(values.notna().mean()))
        rows.append(row)
    return table(["Group", "Representative feature", "Global", "Song", "Ming", "Qing"], rows)


def primary_model_section(metrics: pd.DataFrame, algorithm: str) -> str:
    subset = metrics.loc[
        metrics["algorithm"].eq(algorithm)
        & metrics["threshold_source"].eq("fixed_0.5")
        & metrics["evaluation_split"].eq("test")
    ].copy()
    if algorithm == "LogisticRegression":
        subset = subset.loc[subset["model_variant"].eq("balanced")]
    rows = []
    for population in PRIMARY_POPULATIONS:
        for feature_set in FEATURE_ORDER:
            item = subset.loc[
                subset["population"].eq(population) & subset["feature_set"].eq(feature_set)
            ]
            if item.empty:
                continue
            value = item.iloc[0]
            rows.append([
                population,
                feature_set,
                fmt_number(value.roc_auc, 4),
                fmt_number(value.pr_auc, 4),
                fmt_number(value.balanced_accuracy, 4),
                fmt_number(value.f1, 4),
                fmt_number(value.log_loss, 4),
            ])
    return table(["Population", "Set", "ROC-AUC", "PR-AUC", "Balanced acc.", "F1", "Log loss"], rows)


def ablation_section(ablation: pd.DataFrame) -> str:
    subset = ablation.loc[
        ablation["algorithm"].eq("CatBoost")
        & ablation["feature_block"].isin(["geography", "family_structure", "family_capital", "documentation_addition"])
    ].copy()
    rows = []
    for row in subset.sort_values(["population", "extension_feature_set"]).itertuples():
        rows.append([
            row.population,
            f"{row.baseline_feature_set} -> {row.extension_feature_set}",
            row.feature_block,
            fmt_number(row.delta_roc_auc, 4),
            f"[{fmt_number(row.delta_roc_auc_ci_low, 4)}, {fmt_number(row.delta_roc_auc_ci_high, 4)}]",
            fmt_number(row.delta_pr_auc, 4),
            fmt_number(row.delta_log_loss, 4),
        ])
    return table(
        ["Population", "Comparison", "Block", "Delta ROC-AUC", "95% CI", "Delta PR-AUC", "Delta log loss"],
        rows,
    )


def family_section(metrics: pd.DataFrame, primary: pd.DataFrame) -> str:
    robust = metrics.loc[
        metrics["analysis"].eq("family_group_robustness")
        & metrics["threshold_source"].eq("fixed_0.5")
        & metrics["feature_set"].isin(["M4", "M6"])
    ]
    primary_lookup = primary.loc[
        primary["algorithm"].eq("LogisticRegression")
        & primary["threshold_source"].eq("fixed_0.5")
        & primary["model_variant"].eq("balanced")
    ].set_index(["population", "feature_set"])["roc_auc"]
    rows = []
    for row in robust.sort_values(["population", "feature_set"]).itertuples():
        reference = float(primary_lookup[(row.population, row.feature_set)])
        rows.append([
            row.population,
            row.feature_set,
            fmt_number(reference, 4),
            fmt_number(row.roc_auc, 4),
            fmt_number(row.roc_auc - reference, 4),
            f"{int(row.n_test):,}",
        ])
    return table(["Population", "Set", "Primary AUC", "Family AUC", "Change", "Family test N"], rows)


def temporal_section(metrics: pd.DataFrame) -> str:
    subset = metrics.loc[
        metrics["analysis"].eq("temporal_sensitivity")
        & metrics["threshold_source"].eq("fixed_0.5")
        & metrics["feature_set"].isin(["M4", "M6"])
    ]
    rows = []
    for row in subset.sort_values(["population", "feature_set"]).itertuples():
        rows.append([row.population, row.feature_set, fmt_number(row.roc_auc, 4), f"{int(row.n_test):,}"])
    return table(["Population", "Set", "Temporal test ROC-AUC", "Test N"], rows)


def prebirth_section(metrics: pd.DataFrame) -> str:
    subset = metrics.loc[
        metrics["analysis"].eq("prebirth_lineage")
        & metrics["threshold_source"].eq("fixed_0.5")
    ]
    rows = []
    for row in subset.sort_values(["population", "feature_set"]).itertuples():
        rows.append([row.population, row.feature_set, fmt_number(row.roc_auc, 4), fmt_number(row.pr_auc, 4), f"{int(row.n_test):,}"])
    return table(["Population", "Set", "ROC-AUC", "PR-AUC", "Safe-birth test N"], rows)


def qing_section(metrics: pd.DataFrame) -> str:
    subset = metrics.loc[
        metrics["analysis"].eq("qing_holdout")
        & metrics["threshold_source"].eq("fixed_0.5")
        & metrics["feature_set"].isin(["M0", "M2", "M4", "M6"])
    ]
    rows = []
    for row in subset.sort_values("feature_set").itertuples():
        rows.append([row.feature_set, fmt_number(row.roc_auc, 4), fmt_number(row.pr_auc, 4), f"{int(row.n_test):,}"])
    return table(["Set", "Qing holdout ROC-AUC", "PR-AUC", "Qing test N"], rows)


def top_features() -> tuple[str, str]:
    importance = pd.read_csv(PROJECT_ROOT / "outputs/phase2/tables/catboost_feature_importance.csv")
    subset = importance.loc[
        importance["algorithm"].eq("CatBoost")
        & importance["population"].eq("Global")
        & importance["feature_set"].eq("M6")
    ].sort_values("importance", ascending=False).head(10)
    cat_rows = [[row.feature, fmt_number(row.importance, 3), int(row.importance_rank)] for row in subset.itertuples()]
    catboost = table(["Feature", "Importance", "Rank"], cat_rows)

    coefficients = pd.read_csv(PROJECT_ROOT / "outputs/phase2/tables/logistic_coefficients.csv")
    subset = coefficients.loc[
        coefficients["algorithm"].eq("LogisticRegression")
        & coefficients["population"].eq("Global")
        & coefficients["feature_set"].eq("M6")
    ].sort_values("absolute_coefficient_rank").head(12)
    log_rows = [[row.transformed_feature, fmt_number(row.coefficient, 3), int(row.absolute_coefficient_rank)] for row in subset.itertuples()]
    logistic = table(["Transformed feature", "Coefficient", "Absolute rank"], log_rows)
    return catboost, logistic


def bootstrap_section(bootstrap: pd.DataFrame) -> str:
    subset = bootstrap.loc[
        bootstrap["feature_set"].eq("M6")
        & bootstrap["algorithm"].isin(["LogisticRegression", "CatBoost"])
    ]
    rows = []
    for row in subset.sort_values(["population", "algorithm"]).itertuples():
        rows.append([
            row.algorithm,
            row.population,
            fmt_number(row.roc_auc, 4),
            f"[{fmt_number(row.roc_auc_ci_low, 4)}, {fmt_number(row.roc_auc_ci_high, 4)}]",
            fmt_number(row.pr_auc, 4),
            f"[{fmt_number(row.pr_auc_ci_low, 4)}, {fmt_number(row.pr_auc_ci_high, 4)}]",
            int(row.bootstrap_resamples),
        ])
    return table(["Algorithm", "Population", "ROC-AUC", "ROC 95% CI", "PR-AUC", "PR 95% CI", "B"], rows)


def main() -> int:
    logger = setup_logging("phase2_report", PROJECT_ROOT / "outputs/logs/phase2_report.log")
    summary = pd.read_csv(PROJECT_ROOT / "outputs/tables/modeling_population_summary.csv")
    metrics = pd.read_csv(PROJECT_ROOT / "outputs/phase2/tables/model_metrics.csv")
    ablation = pd.read_csv(PROJECT_ROOT / "outputs/phase2/tables/ablation_results.csv")
    robustness = pd.read_csv(PROJECT_ROOT / "outputs/phase2/tables/robustness_metrics.csv")
    bootstrap = pd.read_csv(PROJECT_ROOT / "outputs/phase2/tables/bootstrap_intervals.csv")
    temporal_support = pd.read_csv(PROJECT_ROOT / "outputs/phase2/tables/temporal_support_audit.csv")
    catboost_top, logistic_top = top_features()
    model_config = load_yaml("configs/phase2_models.yaml")

    fixed = metrics.loc[
        metrics["evaluation_split"].eq("test") & metrics["threshold_source"].eq("fixed_0.5")
    ]
    catboost_m6 = fixed.loc[
        fixed["algorithm"].eq("CatBoost") & fixed["feature_set"].eq("M6")
    ].set_index("population")["roc_auc"]
    logistic_m6 = fixed.loc[
        fixed["algorithm"].eq("LogisticRegression")
        & fixed["model_variant"].eq("balanced")
        & fixed["feature_set"].eq("M6")
    ].set_index("population")["roc_auc"]
    catboost_m2 = fixed.loc[
        fixed["algorithm"].eq("CatBoost") & fixed["feature_set"].eq("M2")
    ].set_index("population")["roc_auc"]
    catboost_m1 = fixed.loc[
        fixed["algorithm"].eq("CatBoost") & fixed["feature_set"].eq("M1")
    ].set_index("population")["roc_auc"]
    catboost_m3 = fixed.loc[
        fixed["algorithm"].eq("CatBoost") & fixed["feature_set"].eq("M3")
    ].set_index("population")["roc_auc"]
    catboost_m4 = fixed.loc[
        fixed["algorithm"].eq("CatBoost") & fixed["feature_set"].eq("M4")
    ].set_index("population")["roc_auc"]
    family_m6 = robustness.loc[
        robustness["analysis"].eq("family_group_robustness")
        & robustness["threshold_source"].eq("fixed_0.5")
        & robustness["feature_set"].eq("M6")
    ].set_index("population")["roc_auc"]

    report = [
        "# CBDB Phase 2: Predicting Recorded Entry-Data Presence",
        "",
        "> Final report generated from the frozen CBDB foundation and the locked Phase 2 outputs.",
        "",
        "## Executive Summary",
        "",
        "This project predicts whether a person appears in `ENTRY_DATA` at least once. The target is a database-record presence label, not proof that a historical person actually held office or that a person without a record never entered government.",
        "",
        "The primary benchmark uses the frozen dynasty-by-target split (seed 42). Logistic Regression and CatBoost use train-only preprocessing; CatBoost class weighting is selected on validation only. Test metrics below use the fixed 0.5 threshold unless otherwise noted.",
        "",
        "## Reproduction",
        "",
        "Run the complete Phase 2 pipeline from the project root:",
        "",
        "```bash",
        "bash scripts/run_phase2.sh",
        "```",
        "",
        "The pipeline uses the frozen Phase 1.5 foundation and writes features, predictions, models, result tables, figures, the report, and the final invariant manifest.",
        "",
        "## Data Sources",
        "",
        "- [Official CBDB SQLite repository](https://github.com/cbdb-project/cbdb_sqlite)",
        "- [CBDB download page](https://projects.iq.harvard.edu/chinesecbdb/%E4%B8%8B%E8%BC%89cbdb%E5%96%AE%E6%A9%9F%E7%89%88)",
        "- [CBDB Chinese user guide](https://projects.iq.harvard.edu/files/cbdb/files/cbdb_users_guide_ch_20210322.pdf)",
        "",
        "## Dataset",
        "",
        f"The retained master table contains **661,124** unique people and **220,627** V1 positives ({220627 / 661124:.2%}). V2a/V2b and posting are auxiliary sensitivity outcomes and are not predictors.",
        "",
        population_section(summary),
        "",
        "Global is a database-wide benchmark and must not be described as the historical population of China. Song is relatively balanced and has the strongest address coverage among the principal populations. Ming has a lower V1 rate and stronger kin coverage. Qing is used here for external and temporal comparison rather than as a full primary model population.",
        "",
        "## Feature Coverage",
        "",
        coverage_section(),
        "",
        "Family lifetime `ever_*` features are cross-sectional and temporally ambiguous. Pre-birth lineage features require a valid SAFE birth year and a relative event year strictly earlier than that birth year; missing relative event years remain missing.",
        "",
        "## Primary Model Results",
        "",
        "### Logistic Regression",
        "",
        primary_model_section(metrics, "LogisticRegression"),
        "",
        "### CatBoost",
        "",
        primary_model_section(metrics, "CatBoost"),
        "",
        "CatBoost M6 reaches ROC-AUC values of "
        f"{catboost_m6['Global']:.4f} (Global), {catboost_m6['Song']:.4f} (Song), and {catboost_m6['Ming']:.4f} (Ming), compared with Logistic M6 values of "
        f"{logistic_m6['Global']:.4f}, {logistic_m6['Song']:.4f}, and {logistic_m6['Ming']:.4f}.",
        "",
        "## Feature Ablation",
        "",
        "The following paired comparisons use CatBoost primary test predictions. Confidence intervals are paired bootstrap intervals with the configured 500 resamples. Positive ROC-AUC and PR-AUC deltas indicate improved ranking; a negative log-loss delta indicates improved probabilistic accuracy.",
        "",
        ablation_section(ablation),
        "",
        f"For CatBoost, the geography increment M2-M1 is {catboost_m2['Global'] - catboost_m1['Global']:.4f} ROC-AUC in Global, {catboost_m2['Song'] - catboost_m1['Song']:.4f} in Song, and {catboost_m2['Ming'] - catboost_m1['Ming']:.4f} in Ming. The family-structure increment M3-M2 is {catboost_m3['Global'] - catboost_m2['Global']:.4f}, {catboost_m3['Song'] - catboost_m2['Song']:.4f}, and {catboost_m3['Ming'] - catboost_m2['Ming']:.4f} respectively. The family-capital increment M4-M3 is {catboost_m4['Global'] - catboost_m3['Global']:.4f}, {catboost_m4['Song'] - catboost_m3['Song']:.4f}, and {catboost_m4['Ming'] - catboost_m3['Ming']:.4f}.",
        "",
        "## Documentation Bias",
        "",
        "M5 contains only domain-presence and documentation-intensity variables. It is a diagnostic for recording structure, not a historical mechanism. M6 combines the historical feature set with these recording variables.",
        "",
        "The primary tables show that M5 alone can be strong, especially in Song. The improvement from M4 to M6 therefore should not be interpreted as a purely historical gain; it may partly reflect which people and relations CBDB records more completely.",
        "",
        "## Robustness",
        "",
        "### Family-Group Split",
        "",
        family_section(robustness, metrics),
        "",
        f"For the M6 Logistic model, the family-group split changes ROC-AUC by {family_m6['Global'] - logistic_m6['Global']:.4f} in Global, {family_m6['Song'] - logistic_m6['Song']:.4f} in Song, and {family_m6['Ming'] - logistic_m6['Ming']:.4f} in Ming relative to the primary split. This is a generalization check across whole core-family groups, not a replacement for the primary benchmark.",
        "",
        "### SAFE Temporal Sensitivity",
        "",
        temporal_section(robustness),
        "",
        "The SAFE temporal support audit shows that only "
        + ", ".join(temporal_support.loc[temporal_support["supports_three_partitions"], "population"].tolist())
        + " have all three partitions. Song and Ming are explicitly skipped because their SAFE people fall entirely in the temporal training partition.",
        "",
        "The temporal split is restricted to the small SAFE birth-year subset. Calendar time, dynasty composition, source composition, and recording practice shift together, so it is a distribution-shift sensitivity analysis rather than a clean causal time experiment.",
        "",
        "### Qing Holdout",
        "",
        "The Qing holdout trains on Song/Yuan/Ming source people using frozen primary train/validation assignments and evaluates all Qing people. It measures transport across institutional regimes.",
        "",
        qing_section(robustness),
        "",
        "### Pre-birth Lineage",
        "",
        prebirth_section(robustness),
        "",
        "PB1 is a sensitivity analysis for recorded political capital already present before the focal person's birth. Its coverage is very low, so any difference from PB0 should be treated as suggestive and not as a population-wide estimate.",
        "",
        "## Uncertainty",
        "",
        bootstrap_section(bootstrap),
        "",
        "Primary-model intervals use stratified bootstrap resampling of positive and negative test rows. Ablation intervals are paired on the same frozen test IDs. These intervals reflect test-set sampling uncertainty and do not account for database coverage bias or target-definition uncertainty.",
        "",
        "## Top Features",
        "",
        "### CatBoost Global/M6",
        "",
        catboost_top,
        "",
        "### Logistic Global/M6",
        "",
        logistic_top,
        "",
        "Coefficients and importances are predictive associations. They should not be read as causal effects, and lifetime family variables should not be described as definitely available before the focal person's own entry.",
        "",
        "## Figures",
        "",
        "- [Primary ROC-AUC comparison](../../outputs/phase2/figures/phase2_primary_auc.png)",
        "- [Ablation deltas](../../outputs/phase2/figures/phase2_ablation_delta.png)",
        "- [Family and temporal robustness](../../outputs/phase2/figures/phase2_robustness_auc.png)",
        "- [Top CatBoost features](../../outputs/phase2/figures/phase2_feature_importance.png)",
        "- [Population context](../../outputs/phase2/figures/phase2_population_context.png)",
        "- [Bootstrap intervals](../../outputs/phase2/figures/phase2_bootstrap_ci.png)",
        "",
        "## Scientific Conclusions",
        "",
        "1. The current target measures recorded presence in CBDB `ENTRY_DATA`, so all results describe documentation-linked prediction rather than a verified historical office-holding rate.",
        f"2. Dynasty and SAFE birth-cohort information provide a useful baseline, but the largest primary gain is geographic: CatBoost increases Global ROC-AUC from {catboost_m1['Global']:.3f} at M1 to {catboost_m2['Global']:.3f} at M2.",
        f"3. Family structure adds substantial predictive information after geography, with Global CatBoost ROC-AUC rising from {catboost_m2['Global']:.4f} to {catboost_m3['Global']:.4f}.",
        f"4. Cross-sectional family political capital adds a smaller incremental gain in Global, from {catboost_m3['Global']:.4f} to {catboost_m4['Global']:.4f}; its lifetime timing is ambiguous.",
        "5. Documentation-only features are often strong, so the historical interpretation of M6 must be separated from database recording intensity.",
        "6. CatBoost generally outperforms the linear model on the same frozen primary test set, indicating useful nonlinearities and categorical interactions, but this does not establish transport to undocumented people.",
        "7. Family-group and temporal sensitivities are the relevant checks for generalization; their estimates should be read separately from the primary random-within-dynasty benchmark.",
        "8. Pre-birth lineage results are limited by approximately 9% SAFE birth-year coverage and much lower valid relative-event coverage, so they are robustness evidence rather than a broad estimate of inherited political capital.",
        "",
        "## Limitations and Next Steps",
        "",
        "The database is a selective historical source, dynasty composition is uneven, and `ENTRY_DATA` is not a complete census of entry into government. Cross-sectional family outcomes can include events after the focal person's entry. The current pre-birth design is not the future matched case-control risk-time design. Network centrality, SHAP, GNNs, and large hyperparameter searches were intentionally excluded from this phase.",
        "",
        "The full Phase 2 invariant check records the final status after all tables, figures, report sections, and frozen-split checks are present.",
        "",
        f"Configuration: `configs/phase2_models.yaml`, bootstrap resamples = {int(model_config['bootstrap_resamples'])}, seed = {int(model_config['seed'])}.",
        "",
    ]
    output = PROJECT_ROOT / "docs/phase2/phase2_report.md"
    report_text = "\n".join(report)
    atomic_write_text(output, report_text)
    readme_text = report_text.replace("](../../outputs/phase2/figures/", "](outputs/phase2/figures/")
    atomic_write_text(PROJECT_ROOT / "README.md", readme_text)
    logger.info("Phase 2 report written: %s", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
