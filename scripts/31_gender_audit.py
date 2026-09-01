#!/usr/bin/env python3
"""Audit the actual CBDB gender field and decompose the personal signal."""

from __future__ import annotations

import json
import os
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

from src.feature_builders import atomic_to_csv
from src.phase25 import load_phase25_dataset, metric_deltas, run_fixed_model, save_analysis_outputs
from src.utils import atomic_write_text, setup_logging


def atomic_savefig(figure: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.stem + ".tmp" + path.suffix)
    figure.savefig(temporary, dpi=300, bbox_inches="tight")
    os.replace(temporary, path)
    plt.close(figure)


def gender_code_audit(dataset: pd.DataFrame) -> dict[str, object]:
    database = PROJECT_ROOT / "database/cbdb_working.sqlite3"
    with sqlite3.connect(f"file:{database.resolve().as_posix()}?mode=ro", uri=True) as connection:
        observed = pd.read_sql_query(
            "SELECT c_female AS code, COUNT(*) AS n_people FROM BIOG_MAIN GROUP BY c_female ORDER BY c_female",
            connection,
        )
        code_tables = pd.read_sql_query(
            "SELECT name, sql FROM sqlite_master WHERE type='table' AND (lower(name) LIKE '%gender%' OR lower(name) LIKE '%sex%' OR lower(name) LIKE '%female%')",
            connection,
        )
    base = pd.read_parquet(PROJECT_ROOT / "data/processed/person_base_v0.parquet", columns=["person_id", "gender_code", "gender"])
    mapping = base.drop_duplicates(["gender_code", "gender"])[["gender_code", "gender"]].sort_values("gender_code", na_position="last")
    expected = {0: "male", 1: "female"}
    for code, label in expected.items():
        labels = set(mapping.loc[mapping["gender_code"].eq(code), "gender"])
        if labels != {label}:
            raise RuntimeError(f"Frozen ETL gender mapping failed for c_female={code}: {labels}")
    if set(dataset["gender"].dropna().unique()) != {"male", "female", "unknown"}:
        raise RuntimeError("Unexpected modeled gender labels")
    return {
        "status": "PASS",
        "source_field": "BIOG_MAIN.c_female",
        "dedicated_code_table_found": not code_tables.empty,
        "dedicated_code_tables": code_tables["name"].tolist(),
        "observed_database_codes": observed.where(pd.notna(observed), None).to_dict(orient="records"),
        "verified_mapping": {"0": "male", "1": "female", "NULL": "unknown"},
        "evidence": "Actual working-database distinct values plus frozen Phase 1 ETL/schema definition; no standalone gender code table exists.",
    }


