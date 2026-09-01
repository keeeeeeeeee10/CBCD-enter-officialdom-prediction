#!/usr/bin/env python3
"""Generate Phase 2.6 final reports and, after tests, terminal invariants."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.phase26 import validate_locked_feature_sets
from src.utils import atomic_write_text, markdown_table, setup_logging, sha256_file


TABLES = PROJECT_ROOT / "outputs/phase2_6/tables"
DOCS = PROJECT_ROOT / "docs/phase2_6"


def delta_table(path: Path, comparisons: list[str]) -> str:
    frame = pd.read_csv(path)
    frame = frame.loc[frame["comparison"].isin(comparisons)]
    return markdown_table(
        ["Population", "Comparison", "Δ ROC-AUC", "Δ PR-AUC"],
        ([row.population, row.comparison, f"{row.delta_roc_auc:+.6f}", f"{row.delta_pr_auc:+.6f}"] for row in frame.itertuples()),
    )


def locked_table(metrics: pd.DataFrame) -> str:
    return markdown_table(
        ["Population", "Model", "ROC-AUC", "PR-AUC", "LogLoss", "Brier", "Raw ECE", "Model SHA256"],
        ([
            row.population, row.model_id, f"{row.roc_auc:.6f}", f"{row.pr_auc:.6f}",
            f"{row.log_loss:.6f}", f"{row.brier_score:.6f}", f"{row.raw_ece:.6f}", row.model_sha256,
        ] for row in metrics.itertuples()),
    )


def top_shap_table(shap: pd.DataFrame) -> str:
    top = shap.sort_values(["population", "model_id", "rank"]).groupby(["population", "model_id"], group_keys=False).head(3)
    return markdown_table(
        ["Population", "Model", "Group", "Share of total |SHAP|", "Rank"],
        ([row.population, row.model_id, row.feature_group, f"{row.group_share_of_total_abs_shap:.2%}", row.rank] for row in top.itertuples()),
    )


def generate_reports() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "model_cards").mkdir(parents=True, exist_ok=True)
    birth = pd.read_csv(TABLES / "birth_missingness_deltas.csv")
    address = pd.read_csv(TABLES / "address_semantics_deltas.csv")
    stability = pd.read_csv(TABLES / "multiseed_delta_summary.csv")
    stability_auc = stability.loc[stability["metric"].eq("roc_auc")]
    matched = pd.read_csv(TABLES / "matched_random_vs_spatial_results.csv")
    metrics = pd.read_csv(TABLES / "final_model_metrics.csv")
    shap = pd.read_csv(PROJECT_ROOT / "outputs/phase2_6/shap/shap_group_summary.csv")
    context = pd.read_csv(TABLES / "final_population_target_context.csv")
    gender = pd.read_csv(TABLES / "final_gender_entry_rates.csv")
    feature_lists = pd.read_csv(TABLES / "final_model_feature_lists.csv")

    major = context.loc[context["dynasty_name"].isin(["Tang", "Song", "Yuan", "Ming", "Qing"])]
    data_report = [
        "# 谁会留下入仕记录？",
        "",
        "## 基于 CBDB 的性别、地域、家族可观测性与史料记录偏差分析",
        "",
        "**English title:** Who Leaves a Recorded Path into Government? Gender, Geography, Family Observability, and Documentation Bias in CBDB",
        "",
        "The outcome throughout this chapter is **presence of at least one CBDB `ENTRY_DATA` record**. Every rate is a share among CBDB-listed people; it is not an estimate of actual office holding, actual government entry, or the historical Chinese population.",
        "",
        "## 1. Dynasty and gender context",
        "",
        markdown_table(
            ["Dynasty", "CBDB-listed people", "ENTRY-positive", "Recorded share"],
            ([row.dynasty_name, f"{row.n_people:,}", f"{row.n_entry_positive:,}", f"{row.entry_record_presence_rate:.2%}"] for row in major.itertuples()),
        ),
        "",
        "Gender differences are large in the recorded data, but they combine historical structure, database selection, and documentation processes. They are not causal gender effects.",
        "",
        markdown_table(
            ["Population", "Gender", "People", "Recorded share"],
            ([row.population, row.gender, f"{row.n_people:,}", f"{row.entry_record_presence_rate:.2%}"] for row in gender.itertuples()),
        ),
        "",
        "## 2. ENTRY pathway composition",
        "",
        "`entry_category_by_dynasty_records.csv` reports mutually assigned record-level shares. `entry_category_by_dynasty_people.csv` reports non-exclusive unique-person prevalence: one person can have multiple categories, so prevalence can sum above 100%.",
        "",
        "See `outputs/phase2_6/figures/final_entry_pathways_by_dynasty.png`.",
        "",
        "## 3. Birth information",
        "",
        delta_table(TABLES / "birth_missingness_deltas.csv", ["B1 - B0", "B2 - B0", "B3 - B2", "B_OBSERVED_1 - B_OBSERVED_0"]),
        "",
        "The Phase 2.5 P3−P2 result requires a narrower interpretation. In the current CatBoost missing-value mechanism, an explicit missing indicator supplies little additional information after a missing-aware birth value is already present. It does **not** show that birth-year availability has no predictive information by itself.",
        "",
        "## 4. Geography: location versus record semantics",
        "",
        delta_table(TABLES / "address_semantics_deltas.csv", ["A1 - A0", "A2 - A1", "A3 - A2", "A4 - A3", "A5 - A4"]),
        "",
        "Address observability, historical administrative categories, continuous coordinates/capital distance, and `addr_type_name` are reported separately. `addr_type_name` is documentation-linked address semantics, not pure physical geography. The matched-support comparison is a spatial distribution-shift sensitivity, not a causal experiment.",
        "",
        "## 5. Family: observability, topology, and recorded capital",
        "",
        "Phase 2.5 showed that family observability is the dominant family signal and topology adds a smaller increment. The five-seed results below assess whether full-record or train-observed cross-sectional family capital adds stable predictive discrimination.",
        "",
        markdown_table(
            ["Population", "Comparison", "Mean ΔAUC", "SD", "Min", "Max", "Positive seeds", "Magnitude"],
            ([row.population, row.comparison, f"{row.mean_delta:+.6f}", f"{row.std_delta:.6f}", f"{row.min_delta:+.6f}", f"{row.max_delta:+.6f}", f"{row.n_positive_seeds}/{row.n_seeds}", row.practical_magnitude] for row in stability_auc.itertuples()),
        ),
        "",
        "F3 is full-record cross-sectional capital; F4/D6i use only relatives observed in training, but remain cross-sectional rather than strict pre-entry measures. Neither supports a strong causal inheritance claim.",
        "",
        "## 6. Documentation bias and spatial transport",
        "",
        "High AUC and strong documentation bias can coexist. H_STRUCT is the cleaner structural association model, D5_MAIN is the main documentation-linked predictor, and D6_UPPER is a database record-structure upper bound. Their distinct meanings must not be collapsed into one ‘best’ model.",
        "",
        "The matched random/spatial results use the identical reliable-prefecture support. Lower spatial performance indicates weaker transport to unseen historical regions; it does not identify a causal geography effect.",
        "",
        "## 7. Feature coverage",
        "",
        "`final_feature_coverage.csv` distinguishes `non_missing_rate` from `positive_flag_rate`. For binary flags, 100% non-missing means the 0/1 field is complete; it does not mean every person has the recorded characteristic.",
        "",
        "## Interpretation rule",
        "",
        "SHAP explains model prediction attribution, not causal effect. The final figures and tables consistently refer to ENTRY record presence among CBDB-listed people.",
        "",
    ]
    atomic_write_text(DOCS / "final_data_analysis.md", "\n".join(data_report))

    model_report = [
        "# Phase 2.6 Final Model Report",
        "",
        "## Target and protocol",
        "",
        "Target V1 is `ENTRY_DATA` record presence. All canonical models use seed 42 and the unchanged frozen Primary train/validation/test person IDs. Validation alone controls early stopping, class-weight choice, threshold selection, and the optional diagnostic sigmoid calibration. Test data are not used for selection.",
        "",
        "No hyperparameter search, GNN, or PageRank was run. Seeds 202, 2024, 2025, and 2026 are stability checks only; no best seed was selected.",
        "",
        "## Locked canonical models",
        "",
        locked_table(metrics),
        "",
        "- **H_STRUCT:** historical structural prediction associations; excludes `addr_type_name`, general documentation, supervised target priors, and relatives’ outcomes.",
        "- **D5_MAIN:** main predictive model; includes documentation-linked fields and a fold-safe local prior, but no relatives’ ENTRY/posting outcomes.",
        "- **D6_UPPER:** D5 plus explicitly allowlisted full-record cross-sectional family outcomes; a record-structure upper bound, not a strict pre-entry model.",
        "",
        "## Five-seed stability",
        "",
        markdown_table(
            ["Population", "Comparison", "Mean ΔAUC", "SD", "Range", "Positive seeds", "Practical magnitude"],
            ([row.population, row.comparison, f"{row.mean_delta:+.6f}", f"{row.std_delta:.6f}", f"[{row.min_delta:+.6f}, {row.max_delta:+.6f}]", f"{row.n_positive_seeds}/{row.n_seeds}", row.practical_magnitude] for row in stability_auc.itertuples()),
        ),
        "",
        "Statistical detectability, seed stability, and practical importance are distinct. A consistent increment below 0.002 ROC-AUC is explicitly labeled small.",
        "",
        "## Matched-support spatial sensitivity",
        "",
        markdown_table(
            ["Population", "Model", "Random AUC/PR", "Spatial AUC/PR", "Δ spatial−random AUC/PR"],
            ([row.population, row.model_id, f"{row.matched_random_roc_auc:.6f}/{row.matched_random_pr_auc:.6f}", f"{row.matched_spatial_roc_auc:.6f}/{row.matched_spatial_pr_auc:.6f}", f"{row.delta_spatial_minus_random_roc_auc:+.6f}/{row.delta_spatial_minus_random_pr_auc:+.6f}"] for row in matched.itertuples()),
        ),
        "",
        "The random and spatial test IDs differ, so no paired individual bootstrap is claimed.",
        "",
        "## Calibration",
        "",
        "Raw balanced-weight probabilities are not assumed calibrated. `final_model_calibration.csv` reports raw ECE/Brier/LogLoss and a validation-fitted sigmoid diagnostic evaluated on test. The calibrated probability is diagnostic, not selected on test.",
        "",
        "## Grouped SHAP",
        "",
        top_shap_table(shap),
        "",
        "Native CatBoost SHAP was computed for the nine seed-42 model/population combinations on shared frozen-test samples. Additivity is checked in raw-logit space. Group shares sum to one within tolerance.",
        "",
        "**SHAP explains model prediction attribution, not causal effect.** H_STRUCT, D5_MAIN, and D6_UPPER answer different questions and their attributions must not be merged into a single historical conclusion.",
        "",
        "## Reproduction",
        "",
        "Run `bash scripts/run_phase2_6.sh`. Exact features, parameters, model hashes, prediction hashes, thresholds, and best iterations are saved in `outputs/phase2_6/tables/` and `outputs/phase2_6/models/canonical_model_metadata.json`.",
        "",
    ]
    atomic_write_text(DOCS / "final_model_report.md", "\n".join(model_report))

    limitations = """# Final Interpretation and Limitations

