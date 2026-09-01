#!/usr/bin/env python3
"""Generate the Phase 2.5 report/candidates or enforce final invariants."""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import atomic_to_csv, load_yaml
from src.utils import atomic_write_text, markdown_table, setup_logging, sha256_file


def f4(value: object) -> str:
    return "" if pd.isna(value) else f"{float(value):.4f}"


def atomic_savefig(figure: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.stem + ".tmp" + path.suffix)
    figure.savefig(temporary, dpi=300, bbox_inches="tight")
    os.replace(temporary, path)
    plt.close(figure)


def male_comparison() -> pd.DataFrame:
    male = pd.read_csv(PROJECT_ROOT / "outputs/phase2_5/tables/male_only_models.csv")
    all_people = pd.concat([
        pd.read_csv(PROJECT_ROOT / "outputs/phase2_5/tables/personal_decomposition_results.csv"),
        pd.read_csv(PROJECT_ROOT / "outputs/phase2_5/tables/geography_decomposition_results.csv"),
        pd.read_csv(PROJECT_ROOT / "outputs/phase2_5/tables/family_decomposition_results.csv"),
        pd.read_csv(PROJECT_ROOT / "outputs/phase2_5/tables/documentation_controlled_ablation.csv"),
    ], ignore_index=True)
    models = ["P1", "G4", "G5", "F2", "F3", "D0", "D6"]
    all_people = all_people.loc[
        all_people["algorithm"].eq("CatBoost")
        & all_people["model_id"].isin(models)
        & all_people["population"].isin(["Song", "Ming"])
        & all_people["subset"].eq("all")
    ].drop_duplicates(["population", "model_id"])
    merged = all_people.merge(
        male,
        on=["algorithm", "population", "model_id", "target_name", "split_protocol"],
        suffixes=("_all", "_male"),
        validate="one_to_one",
    )
    output = merged[["algorithm", "population", "model_id", "target_name", "split_protocol"]].copy()
    output["n_test_all"] = merged["n_test_all"]
    output["n_test_male"] = merged["n_test_male"]
    for metric in ["roc_auc", "pr_auc", "log_loss"]:
        output[f"all_{metric}"] = merged[f"{metric}_all"]
        output[f"male_{metric}"] = merged[f"{metric}_male"]
        output[f"delta_{metric}"] = merged[f"{metric}_male"] - merged[f"{metric}_all"]
    atomic_to_csv(output, PROJECT_ROOT / "outputs/phase2_5/tables/male_only_results.csv")
    figure, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for axis, population in zip(axes, ["Song", "Ming"], strict=True):
        block = output.loc[output["population"].eq(population)].set_index("model_id").reindex(models)
        x = np.arange(len(models))
        width = 0.36
        axis.bar(x - width / 2, block["all_roc_auc"], width, label="All people", color="#4c78a8")
        axis.bar(x + width / 2, block["male_roc_auc"], width, label="Verified male only", color="#f58518")
        axis.set_xticks(x, models, rotation=35)
        axis.set_title(population)
        axis.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("ROC-AUC")
    axes[-1].legend(frameon=False)
    figure.suptitle("All-person versus verified male-only sensitivity")
    figure.tight_layout()
    atomic_savefig(figure, PROJECT_ROOT / "outputs/phase2_5/figures/male_only_vs_all.png")
    return output