def summary_table(dataset: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for population in ["Global", "Song", "Ming", "Qing"]:
        subset = dataset if population == "Global" else dataset.loc[dataset["dynasty_name"].eq(population)]
        for gender, group in subset.groupby("gender", dropna=False):
            rows.append({
                "population": population,
                "gender": str(gender),
                "n_people": len(group),
                "n_positive": int(group["target_entry_v1"].sum()),
                "positive_rate": float(group["target_entry_v1"].mean()),
                "geography_coverage": float(group["has_geography"].mean()),
                "kin_coverage": float(group["has_kin"].mean()),
                "documentation_intensity_mean": float(group["documentation_intensity"].mean()),
            })
    return pd.DataFrame(rows)


def plot_gender(summary: pd.DataFrame, path: Path) -> None:
    populations = ["Global", "Song", "Ming", "Qing"]
    genders = ["male", "female", "unknown"]
    colors = ["#4c78a8", "#e45756", "#9d9d9d"]
    x = np.arange(len(populations))
    width = 0.24
    figure, axis = plt.subplots(figsize=(9, 4.5))
    for index, (gender, color) in enumerate(zip(genders, colors, strict=True)):
        values = [float(summary.loc[
            summary["population"].eq(population) & summary["gender"].eq(gender), "positive_rate"
        ].iloc[0]) for population in populations]
        axis.bar(x + (index - 1) * width, values, width, label=gender, color=color)
    axis.set_xticks(x, populations)
    axis.set_ylabel("V1 ENTRY-record positive rate")
    axis.set_title("Recorded ENTRY target by verified CBDB gender code")
    axis.legend(frameon=False)
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    atomic_savefig(figure, path)


def plot_personal(metrics: pd.DataFrame, path: Path) -> None:
    models = ["P0", "P1", "P2", "P3"]
    figure, axis = plt.subplots(figsize=(7.5, 4.5))
    for population, color in zip(["Global", "Song", "Ming"], ["#4c78a8", "#f58518", "#54a24b"], strict=True):
        values = metrics.loc[metrics["population"].eq(population)].set_index("model_id").reindex(models)
        axis.plot(models, values["roc_auc"], marker="o", linewidth=2, label=population, color=color)
    axis.set_xlabel("Personal decomposition")
    axis.set_ylabel("ROC-AUC")
    axis.set_title("Gender, SAFE cohort, and birth-year observability")
    axis.grid(axis="y", alpha=0.25)
    axis.legend(frameon=False)
    figure.tight_layout()
    atomic_savefig(figure, path)


def main() -> int:
    logger = setup_logging("phase2_5_gender", PROJECT_ROOT / "outputs/phase2_5/logs/gender_audit.log")
    dataset = load_phase25_dataset()
    audit = gender_code_audit(dataset)
    atomic_write_text(
        PROJECT_ROOT / "outputs/phase2_5/tables/gender_code_audit.json",
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
    )
    summary = summary_table(dataset)
    atomic_to_csv(summary, PROJECT_ROOT / "outputs/phase2_5/tables/gender_target_summary.csv")
    figures = PROJECT_ROOT / "outputs/phase2_5/figures"
    plot_gender(summary, figures / "entry_rate_by_gender_population.png")

    metrics, tests, validations, metadata = [], [], [], []
    for population in ["Global", "Song", "Ming"]:
        for model_id in ["P0", "P1", "P2", "P3"]:
            run = run_fixed_model(dataset, population, model_id, "CatBoost")
            metrics.append(run.metric)
            tests.append(run.test_predictions)
            validations.append(run.validation_predictions)
            metadata.append(run.feature_metadata)
            logger.info("Personal %s/%s AUC=%.4f", population, model_id, run.metric["roc_auc"])
    personal = pd.DataFrame(metrics)
    deltas = metric_deltas(personal, ["P0", "P1", "P2", "P3"], ["algorithm", "population", "target_name", "split_protocol", "subset"])
    atomic_to_csv(deltas, PROJECT_ROOT / "outputs/phase2_5/tables/personal_decomposition_deltas.csv")
    plot_personal(personal, figures / "personal_gender_decomposition.png")
    save_analysis_outputs("personal_decomposition_results", metrics, tests, validations, metadata)

    male_metrics, male_tests, male_validations, male_metadata = [], [], [], []
    for population in ["Song", "Ming"]:
        for model_id in ["P1", "G4", "G5", "F2", "F3", "D0", "D6"]:
            run = run_fixed_model(dataset, population, model_id, "CatBoost", subset="verified_male")
            male_metrics.append(run.metric)
            male_tests.append(run.test_predictions)
            male_validations.append(run.validation_predictions)
            male_metadata.append(run.feature_metadata)
            logger.info("Male-only %s/%s AUC=%.4f", population, model_id, run.metric["roc_auc"])
    atomic_to_csv(pd.DataFrame(male_metrics), PROJECT_ROOT / "outputs/phase2_5/tables/male_only_results.csv")
    save_analysis_outputs("male_only_models", male_metrics, male_tests, male_validations, male_metadata)
    logger.info("Gender audit and personal/male-only models complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