## Scientific scope

The target is presence of at least one CBDB `ENTRY_DATA` record. It is not actual government-entry probability, actual office holding, or an estimate for the historical population of China. ENTRY credentials and routes are not equivalent to a verified posting.

## Selection and documentation

CBDB is a selected historical database. Survival of sources, editorial attention, lineage documentation, address recording, biography density, and institutional coverage vary sharply across periods and social groups. Consequently, strong discrimination and strong documentation bias can coexist.

H_STRUCT reduces explicit documentation-linked content, but address and family observability can still encode record survival. D5_MAIN is deliberately a documentation-linked predictor. D6_UPPER uses relatives’ complete recorded outcomes and is only a database-internal record-structure upper bound.

## Time and family ambiguity

Full-record family ENTRY/posting outcomes are cross-sectional and temporally ambiguous. Train-observed family outcomes restrict whose records are visible but are not strict pre-entry measures. Pre-birth lineage coverage is sparse and is not equivalent to matched pre-entry family capital.

## Geography and transport

Historical administrative categories, address observability, physical coordinates, and address-record semantics are separate constructs. `addr_type_name` is documentation-linked. Matched spatial holdout tests distribution shift to unseen historical region groups; it is not a causal experiment and does not establish geographic effects.

## SAFE birth information

SAFE birth-year coverage is low. When CatBoost already sees a missing-aware value, the explicit flag can be redundant. Therefore P3−P2≈0 means only that the explicit indicator adds little under that representation; it does not mean birth-year availability has no predictive information.