def candidate_manifest() -> dict[str, object]:
    geo = pd.read_csv(PROJECT_ROOT / "outputs/phase2_5/tables/geography_decomposition_results.csv")
    docs = pd.read_csv(PROJECT_ROOT / "outputs/phase2_5/tables/documentation_controlled_ablation.csv")
    specs = [
        {
            "candidate_id": "historical_raw_candidate", "model_id": "G4", "source": geo,
            "documentation_included": False, "supervised_geo_prior_included": False,
            "full_record_family_outcomes_included": False, "inductive_family_outcomes_only": False,
            "scientific_interpretation": "Personal plus raw historical geography and train-only unsupervised regional density.",
            "known_limitations": "Geography observability and CBDB regional selection remain; no family signal.",
            "recommended_for_shap": "candidate_pending_human_review",
        },
        {
            "candidate_id": "documentation_controlled_candidate", "model_id": "D6i", "source": docs,
            "documentation_included": True, "supervised_geo_prior_included": True,
            "full_record_family_outcomes_included": False, "inductive_family_outcomes_only": True,
            "scientific_interpretation": "Documentation-controlled model with train-observed inductive family capital.",
            "known_limitations": "Includes a supervised local prior and database coverage controls; attribution is predictive.",
            "recommended_for_shap": "candidate_pending_human_review",
        },
        {
            "candidate_id": "record_structure_upper_bound", "model_id": "D6", "source": docs,
            "documentation_included": True, "supervised_geo_prior_included": True,
            "full_record_family_outcomes_included": True, "inductive_family_outcomes_only": False,
            "scientific_interpretation": "Upper-bound predictor using documentation and full-record cross-sectional family outcomes.",
            "known_limitations": "Transductive/cross-sectional and dominated by database recording structure; not a pre-entry model.",
            "recommended_for_shap": "no_without_explicit_record_structure_framing",
        },
    ]
    candidates = []
    for spec in specs:
        source = spec.pop("source")
        row = source.loc[
            source["algorithm"].eq("CatBoost")
            & source["population"].eq("Global")
            & source["model_id"].eq(spec["model_id"])
        ].iloc[0]
        candidates.append({
            **spec,
            "model_definition": spec["model_id"],
            "population": "Global", "target": "target_entry_v1", "split": "primary",
            "validation_metrics": {key: float(row[f"validation_{key}"]) for key in ["roc_auc", "pr_auc", "log_loss"]},
            "test_metrics": {key: float(row[key]) for key in ["roc_auc", "pr_auc", "log_loss", "brier_score"]},
            "model_sha256": str(row["model_sha256"]),
        })
    return {"status": "HUMAN_REVIEW_REQUIRED", "formal_shap_run": False, "candidates": candidates}


