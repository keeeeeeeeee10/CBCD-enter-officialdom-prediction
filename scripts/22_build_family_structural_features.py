#!/usr/bin/env python3
"""Build family structure features without any relative career outcome."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.cleaning import clean_person_identifier
from src.config import load_config
from src.db import connect_readonly
from src.feature_builders import atomic_to_parquet, ensure_unique_people
from src.utils import setup_logging


SPECIFIC_RELATIONS = [
    "father", "mother", "paternal_grandfather", "paternal_grandmother",
    "maternal_grandfather", "maternal_grandmother",
]


def main() -> int:
    logger = setup_logging("phase2_family_structure", PROJECT_ROOT / "outputs/logs/phase2_family_structure.log")
    config = load_config()
    population = pd.read_parquet(
        PROJECT_ROOT / "data/interim/person_modeling_population.parquet", columns=["person_id"]
    )
    known_people = set(population["person_id"].astype("int64"))
    taxonomy = pd.read_csv(PROJECT_ROOT / "outputs/tables/kinship_generation_taxonomy.csv")[[
        "kin_code", "generation_class", "specific_relation", "is_blood_core", "is_affinal"
    ]]
    database = PROJECT_ROOT / config["database"]["working_db"]
    with connect_readonly(database, config["database"]["busy_timeout_ms"]) as connection:
        relations = pd.read_sql_query(
            "SELECT c_personid AS person_id, c_kin_id AS kin_id, c_kin_code AS kin_code FROM KIN_DATA",
            connection,
        )
    relations["person_id"] = clean_person_identifier(relations["person_id"])
    relations["kin_id"] = clean_person_identifier(relations["kin_id"])
    relations = relations.dropna(subset=["person_id", "kin_id"]).copy()
    relations[["person_id", "kin_id"]] = relations[["person_id", "kin_id"]].astype("int64")
    relations = relations[
        relations["person_id"].isin(known_people)
        & relations["kin_id"].isin(known_people)
        & relations["person_id"].ne(relations["kin_id"])
    ].merge(taxonomy, on="kin_code", how="left", validate="many_to_one")
    relations = relations.sort_values(
        ["person_id", "kin_id", "is_blood_core", "is_affinal", "kin_code"],
        ascending=[True, True, False, True, True], kind="mergesort",
    ).drop_duplicates(["person_id", "kin_id"], keep="first")

    structural = population.copy()
    for relation in SPECIFIC_RELATIONS:
        identified = relations.loc[relations["specific_relation"].eq(relation)].groupby("person_id")["kin_id"].nunique()
        structural[f"{relation}_identified"] = structural["person_id"].map(identified).fillna(0).gt(0).astype("int8")
    parent_count = relations.loc[relations["specific_relation"].isin(["father", "mother"])].groupby("person_id")["kin_id"].nunique()
    grandparent_count = relations.loc[relations["specific_relation"].isin(SPECIFIC_RELATIONS[2:])].groupby("person_id")["kin_id"].nunique()
    structural["n_known_parents"] = structural["person_id"].map(parent_count).fillna(0).astype("int32")
    structural["n_known_grandparents"] = structural["person_id"].map(grandparent_count).fillna(0).astype("int32")
    for generation, column in (
        ("ancestor", "n_known_ancestors"),
        ("parent_generation", "n_known_parent_generation"),
        ("same_generation", "n_known_same_generation"),
        ("descendant", "n_known_descendants"),
    ):
        counts = relations.loc[relations["generation_class"].eq(generation)].groupby("person_id")["kin_id"].nunique()
        structural[column] = structural["person_id"].map(counts).fillna(0).astype("int32")

    canonical = pd.read_parquet(
        PROJECT_ROOT / "data/interim/family_edges_core.parquet",
        columns=["person_id", "kin_id", "is_blood_core"],
    )
    core = canonical.loc[canonical["is_blood_core"]]
    symmetric = pd.concat([
        core[["person_id", "kin_id"]],
        core.rename(columns={"person_id": "kin_id", "kin_id": "person_id"})[["person_id", "kin_id"]],
    ], ignore_index=True).drop_duplicates()
    core_counts = symmetric.groupby("person_id")["kin_id"].nunique()
    structural["n_known_core_kin"] = structural["person_id"].map(core_counts).fillna(0).astype("int32")
    groups = pd.read_parquet(PROJECT_ROOT / "data/interim/person_family_groups.parquet")
    structural = structural.merge(groups, on="person_id", how="left", validate="one_to_one")
    structural["family_group_size"] = structural["family_group_size"].astype("int32")
    structural["has_core_family"] = structural["has_core_family"].astype("int8")
    structural = structural.sort_values("person_id").reset_index(drop=True)
    ensure_unique_people(structural)
    atomic_to_parquet(structural, PROJECT_ROOT / "data/features/family_structural_features.parquet")
    logger.info(
        "Family structural features complete: father=%.2f%% paternal_grandfather=%.2f%% core_family=%.2f%%",
        100 * structural["father_identified"].mean(),
        100 * structural["paternal_grandfather_identified"].mean(),
        100 * structural["has_core_family"].mean(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