## Calibration and interpretation

Balanced class weights can shift raw probabilities. Validation-fitted sigmoid results are diagnostic. Neither raw nor calibrated values should be described as an individual's real probability of entering government.

SHAP explains attribution within a fitted predictive model, not causal effect. “Gender causes ENTRY,” “prefecture causes entry,” and “father ENTRY causes child ENTRY” are unsupported statements. Global results describe the assembled CBDB population, not the overall population of historical China.
"""
    atomic_write_text(DOCS / "final_interpretation_and_limitations.md", limitations)

    meanings = {
        "H_STRUCT": ("Historical Structural Model", "Historical structural prediction associations", "No general documentation, address-record type, supervised local prior, or relatives’ outcomes."),
        "D5_MAIN": ("Main Predictive Model", "Main prediction of ENTRY record presence", "Contains documentation-linked predictors and a fold-safe local prior; it is not a pure historical-mechanism model."),
        "D6_UPPER": ("Record-Structure Upper Bound", "Database-internal predictive upper bound", "Adds full-record cross-sectional relatives’ ENTRY/posting outcomes and is not strict pre-entry."),
    }
    for model_id, (title, use, limitation) in meanings.items():
        model_metrics = metrics.loc[metrics["model_id"].eq(model_id)]
        model_features = feature_lists.loc[feature_lists["model_id"].eq(model_id)]
        card = [
            f"# {model_id}: {title}", "", f"**Intended use:** {use}.", "",
            "**Target:** CBDB ENTRY_DATA record presence.", "",
            "**Canonical protocol:** seed 42, frozen Primary split, validation-controlled early stopping/class weights/threshold.", "",
            f"**Known limitation:** {limitation}", "",
            "## Test metrics", "", locked_table(model_metrics), "",
            "## Resolved features", "",
            markdown_table(["Feature", "Role"], ([row.feature, row.role] for row in model_features.itertuples())), "",
            "## Interpretation", "",
            "SHAP and feature importance describe prediction attribution, not causal effects. The model must be interpreted only according to its stated scientific role.", "",
        ]
        atomic_write_text(DOCS / f"model_cards/{model_id}.md", "\n".join(card))


def tree_manifest(roots: list[Path]) -> dict[str, str]:
    return {
        str(path.relative_to(PROJECT_ROOT)): sha256_file(path)
        for root in roots for path in sorted(root.rglob("*")) if path.is_file()
    }


def final_invariants() -> None:
    semantic = json.loads((TABLES / "semantic_patch.json").read_text())
    hashes = semantic["frozen_hashes"]
    paths = {
        "database": "database/cbdb_20260829.sqlite3", "working_database": "database/cbdb_working.sqlite3",
        "target": "data/interim/person_target.parquet", "base": "data/processed/person_base_v0.parquet",
        "phase2_master": "data/modeling/person_phase2_features.parquet",
        "primary": "data/splits/split_primary_dynasty_target.parquet", "random": "data/splits/split_random_benchmark.parquet",
        "family": "data/splits/split_family_group_robustness.parquet", "temporal": "data/splits/split_safe_temporal.parquet",
    }
    unchanged = {key: sha256_file(PROJECT_ROOT / path) == hashes[key] for key, path in paths.items()}
    with sqlite3.connect(f"file:{(PROJECT_ROOT / paths['working_database']).resolve().as_posix()}?mode=ro", uri=True) as connection:
        quick_check = connection.execute("PRAGMA quick_check").fetchone()[0]
    phase2_current = tree_manifest([PROJECT_ROOT / "outputs/phase2", PROJECT_ROOT / "docs/phase2"])
    phase2_frozen = json.loads((PROJECT_ROOT / "outputs/phase2_5/tables/phase2_preservation_manifest.json").read_text())["files"]
    phase25_current = tree_manifest([PROJECT_ROOT / "outputs/phase2_5", PROJECT_ROOT / "docs/phase2_5"])
    phase25_frozen = json.loads((TABLES / "phase2_5_preservation_manifest.json").read_text())["files"]
    lock = json.loads((TABLES / "final_model_lock_manifest.json").read_text())
    multiseed = pd.read_csv(TABLES / "multiseed_model_metrics.csv")
    multiseed_ok = (
        set(multiseed["seed"].astype(int)) == {42, 202, 2024, 2025, 2026}
        and multiseed.groupby(["population", "model_id"])["seed"].nunique().eq(5).all()
    )
    spatial = json.loads((TABLES / "matched_spatial_overlap_check.json").read_text())
    shap = json.loads((PROJECT_ROOT / "outputs/phase2_6/shap/shap_additivity_check.json").read_text())
    shap_ok = shap.get("status") == "PASS" and len(shap.get("checks", [])) == 9 and all(row["status"] == "PASS" for row in shap["checks"])
    reports = [
        DOCS / "final_data_analysis.md", DOCS / "final_model_report.md",
        DOCS / "final_interpretation_and_limitations.md", DOCS / "address_feature_policy.md",
        *(DOCS / "model_cards" / f"{model}.md" for model in ["H_STRUCT", "D5_MAIN", "D6_UPPER"]),
    ]
    report_ok = all(path.exists() and "[svg]" not in path.read_text(encoding="utf-8") for path in reports)
    pytest_log = (PROJECT_ROOT / "outputs/phase2_6/logs/pytest_phase2_6.log").read_text(encoding="utf-8")
    passed_match = re.search(r"(\d+) passed", pytest_log)
    failed_match = re.search(r"(\d+) failed", pytest_log)
    tests_passed = int(passed_match.group(1)) if passed_match else 0
    tests_failed = int(failed_match.group(1)) if failed_match else 0
    coverage = pd.read_csv(TABLES / "final_feature_coverage.csv")
    coverage_check = coverage.loc[
        coverage["population"].eq("Global") & coverage["feature"].isin(["has_geography", "father_identified"])
    ]
    coverage_ok = len(coverage_check) == 2 and coverage_check["non_missing_rate"].eq(1).all() and coverage_check["positive_flag_rate"].lt(1).all()
    validate_locked_feature_sets()
    checks = {
        "database_sha256_unchanged": unchanged["database"],
        "working_db_sha256_unchanged": unchanged["working_database"],
        "target_sha256_unchanged": unchanged["target"],
        "base_sha256_unchanged": unchanged["base"],
        "phase2_master_sha256_unchanged": unchanged["phase2_master"],
        "primary_split_sha256_unchanged": unchanged["primary"],
        "random_split_sha256_unchanged": unchanged["random"],
        "family_split_sha256_unchanged": unchanged["family"],
        "temporal_split_sha256_unchanged": unchanged["temporal"],
        "phase2_outputs_unchanged": phase2_current == phase2_frozen,
        "phase2_5_outputs_unchanged": phase25_current == phase25_frozen,
        "working_db_quick_check": quick_check,
        "model_lock_tests": "PASS" if lock.get("status") == "FINAL_MODELS_LOCKED" else "FAIL",
        "multiseed_tests": "PASS" if multiseed_ok else "FAIL",
        "spatial_support_tests": spatial.get("status", "FAIL"),
        "shap_additivity_tests": "PASS" if shap_ok else "FAIL",
        "report_tests": "PASS" if report_ok and coverage_ok else "FAIL",
        "pytest_passed": tests_passed,
        "pytest_failed": tests_failed,
        "formal_shap_run": True,
        "gnn_run": False,
        "pagerank_run": False,
        "hyperparameter_search_run": False,
    }
    boolean_keys = [key for key, value in checks.items() if isinstance(value, bool) and key not in {"formal_shap_run", "gnn_run", "pagerank_run", "hyperparameter_search_run"}]
    pass_strings = ["model_lock_tests", "multiseed_tests", "spatial_support_tests", "shap_additivity_tests", "report_tests"]
    if (
        not all(checks[key] for key in boolean_keys)
        or any(checks[key] != "PASS" for key in pass_strings)
        or quick_check != "ok" or tests_passed == 0 or tests_failed != 0
        or not checks["formal_shap_run"] or checks["gnn_run"] or checks["pagerank_run"] or checks["hyperparameter_search_run"]
    ):
        raise RuntimeError(f"Phase 2.6 final invariant failure: {checks}")
    atomic_write_text(TABLES / "phase2_6_invariants.json", json.dumps({"status": "PASS", **checks}, ensure_ascii=False, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final-invariants", action="store_true")
    args = parser.parse_args()
    logger = setup_logging("phase2_6_reports", PROJECT_ROOT / "outputs/phase2_6/logs/final_reports.log")
    if args.final_invariants:
        final_invariants()
        logger.info("Phase 2.6 final invariants PASS")
    else:
        generate_reports()
        logger.info("Phase 2.6 final reports and model cards generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
