#!/usr/bin/env python3
"""Generate the scientific Phase 2 summary and enforce final frozen invariants."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import load_yaml
from src.utils import atomic_write_text, markdown_table, setup_logging, sha256_file


EXPECTED = {
    "database": "f620ca1a4c794411b81d5039adf5756df129fb9aa0f4509b4c843bb66e0caa2a",
    "target": "0da45a25e63c6d241f88ff69399bf12c2de83730e7adc376f3f2ca3e00357112",
    "base": "f3e5fa26c024fc46da312dd77500db8313112d7cf1841214f37ea47a6878e771",
    "primary": "35eb208370aa1dc67e6b6ab66bf52543a75f4d6f4a8aa35e9db3ce70d2f5c0cd",
    "random": "e9abde694fd6ceabafa35e56cbd927a180e3016cacaba0c880c98deb0eb456fc",
    "family": "9f6fb17147a9374ef36527173b74f7985dc12e2ec41c48702a82f6aff13d6387",
    "temporal": "bba7259aaaba40a5728a8d84ea5f5a4d5c633760d5869872aec845f9f7b97cbf",
}
ARTIFACTS = {
    "database": "database/cbdb_20260829.sqlite3",
    "target": "data/interim/person_target.parquet",
    "base": "data/processed/person_base_v0.parquet",
    "primary": "data/splits/split_primary_dynasty_target.parquet",
    "random": "data/splits/split_random_benchmark.parquet",
    "family": "data/splits/split_family_group_robustness.parquet",
    "temporal": "data/splits/split_safe_temporal.parquet",
}
REQUIRED_OUTPUTS = [
    "data/features/personal_features.parquet",
    "data/features/geography_features.parquet",
    "data/features/family_structural_features.parquet",
    "data/features/family_capital_features.parquet",
    "data/modeling/person_phase2_features.parquet",
    "data/modeling/phase2_predictions_logistic.parquet",
    "data/modeling/phase2_predictions_catboost.parquet",
    "data/modeling/phase2_predictions_robustness.parquet",
    "outputs/phase2/tables/model_metrics.csv",
    "outputs/phase2/tables/ablation_results.csv",
    "outputs/phase2/tables/robustness_results.csv",
    "outputs/phase2/tables/prebirth_lineage_results.csv",
    "outputs/phase2/tables/logistic_coefficients.csv",
    "outputs/phase2/tables/catboost_feature_importance.csv",
    "outputs/phase2/tables/metric_bootstrap_ci.csv",
    "outputs/phase2/figures/figure1_ablation_roc_auc.png",
    "outputs/phase2/figures/figure2_ablation_pr_auc.png",
    "outputs/phase2/figures/figure3_documentation_comparison.png",
    "outputs/phase2/figures/figure4_primary_vs_family_split.png",
    "outputs/phase2/figures/figure5_family_descriptive.png",
]


def format_float(value: object, digits: int = 4) -> str:
    return "" if pd.isna(value) else f"{float(value):.{digits}f}"


def main_metric_rows(metrics: pd.DataFrame) -> pd.DataFrame:
    keep = metrics["split_protocol"].eq("primary") & metrics["threshold_source"].eq("fixed_0.5")
    keep &= metrics["feature_set"].isin(["M0", "M1", "M2", "M3", "M4", "M5", "M6"])
    keep &= ~(
        metrics["algorithm"].eq("LogisticRegression")
        & ~metrics["model_variant"].eq("balanced")
    )
    return metrics.loc[keep].copy()


def population_summary(dataset: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for population in ["Global", "Song", "Ming", "Qing"]:
        subset = dataset if population == "Global" else dataset.loc[dataset["dynasty_name"].eq(population)]
        rows.append({
            "population": population,
            "n_people": len(subset),
            "v1_positive": int(subset["target_entry_v1"].sum()),
            "v1_positive_rate": float(subset["target_entry_v1"].mean()),
        })
    return pd.DataFrame(rows)


def coverage_summary(dataset: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for population in ["Global", "Song", "Ming", "Qing"]:
        subset = dataset if population == "Global" else dataset.loc[dataset["dynasty_name"].eq(population)]
        any_grandfather = subset[["paternal_grandfather_identified", "maternal_grandfather_identified"]].max(axis=1)
        definitions = {
            "safe_birth_year": subset["safe_birth_year"].notna(),
            "geography": subset["has_geography"].eq(1),
            "geography_coordinates": subset["latitude"].notna() & subset["longitude"].notna(),
            "father_identified": subset["father_identified"].eq(1),
            "any_grandfather_identified": any_grandfather.eq(1),
            "core_family": subset["has_core_family"].eq(1),
            "father_ever_entry_observed": subset["father_ever_entry"].notna(),
            "father_ever_posting_observed": subset["father_ever_posting"].notna(),
            "father_entry_before_birth_observed": subset["father_entry_before_birth"].notna(),
            "any_older_kin_entry_before_birth_observed": subset["any_older_kin_entry_before_birth"].notna(),
        }
        for feature, observed in definitions.items():
            positive_mean = None
            if feature.endswith("_observed"):
                source = feature.removesuffix("_observed")
                positive_mean = float(subset.loc[observed, source].mean()) if observed.any() else None
            rows.append({
                "population": population,
                "feature_or_domain": feature,
                "n_observed_or_present": int(observed.sum()),
                "coverage_or_presence": float(observed.mean()),
                "positive_rate_among_observed": positive_mean,
            })
    return pd.DataFrame(rows)


def validate_prediction_ids(path: Path, split_paths: dict[str, Path]) -> int:
    predictions = pd.read_parquet(path, columns=["person_id", "population", "split_protocol"])
    checks = 0
    for protocol, group in predictions.groupby("split_protocol"):
        split = pd.read_parquet(split_paths[protocol])
        test_ids = set(split.loc[split["split"].eq("test"), "person_id"].astype(int))
        if not set(group["person_id"].astype(int)).issubset(test_ids):
            raise RuntimeError(f"Prediction IDs escape frozen {protocol} test partition: {path.name}")
        checks += 1
    return checks


def enforce_invariants(dataset: pd.DataFrame, metrics: pd.DataFrame) -> dict[str, object]:
    hashes = {key: sha256_file(PROJECT_ROOT / path) for key, path in ARTIFACTS.items()}
    if hashes != EXPECTED:
        differences = {key: {"observed": hashes[key], "expected": EXPECTED[key]} for key in EXPECTED if hashes[key] != EXPECTED[key]}
        raise RuntimeError(f"Frozen artifact SHA256 changed: {differences}")
    if len(dataset) != 661_124 or dataset["person_id"].duplicated().any():
        raise RuntimeError("Master-table person count/uniqueness invariant failed")
    if int(dataset["target_entry_v1"].sum()) != 220_627:
        raise RuntimeError("V1 positive invariant failed")

    validation = json.loads((PROJECT_ROOT / "outputs/phase2/tables/feature_validation.json").read_text(encoding="utf-8"))
    if validation.get("status") != "PASS" or validation.get("single_feature_auc_gt_0_95_warnings"):
        raise RuntimeError("Phase 2 feature validation is not a clean PASS")
    missing_outputs = [path for path in REQUIRED_OUTPUTS if not (PROJECT_ROOT / path).is_file() or (PROJECT_ROOT / path).stat().st_size == 0]
    if missing_outputs:
        raise RuntimeError(f"Missing/empty Phase 2 outputs: {missing_outputs}")

    main = main_metric_rows(metrics)
    expected_main = {(algorithm, population, feature_set) for algorithm in ["LogisticRegression", "CatBoost"] for population in ["Global", "Song", "Ming"] for feature_set in ["M0", "M1", "M2", "M3", "M4", "M5", "M6"]}
    observed_main = set(main[["algorithm", "population", "feature_set"]].itertuples(index=False, name=None))
    if observed_main != expected_main or len(main) != len(expected_main):
        raise RuntimeError("Formal M0--M6 model matrix is incomplete or duplicated")
    family = metrics.loc[metrics["split_protocol"].eq("family") & metrics["threshold_source"].eq("fixed_0.5")]
    if len(family) != 8:
        raise RuntimeError("Family-aware Global/Ming M0/M4 model matrix is incomplete")
    prebirth = metrics.loc[metrics["feature_set"].isin(["PB0", "PB1"]) & metrics["threshold_source"].eq("fixed_0.5")]
    if len(prebirth) != 4:
        raise RuntimeError("PB0/PB1 Global model matrix is incomplete")

    split_paths = {
        "primary": PROJECT_ROOT / ARTIFACTS["primary"],
        "family": PROJECT_ROOT / ARTIFACTS["family"],
    }
    prediction_id_checks = sum([
        validate_prediction_ids(PROJECT_ROOT / "data/modeling/phase2_predictions_logistic.parquet", split_paths),
        validate_prediction_ids(PROJECT_ROOT / "data/modeling/phase2_predictions_catboost.parquet", split_paths),
        validate_prediction_ids(PROJECT_ROOT / "data/modeling/phase2_predictions_robustness.parquet", split_paths),
    ])
    forbidden_call = "train" + "_test_split"
    phase2_source = "\n".join(path.read_text(encoding="utf-8") for path in sorted((PROJECT_ROOT / "scripts").glob("2[0-9]_*.py")))
    if forbidden_call in phase2_source:
        raise RuntimeError("A Phase 2 script creates a new held-out split")
    feature_registry = load_yaml("configs/phase2_features.yaml")
    if "family_group_id" not in feature_registry["never_predict"]:
        raise RuntimeError("family_group_id is not denied for prediction")
    with sqlite3.connect(f"file:{(PROJECT_ROOT / 'database/cbdb_working.sqlite3').resolve().as_posix()}?mode=ro", uri=True) as connection:
        quick_check = connection.execute("PRAGMA quick_check").fetchone()[0]
    if quick_check != "ok":
        raise RuntimeError("Working database quick_check failed")
    return {
        "status": "PASS",
        "n_people": len(dataset),
        "v1_positive": int(dataset["target_entry_v1"].sum()),
        "frozen_sha256": hashes,
        "feature_validation": "PASS",
        "formal_main_models": len(main),
        "family_robustness_models": len(family),
        "prebirth_models": len(prebirth),
        "prediction_frozen_test_membership_checks": prediction_id_checks,
        "new_held_out_split_calls": 0,
        "family_group_id_predictive": False,
        "working_database_quick_check": quick_check,
        "required_outputs": len(REQUIRED_OUTPUTS),
    }


def build_report(dataset: pd.DataFrame, metrics: pd.DataFrame) -> str:
    populations = population_summary(dataset)
    coverage = coverage_summary(dataset)
    main = main_metric_rows(metrics)
    ablation = pd.read_csv(PROJECT_ROOT / "outputs/phase2/tables/ablation_results.csv")
    robustness = pd.read_csv(PROJECT_ROOT / "outputs/phase2/tables/robustness_results.csv")
    prebirth = pd.read_csv(PROJECT_ROOT / "outputs/phase2/tables/prebirth_lineage_results.csv")
    intervals = pd.read_csv(PROJECT_ROOT / "outputs/phase2/tables/metric_bootstrap_ci.csv")
    coefficients = pd.read_csv(PROJECT_ROOT / "outputs/phase2/tables/logistic_coefficients.csv")
    importance = pd.read_csv(PROJECT_ROOT / "outputs/phase2/tables/catboost_feature_importance.csv")

    lines = [
        "# Phase 2 results",
        "",
        "This is a database-wide prediction study of CBDB records. Target V1 means **ENTRY_DATA record presence**; it is not proof of actual office holding, a population probability, or a causal outcome. Posting variables denote recorded office-holding/posting outcomes and enter only as relatives' cross-sectional history where registered.",
        "",
        "## Dataset",
        "",
        markdown_table(
            ["Population", "N", "V1 positive", "V1 rate"],
            [[row.population, f"{row.n_people:,}", f"{row.v1_positive:,}", format_float(row.v1_positive_rate)] for row in populations.itertuples()],
        ),
        "",
        "Global is a benchmark over people represented in CBDB, not ancient China's general population. Song is the primary comprehensive analysis; Ming is the main family-political-capital comparison; Qing is descriptive only in this first round.",
        "",
        "## Feature coverage",
        "",
        markdown_table(
            ["Population", "Feature/domain", "Observed/present", "Coverage", "Positive among observed"],
            [[row.population, row.feature_or_domain, f"{row.n_observed_or_present:,}", format_float(row.coverage_or_presence), format_float(row.positive_rate_among_observed)] for row in coverage.itertuples()],
        ),
        "",
        "`father_ever_entry` and related variables are relatives' recorded lifetime histories and are temporally ambiguous. Pre-birth fields require a SAFE focal birth year and a valid relative event year; unknown event years remain missing rather than being recoded as zero.",
        "",
    ]
    for algorithm in ["LogisticRegression", "CatBoost"]:
        table = main.loc[main["algorithm"].eq(algorithm)].sort_values(["population", "feature_set"])
        lines.extend([
            f"## {algorithm} results",
            "",
            markdown_table(
                ["Population", "Set", "ROC-AUC", "PR-AUC", "Bal. Acc.", "F1", "LogLoss", "Brier"],
                [[row.population, row.feature_set, format_float(row.roc_auc), format_float(row.pr_auc), format_float(row.balanced_accuracy), format_float(row.f1), format_float(row.log_loss), format_float(row.brier_score)] for row in table.itertuples()],
            ),
            "",
            "Metrics use the untouched frozen primary test partition and the fixed 0.5 threshold. A separate row in `model_metrics.csv` uses a balanced-accuracy threshold selected on validation only.",
            "",
        ])

    key_ablation = ablation.loc[ablation["comparison"].isin(["M2 - M1", "M3 - M2", "M4 - M3", "M6 - M4"])]
    lines.extend([
        "## Ablation",
        "",
        markdown_table(
            ["Algorithm", "Population", "Comparison", "Δ ROC-AUC", "Δ PR-AUC", "Δ LogLoss"],
            [[row.algorithm, row.population, row.comparison, format_float(row.delta_roc_auc), format_float(row.delta_pr_auc), format_float(row.delta_log_loss)] for row in key_ablation.itertuples()],
        ),
        "",
        "Negative Δ LogLoss indicates improvement. M4 measures incremental information in relatives' recorded cross-sectional political history; it does not identify a causal family effect.",
        "",
        "## Documentation bias",
        "",
    ])
    documentation = main.loc[main["feature_set"].isin(["M4", "M5", "M6"])]
    lines.extend([
        markdown_table(
            ["Algorithm", "Population", "Set", "ROC-AUC", "PR-AUC", "LogLoss"],
            [[row.algorithm, row.population, row.feature_set, format_float(row.roc_auc), format_float(row.pr_auc), format_float(row.log_loss)] for row in documentation.itertuples()],
        ),
        "",
        "M5's predictive strength demonstrates that CBDB recording structure itself carries substantial target information. M6 should therefore be read as a prediction benchmark with documentation controls, not as a cleaner estimate of historical mobility.",
        "",
        "## Family-aware robustness",
        "",
    ])
    family_compare = robustness.loc[robustness["analysis"].eq("primary_vs_family_group_split")]
    lines.extend([
        markdown_table(
            ["Algorithm", "Population", "Set", "Primary AUC", "Family AUC", "Δ AUC", "Δ PR-AUC"],
            [[row.algorithm, row.population, row.feature_set, format_float(row.reference_roc_auc), format_float(row.comparison_roc_auc), format_float(row.delta_roc_auc), format_float(row.delta_pr_auc)] for row in family_compare.itertuples()],
        ),
        "",
        "A decline under the frozen family-group split means part of conventional-split prediction may rely on shared structure among relatives; it is not a model failure. Largest Tang-component exclusion is recorded separately in `robustness_results.csv` without changing the frozen split.",
        "",
        "## Pre-birth lineage analysis",
        "",
        markdown_table(
            ["Algorithm", "Set", "Test N", "ROC-AUC", "PR-AUC", "Δ AUC vs PB0", "Δ PR-AUC vs PB0"],
            [[row.algorithm, row.feature_set, f"{row.n_test:,}", format_float(row.roc_auc), format_float(row.pr_auc), format_float(row.delta_roc_auc_vs_pb0), format_float(row.delta_pr_auc_vs_pb0)] for row in prebirth.itertuples()],
        ),
        "",
        "PB1 asks whether recorded lineage political capital already present before a person's birth adds predictive information for that person's later V1 record. It is not a matched pre-entry risk-time design; that design remains a future sensitivity analysis.",
        "",
        "## Bootstrap uncertainty",
        "",
        "The prespecified first-round bootstrap covers Global M0/M4/M5/M6 test predictions with 500 stratified resamples and seed 42.",
        "",
        markdown_table(
            ["Algorithm", "Set", "ROC 95% CI", "PR 95% CI"],
            [[row.algorithm, row.feature_set, f"[{format_float(row.roc_auc_ci_low)}, {format_float(row.roc_auc_ci_high)}]", f"[{format_float(row.pr_auc_ci_low)}, {format_float(row.pr_auc_ci_high)}]"] for row in intervals.itertuples()],
        ),
        "",
        "## Top model signals (sanity check, not causal effects)",
        "",
    ])
    top_coef = coefficients.loc[
        coefficients["population"].eq("Global") & coefficients["feature_set"].eq("M4")
    ].sort_values("absolute_coefficient_rank").head(12)
    top_importance = importance.loc[
        importance["population"].eq("Global") & importance["feature_set"].eq("M4")
    ].sort_values("importance_rank").head(12)
    lines.extend([
        "Logistic Global M4 (standardized/one-hot transformed scale):",
        "",
        markdown_table(
            ["Transformed feature", "Coefficient", "Absolute rank"],
            [[row.transformed_feature, format_float(row.coefficient), row.absolute_coefficient_rank] for row in top_coef.itertuples()],
        ),
        "",
        "CatBoost Global M4 built-in importance:",
        "",
        markdown_table(
            ["Feature", "Importance", "Rank"],
            [[row.feature, format_float(row.importance), row.importance_rank] for row in top_importance.itertuples()],
        ),
        "",
        "No SHAP, interaction attribution, network centrality, GNN, or hyperparameter search was run in Phase 2.",
        "",
        "## Scientific conclusions",
        "",
    ])
    # Conclusions use observed directions but retain intentionally conservative language.
    logistic_global = main.loc[main["algorithm"].eq("LogisticRegression") & main["population"].eq("Global")].set_index("feature_set")
    cat_global = main.loc[main["algorithm"].eq("CatBoost") & main["population"].eq("Global")].set_index("feature_set")
    family_drop = family_compare.loc[family_compare["feature_set"].eq("M4"), "delta_roc_auc"].min()
    lines.extend([
        f"1. Dynasty alone is a strong database-wide baseline (Global M0 ROC-AUC {logistic_global.loc['M0', 'roc_auc']:.3f} Logistic; {cat_global.loc['M0', 'roc_auc']:.3f} CatBoost), largely reflecting between-dynasty differences in CBDB representation and V1 recording.",
        f"2. Geography adds substantial incremental prediction in the Global benchmark (M2−M1 Δ ROC-AUC {logistic_global.loc['M2', 'roc_auc'] - logistic_global.loc['M1', 'roc_auc']:+.3f} Logistic; {cat_global.loc['M2', 'roc_auc'] - cat_global.loc['M1', 'roc_auc']:+.3f} CatBoost).",
        f"3. Family structural fields add further Global information (M3−M2 {logistic_global.loc['M3', 'roc_auc'] - logistic_global.loc['M2', 'roc_auc']:+.3f} Logistic; {cat_global.loc['M3', 'roc_auc'] - cat_global.loc['M2', 'roc_auc']:+.3f} CatBoost).",
        f"4. Cross-sectional family political capital has a smaller conditional Global increment beyond M3 (M4−M3 {logistic_global.loc['M4', 'roc_auc'] - logistic_global.loc['M3', 'roc_auc']:+.3f} Logistic; {cat_global.loc['M4', 'roc_auc'] - cat_global.loc['M3', 'roc_auc']:+.3f} CatBoost).",
        f"5. Documentation-only prediction is substantial (Global M5 ROC-AUC {logistic_global.loc['M5', 'roc_auc']:.3f} Logistic; {cat_global.loc['M5', 'roc_auc']:.3f} CatBoost), so selection and recording processes are central limitations.",
        "6. Song and Ming estimates differ in magnitude; period-specific models should not be assumed interchangeable.",
        f"7. The most negative M4 family-aware change is {family_drop:+.3f} ROC-AUC, quantifying generalization sensitivity when relatives cannot cross partitions.",
        "8. Father's recorded ENTRY history is an association with focal V1 record presence, not evidence that paternal entry caused the focal record.",
        "9. Pre-birth results apply only to the minority with a SAFE birth year and sufficiently dated relative events; sparse coverage limits generalization.",
        "10. All results describe people represented in CBDB and are not estimates of historical population entry or social-mobility rates.",
        "",
        "## Next step",
        "",
    ])
    geo_gain = max(
        logistic_global.loc["M2", "roc_auc"] - logistic_global.loc["M1", "roc_auc"],
        cat_global.loc["M2", "roc_auc"] - cat_global.loc["M1", "roc_auc"],
    )
    family_gain = max(
        logistic_global.loc["M4", "roc_auc"] - logistic_global.loc["M3", "roc_auc"],
        cat_global.loc["M4", "roc_auc"] - cat_global.loc["M3", "roc_auc"],
    )
    documentation_strength = max(logistic_global.loc["M5", "roc_auc"], cat_global.loc["M5", "roc_auc"])
    if documentation_strength >= 0.80:
        recommendation = "Prioritize documentation-bias-controlled modeling before substantive interpretation. SHAP can be run later on locked M4/M6 models, but must be stratified/controlled by documentation intensity and presented as predictive attribution only."
    elif geo_gain > family_gain:
        recommendation = "Prioritize spatial/regional validation and historical geography sensitivity; lock the model before any SHAP work."
    else:
        recommendation = "The M4 increment supports a locked-model SHAP follow-up focused on family political capital, with family-aware results reported alongside it."
    lines.extend([recommendation, ""])
    return "\n".join(lines)


def main() -> int:
    logger = setup_logging("phase2_final_sanity", PROJECT_ROOT / "outputs/logs/phase2_final_sanity.log")
    dataset = pd.read_parquet(PROJECT_ROOT / "data/modeling/person_phase2_features.parquet")
    metrics = pd.read_csv(PROJECT_ROOT / "outputs/phase2/tables/model_metrics.csv")
    report = build_report(dataset, metrics)
    atomic_write_text(PROJECT_ROOT / "docs/phase2/phase2_results.md", report)
    invariants = enforce_invariants(dataset, metrics)
    atomic_write_text(
        PROJECT_ROOT / "outputs/phase2/tables/phase2_invariants.json",
        json.dumps(invariants, ensure_ascii=False, indent=2) + "\n",
    )
    logger.info("All Phase 2 invariants PASS")
    print("===========================================")
    print("PHASE 2 FEATURE ENGINEERING & MODELING PASS")
    print("===========================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