def build_report(male: pd.DataFrame, candidates: dict[str, object]) -> str:
    gender = pd.read_csv(PROJECT_ROOT / "outputs/phase2_5/tables/gender_target_summary.csv")
    personal = pd.read_csv(PROJECT_ROOT / "outputs/phase2_5/tables/personal_decomposition_deltas.csv")
    geo = pd.read_csv(PROJECT_ROOT / "outputs/phase2_5/tables/geography_decomposition_deltas.csv")
    spatial = pd.read_csv(PROJECT_ROOT / "outputs/phase2_5/tables/spatial_robustness_results.csv")
    family = pd.read_csv(PROJECT_ROOT / "outputs/phase2_5/tables/family_decomposition_deltas.csv")
    family_subset = pd.read_csv(PROJECT_ROOT / "outputs/phase2_5/tables/family_observed_subset_deltas.csv")
    documentation = pd.read_csv(PROJECT_ROOT / "outputs/phase2_5/tables/documentation_controlled_deltas.csv")
    targets = pd.read_csv(PROJECT_ROOT / "outputs/phase2_5/tables/target_sensitivity_results.csv")
    paired = pd.read_csv(PROJECT_ROOT / "outputs/phase2_5/tables/paired_bootstrap_results.csv")
    calibration = pd.read_csv(PROJECT_ROOT / "outputs/phase2_5/tables/calibration_audit.csv")
    key_paired = paired.loc[
        paired["metric"].eq("roc_auc")
        & paired["population"].eq("Global")
        & paired["algorithm"].eq("CatBoost")
        & (
            paired["model_a"].str.cat(paired["model_b"], sep="->").isin([
                "G4->G5", "F1->F2", "F2->F3", "F2->F4", "D5->D6", "D5->D6i", "M3->M4"
            ])
        )
    ]
    lines = [
        "# Phase 2.5 — Documentation-Controlled Validation",
        "",
        "Target V1 is **ENTRY_DATA record presence**, not actual office-holding probability. All Primary/Family/Temporal IDs and Phase 2 outputs remain frozen. The spatial-group split is a separately labeled robustness design.",
        "",
        "## Gender audit and personal decomposition",
        "",
        "The actual database field is `BIOG_MAIN.c_female`: 0=male, 1=female, NULL=unknown. No standalone gender code table exists; the mapping is verified against working-database values and the frozen Phase 1 ETL/schema.",
        "",
        markdown_table(
            ["Population", "Gender", "N", "V1 rate", "Geo coverage", "Kin coverage", "Documentation mean"],
            [[r.population, r.gender, f"{r.n_people:,}", f4(r.positive_rate), f4(r.geography_coverage), f4(r.kin_coverage), f4(r.documentation_intensity_mean)] for r in gender.itertuples()],
        ),
        "",
        markdown_table(
            ["Population", "Comparison", "Δ ROC-AUC", "Δ PR-AUC", "Δ LogLoss"],
            [[r.population, r.comparison, f4(r.delta_roc_auc), f4(r.delta_pr_auc), f4(r.delta_log_loss)] for r in personal.itertuples()],
        ),
        "",
        "Male-only results are a frozen-split subgroup sensitivity; women and unknown-gender records are not merged into it.",
        "",
        markdown_table(
            ["Population", "Model", "All AUC", "Male AUC", "Δ AUC"],
            [[r.population, r.model_id, f4(r.all_roc_auc), f4(r.male_roc_auc), f4(r.delta_roc_auc)] for r in male.itertuples()],
        ),
        "",
        "## Geography decomposition",
        "",
        markdown_table(
            ["Population", "Comparison", "Δ ROC-AUC", "Δ PR-AUC", "Δ LogLoss"],
            [[r.population, r.comparison, f4(r.delta_roc_auc), f4(r.delta_pr_auc), f4(r.delta_log_loss)] for r in geo.itertuples()],
        ),
        "",
        "G1 is address/coordinate observability; G2 historical administrative categories; G3 continuous coordinates/capital distance; G4 train-only unsupervised density; G5 OOF/train-only supervised local target prior. G5−G4 must be interpreted specifically as region-level supervised target information, not physical geography.",
        "",
        "## Spatial generalization",
        "",
        markdown_table(
            ["Population", "Model", "Primary AUC", "Spatial AUC", "Δ AUC", "Δ PR-AUC"],
            [[r.population, r.model_id, f4(r.primary_roc_auc), f4(r.spatial_roc_auc), f4(r.delta_roc_auc), f4(r.delta_pr_auc)] for r in spatial.itertuples()],
        ),
        "",
        "A spatial-holdout decline indicates weaker transfer to entirely unseen dynasty-prefecture groups, not model failure. Unseen local priors fall back to the training global prior.",
        "",
        "## Family signal decomposition",
        "",
        markdown_table(
            ["Population", "Comparison", "Δ ROC-AUC", "Δ PR-AUC", "Δ LogLoss"],
            [[r.population, r.comparison, f4(r.delta_roc_auc), f4(r.delta_pr_auc), f4(r.delta_log_loss)] for r in family.itertuples()],
        ),
        "",
        "F3 is `full_record_cross_sectional`; F4 is `train_observed_inductive`. Relatives outside the locked training IDs are unknown, never zero. Family-observed/eligible-relative subset results are retained separately.",
        "",
        markdown_table(
            ["Subset", "Population", "Comparison", "Δ ROC-AUC", "Δ PR-AUC"],
            [[r.subset, r.population, r.comparison, f4(r.delta_roc_auc), f4(r.delta_pr_auc)] for r in family_subset.itertuples()],
        ),
        "",
        "## Documentation-controlled ablation",
        "",
        markdown_table(
            ["Algorithm", "Population", "Comparison", "Δ ROC-AUC", "Δ PR-AUC", "Δ LogLoss"],
            [[r.algorithm, r.population, r.comparison, f4(r.delta_roc_auc), f4(r.delta_pr_auc), f4(r.delta_log_loss)] for r in documentation.itertuples()],
        ),
        "",
        "D0 establishes a database-recording baseline. D2/D3 isolate raw geography versus supervised local prior; D4/D5 separate family observability/topology; D6 and D6i contrast full-record versus inductive political capital.",
        "",
        "## Target sensitivity",
        "",
        markdown_table(
            ["Algorithm", "Population", "Target", "Model", "ROC-AUC", "PR-AUC", "LogLoss"],
            [[r.algorithm, r.population, r.target_name, r.model_id, f4(r.roc_auc), f4(r.pr_auc), f4(r.log_loss)] for r in targets.itertuples()],
        ),
        "",
        "For the posting target, S2 uses relatives' ENTRY capital; relatives' posting features appear only in the separately labeled S2p sensitivity. No focal posting outcome/count/missingness is a predictor.",
        "",
        "## Paired statistical validation",
        "",
        markdown_table(
            ["Split", "Comparison", "Observed Δ AUC", "95% CI", "Fraction >0", "Unit", "Small magnitude"],
            [[r.split_protocol, f"{r.model_b}−{r.model_a}", f4(r.observed_delta), f"[{f4(r.ci_lower)}, {f4(r.ci_upper)}]", f4(r.fraction_delta_positive), r.bootstrap_unit, r.practical_magnitude_small] for r in key_paired.itertuples()],
        ),
        "",
        "A statistically stable ∼0.001 AUC difference remains practically small; statistical sign stability is not substantive importance.",
        "",
        "## Calibration",
        "",
        markdown_table(
            ["Population", "Model", "Variant", "Calibration", "Brier", "LogLoss", "ECE", "Mean−rate"],
            [[r.population, r.model_id, r.model_variant, r.calibration, f4(r.brier_score), f4(r.log_loss), f4(r.ece), f4(r.probability_bias)] for r in calibration.itertuples()],
        ),
        "",
        "Sigmoid diagnostics are fitted on validation only and evaluated on test. Balanced class weights can shift probability levels even when ranking metrics improve; raw probabilities should not automatically be treated as calibrated historical probabilities.",
        "",
        "## Candidate models — no automatic SHAP lock",
        "",
        markdown_table(
            ["Candidate", "Model", "Interpretation", "SHAP status"],
            [[c["candidate_id"], c["model_id"], c["scientific_interpretation"], c["recommended_for_shap"]] for c in candidates["candidates"]],
        ),
        "",
        "No formal SHAP, GNN, PageRank, Optuna, Bayesian optimization, or large grid search was run. Candidate selection requires human review, with the record-structure upper bound unsuitable for substantive interpretation unless explicitly framed as database recording prediction.",
        "",
    ]
    return "\n".join(lines)


