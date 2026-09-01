#!/usr/bin/env python3
"""Generate descriptive, non-causal final data-analysis tables."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import atomic_to_csv, load_yaml, population_mask
from src.phase26 import load_phase26_dataset
from src.utils import setup_logging


CATEGORIES = [
    "exam_degree", "school_or_student_status", "recommendation",
    "hereditary_or_yin_privilege", "military_entry", "purchase_or_donation",
    "direct_appointment", "other_clear_entry", "failed_entry", "ambiguous", "unknown",
]


def complete_categories(frame: pd.DataFrame, dynasties: list[str], value_columns: list[str]) -> pd.DataFrame:
    index = pd.MultiIndex.from_product([dynasties, CATEGORIES], names=["dynasty", "semantic_category"])
    return frame.set_index(["dynasty", "semantic_category"]).reindex(index, fill_value=0).reset_index()[
        ["dynasty", "semantic_category", *value_columns]
    ]


def main() -> int:
    logger = setup_logging("phase2_6_descriptive", PROJECT_ROOT / "outputs/phase2_6/logs/final_descriptive.log")
    reporting = load_yaml("configs/phase2_6_reporting.yaml")
    major = [str(value) for value in reporting["major_dynasties"]]
    dataset = load_phase26_dataset()
    tables = PROJECT_ROOT / "outputs/phase2_6/tables"

    dynasty = dataset.groupby(["dynasty_code", "dynasty_name"], dropna=False).agg(
        n_people=("person_id", "size"), n_entry_positive=("target_entry_v1", "sum")
    ).reset_index()
    dynasty["entry_record_presence_rate"] = dynasty["n_entry_positive"] / dynasty["n_people"]
    dynasty["rate_semantics"] = "share of CBDB-listed people with an ENTRY_DATA record"
    dynasty = dynasty.sort_values("n_people", ascending=False)
    atomic_to_csv(dynasty, tables / "final_population_target_context.csv")

    gender_rows = []
    for population in ["Global", "Song", "Ming", "Qing"]:
        block = dataset.loc[population_mask(dataset, population)]
        for gender, group in block.groupby("gender", dropna=False, sort=True):
            gender_rows.append({
                "population": population,
                "gender": gender,
                "n_people": len(group),
                "n_entry_positive": int(group["target_entry_v1"].sum()),
                "entry_record_presence_rate": float(group["target_entry_v1"].mean()),
                "population_share": float(len(group) / len(block)),
                "rate_semantics": "share of CBDB-listed people with an ENTRY_DATA record",
            })
    atomic_to_csv(pd.DataFrame(gender_rows), tables / "final_gender_entry_rates.csv")

    taxonomy = pd.read_csv(PROJECT_ROOT / "outputs/tables/target_v2_candidate_codes.csv")[[
        "entry_code", "semantic_category"
    ]]
    database = PROJECT_ROOT / "database/cbdb_working.sqlite3"
    with sqlite3.connect(f"file:{database.resolve().as_posix()}?mode=ro", uri=True) as connection:
        records = pd.read_sql_query(
            """
            SELECT e.c_personid AS person_id, e.c_entry_code AS entry_code,
                   d.c_dynasty AS dynasty
            FROM ENTRY_DATA e
            JOIN BIOG_MAIN b ON b.c_personid=e.c_personid
            LEFT JOIN DYNASTIES d ON d.c_dy=b.c_dy
            WHERE e.c_personid IS NOT NULL AND e.c_personid<>0
            """,
            connection,
        )
    records = records.merge(taxonomy, on="entry_code", how="left", validate="many_to_one")
    records["semantic_category"] = records["semantic_category"].fillna("unknown")
    records = records.loc[records["dynasty"].isin(major)].copy()
    record_table = records.groupby(["dynasty", "semantic_category"]).size().rename("n_records").reset_index()
    record_table = complete_categories(record_table, major, ["n_records"])
    record_table["dynasty_entry_records"] = record_table.groupby("dynasty")["n_records"].transform("sum")
    record_table["record_category_share"] = np.where(
        record_table["dynasty_entry_records"].gt(0),
        record_table["n_records"] / record_table["dynasty_entry_records"], np.nan,
    )
    atomic_to_csv(record_table, tables / "entry_category_by_dynasty_records.csv")

    unique = records[["person_id", "dynasty", "semantic_category"]].drop_duplicates()
    people_table = unique.groupby(["dynasty", "semantic_category"]).size().rename("n_people_with_category").reset_index()
    people_table = complete_categories(people_table, major, ["n_people_with_category"])
    all_denominator = dataset.loc[dataset["dynasty_name"].isin(major)].groupby("dynasty_name").size().to_dict()
    entry_denominator = dataset.loc[
        dataset["dynasty_name"].isin(major) & dataset["target_entry_v1"].eq(1)
    ].groupby("dynasty_name").size().to_dict()
    people_table["all_cbdb_people_in_dynasty"] = people_table["dynasty"].map(all_denominator).fillna(0).astype(int)
    people_table["entry_positive_people_in_dynasty"] = people_table["dynasty"].map(entry_denominator).fillna(0).astype(int)
    people_table["prevalence_among_all_cbdb_people"] = people_table["n_people_with_category"] / people_table["all_cbdb_people_in_dynasty"].replace(0, np.nan)
    people_table["prevalence_among_entry_positive_people"] = people_table["n_people_with_category"] / people_table["entry_positive_people_in_dynasty"].replace(0, np.nan)
    people_table["nonexclusive_categories"] = True
    atomic_to_csv(people_table, tables / "entry_category_by_dynasty_people.csv")

    coverage_features = [
        "has_safe_birth_year", "has_geography", "has_valid_coordinates", "has_address",
        "has_kin", "has_core_family", "father_identified", "mother_identified",
        "paternal_grandfather_identified", "maternal_grandfather_identified",
        "has_assoc", "has_status", "has_text", "has_institution", "documentation_intensity",
    ]
    coverage_rows = []
    for population in ["Global", "Song", "Ming", "Qing"]:
        block = dataset.loc[population_mask(dataset, population)]
        for feature in coverage_features:
            values = pd.to_numeric(block[feature], errors="coerce")
            binary = set(values.dropna().unique()).issubset({0, 1})
            coverage_rows.append({
                "population": population,
                "feature": feature,
                "n_people": len(block),
                "non_missing_n": int(values.notna().sum()),
                "non_missing_rate": float(values.notna().mean()),
                "positive_flag_n": int(values.eq(1).sum()) if binary else np.nan,
                "positive_flag_rate": float(values.eq(1).mean()) if binary else np.nan,
                "mean": float(values.mean()),
                "median": float(values.median()),
                "is_binary_flag": binary,
            })
    atomic_to_csv(pd.DataFrame(coverage_rows), tables / "final_feature_coverage.csv")

    documentation = []
    for population in ["Global", "Song", "Ming", "Qing"]:
        block = dataset.loc[population_mask(dataset, population)]
        for intensity, group in block.groupby("documentation_intensity", sort=True):
            documentation.append({
                "population": population,
                "documentation_intensity": int(intensity),
                "n_people": len(group),
                "entry_record_presence_rate": float(group["target_entry_v1"].mean()),
            })
    atomic_to_csv(pd.DataFrame(documentation), tables / "documentation_intensity_descriptive.csv")
    logger.info("Final descriptive tables complete: ENTRY records=%d categorized people=%d", len(records), unique["person_id"].nunique())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