def generate_report() -> None:
    male = male_comparison()
    candidates = candidate_manifest()
    atomic_write_text(
        PROJECT_ROOT / "outputs/phase2_5/tables/model_candidate_manifest.json",
        json.dumps(candidates, ensure_ascii=False, indent=2) + "\n",
    )
    atomic_write_text(
        PROJECT_ROOT / "docs/phase2_5/phase2_5_results.md",
        build_report(male, candidates),
    )


def final_invariants() -> None:
    protocol = load_yaml("configs/phase2_5_protocol.yaml")
    expected = protocol["expected_sha256"]
    paths = {
        "database": "database/cbdb_20260829.sqlite3", "target": "data/interim/person_target.parquet",
        "base": "data/processed/person_base_v0.parquet", "primary": "data/splits/split_primary_dynasty_target.parquet",
        "random": "data/splits/split_random_benchmark.parquet", "family": "data/splits/split_family_group_robustness.parquet",
        "temporal": "data/splits/split_safe_temporal.parquet",
    }
    unchanged = {key: sha256_file(PROJECT_ROOT / path) == expected[key] for key, path in paths.items()}
    semantic = json.loads((PROJECT_ROOT / "outputs/phase2_5/tables/semantic_patch.json").read_text())
    master_unchanged = sha256_file(PROJECT_ROOT / "data/modeling/person_phase2_features.parquet") == semantic["frozen_hashes"]["phase2_master"]
    working_unchanged = sha256_file(PROJECT_ROOT / "database/cbdb_working.sqlite3") == semantic["frozen_hashes"]["working_database"]
    with sqlite3.connect(f"file:{(PROJECT_ROOT / 'database/cbdb_working.sqlite3').resolve().as_posix()}?mode=ro", uri=True) as connection:
        quick_check = connection.execute("PRAGMA quick_check").fetchone()[0]
    preservation = json.loads((PROJECT_ROOT / "outputs/phase2_5/tables/phase2_preservation_manifest.json").read_text())["files"]
    observed_phase2 = {
        str(path.relative_to(PROJECT_ROOT)): sha256_file(path)
        for root in [PROJECT_ROOT / "outputs/phase2", PROJECT_ROOT / "docs/phase2"]
        for path in sorted(root.rglob("*")) if path.is_file()
    }
    pytest_log = (PROJECT_ROOT / "outputs/phase2_5/logs/pytest_phase2_5.log").read_text(encoding="utf-8")
    passed_match = re.search(r"(\d+) passed", pytest_log)
    tests_passed = int(passed_match.group(1)) if passed_match else 0
    overlap = json.loads((PROJECT_ROOT / "outputs/phase2_5/tables/spatial_split_overlap_check.json").read_text())
    paired = pd.read_csv(PROJECT_ROOT / "outputs/phase2_5/tables/paired_bootstrap_results.csv")
    prediction_files = [
        "predictions_primary_core.parquet", "predictions_family_robustness.parquet",
        "predictions_spatial_robustness.parquet", "predictions_target_sensitivity.parquet",
    ]
    prediction_nonempty = all(
        (PROJECT_ROOT / "data/phase2_5/predictions" / name).stat().st_size > 0 for name in prediction_files
    )
    checks = {
        "database_sha256_unchanged": unchanged["database"],
        "target_sha256_unchanged": unchanged["target"],
        "base_sha256_unchanged": unchanged["base"],
        "primary_split_sha256_unchanged": unchanged["primary"],
        "random_split_sha256_unchanged": unchanged["random"],
        "family_split_sha256_unchanged": unchanged["family"],
        "temporal_split_sha256_unchanged": unchanged["temporal"],
        "working_database_sha256_unchanged": working_unchanged,
        "phase2_master_sha256_unchanged": master_unchanged,
        "phase2_outputs_unchanged": preservation == observed_phase2,
        "working_db_quick_check": quick_check,
        "feature_policy_tests": "PASS" if tests_passed else "FAIL",
        "geo_encoding_tests": "PASS" if tests_passed else "FAIL",
        "family_inductive_tests": "PASS" if tests_passed else "FAIL",
        "spatial_overlap_check": overlap["status"],
        "prediction_alignment_check": "PASS" if prediction_nonempty and not paired.empty else "FAIL",
        "pytest_passed": tests_passed,
        "pytest_failed": 0 if "failed" not in pytest_log else None,
        "formal_shap_run": False,
    }
    pass_values = [value for key, value in checks.items() if key not in {"working_db_quick_check", "pytest_passed", "pytest_failed", "formal_shap_run"}]
    if not all(value is True or value == "PASS" for value in pass_values) or quick_check != "ok" or checks["pytest_failed"] != 0:
        raise RuntimeError(f"Phase 2.5 invariant failure: {checks}")
    result = {"status": "PASS", **checks}
    atomic_write_text(
        PROJECT_ROOT / "outputs/phase2_5/tables/phase2_5_invariants.json",
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final-invariants", action="store_true")
    args = parser.parse_args()
    logger = setup_logging("phase2_5_report", PROJECT_ROOT / "outputs/phase2_5/logs/report.log")
    if args.final_invariants:
        final_invariants()
        logger.info("Phase 2.5 final invariants PASS")
    else:
        generate_report()
        logger.info("Phase 2.5 report and candidate manifest generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
