#!/usr/bin/env python3
"""Build cross-sectional and pre-birth lineage political-capital features."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.cleaning import clean_person_identifier, valid_historical_year_sql
from src.config import load_config
from src.db import connect_readonly
from src.feature_builders import atomic_to_csv, atomic_to_parquet, ensure_unique_people
from src.utils import setup_logging


DIRECT_RELATIONS = ["father", "mother", "paternal_grandfather", "maternal_grandfather"]
PREBIRTH_DIRECT = ["father", "paternal_grandfather", "maternal_grandfather"]


def direct_lifetime_features(
    people: pd.DataFrame,
    relations: pd.DataFrame,
    outcomes: pd.DataFrame,
) -> pd.DataFrame:
    linked = relations.merge(
        outcomes.rename(columns={"person_id": "kin_id", "target_entry_v1": "kin_entry", "target_posting": "kin_posting"}),
        on="kin_id", how="left", validate="many_to_one",
    )
    output = people[["person_id"]].copy()
    for relation in DIRECT_RELATIONS:
        subset = linked.loc[linked["specific_relation"].eq(relation)]
        entry = subset.groupby("person_id")["kin_entry"].max()
        posting = subset.groupby("person_id")["kin_posting"].max()
        output[f"{relation}_ever_entry"] = output["person_id"].map(entry).astype("Float64")
        output[f"{relation}_ever_posting"] = output["person_id"].map(posting).astype("Float64")
    return output


def prebirth_direct_features(
    base: pd.DataFrame,
    relations: pd.DataFrame,
    events: pd.DataFrame,
) -> pd.DataFrame:
    linked = relations.merge(events.rename(columns={"person_id": "kin_id"}), on="kin_id", how="left", validate="many_to_one")
    linked = linked.merge(base[["person_id", "safe_birth_year"]], on="person_id", how="left", validate="many_to_one")
    output = base[["person_id"]].copy()
    for relation in PREBIRTH_DIRECT:
        subset = linked.loc[linked["specific_relation"].eq(relation)]
        for event_type, event_column in (("entry", "earliest_entry_year"), ("posting", "earliest_posting_year")):
            evaluable = subset["safe_birth_year"].notna() & subset[event_column].notna()
            values = subset.loc[evaluable].assign(
                before=lambda frame: frame[event_column].lt(frame["safe_birth_year"]).astype(float)
            ).groupby("person_id")["before"].max()
            output[f"{relation}_{event_type}_before_birth"] = output["person_id"].map(values).astype("Float64")
    return output


def older_prebirth_features(
    base: pd.DataFrame,
    older: pd.DataFrame,
    events: pd.DataFrame,
) -> pd.DataFrame:
    linked = older.merge(events.rename(columns={"person_id": "kin_id"}), on="kin_id", how="left", validate="many_to_one")
    linked = linked.merge(base[["person_id", "safe_birth_year"]], on="person_id", how="left", validate="many_to_one")
    output = base[["person_id"]].copy()
    for event_type, event_column in (("entry", "earliest_entry_year"), ("posting", "earliest_posting_year")):
        evaluable = linked["safe_birth_year"].notna() & linked[event_column].notna()
        evaluated = linked.loc[evaluable].assign(before=lambda frame: frame[event_column].lt(frame["safe_birth_year"]).astype(int))
        count = evaluated.groupby("person_id")["before"].sum()
        any_value = evaluated.groupby("person_id")["before"].max()
        observed = evaluated.groupby("person_id")["kin_id"].nunique()
        output[f"n_older_kin_{event_type}_before_birth"] = output["person_id"].map(count).astype("Float64")
        output[f"any_older_kin_{event_type}_before_birth"] = output["person_id"].map(any_value).astype("Float64")
        output[f"n_older_kin_with_valid_{event_type}_year"] = output["person_id"].map(observed).astype("Float64")
    return output


def coverage_table(frame: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    rows = []
    populations = {"Global": pd.Series(True, index=frame.index)}
    populations.update({dynasty: frame["dynasty_name"].eq(dynasty) for dynasty in ["Song", "Ming", "Qing"]})
    for population, mask in populations.items():
        subset = frame.loc[mask]
        for feature in features:
            values = pd.to_numeric(subset[feature], errors="coerce")
            rows.append({
                "feature": feature,
                "population": population,
                "n_people": len(subset),
                "n_non_missing": int(values.notna().sum()),
                "coverage": float(values.notna().mean()),
                "positive_mean": float(values.loc[subset["target_entry_v1"].eq(1)].mean()) if values.loc[subset["target_entry_v1"].eq(1)].notna().any() else None,
                "negative_mean": float(values.loc[subset["target_entry_v1"].eq(0)].mean()) if values.loc[subset["target_entry_v1"].eq(0)].notna().any() else None,
            })
    return pd.DataFrame(rows)


def main() -> int:
    logger = setup_logging("phase2_family_capital", PROJECT_ROOT / "outputs/logs/phase2_family_capital.log")
    config = load_config()
    people = pd.read_parquet(PROJECT_ROOT / "data/features/personal_features.parquet")
    targets = pd.read_parquet(
        PROJECT_ROOT / "data/interim/person_auxiliary_outcomes.parquet",
        columns=["person_id", "target_entry_v1", "target_posting"],
    )
    people = people.merge(targets[["person_id", "target_entry_v1"]], on="person_id", how="left", validate="one_to_one")
    known_people = set(people["person_id"].astype("int64"))
    taxonomy = pd.read_csv(PROJECT_ROOT / "outputs/tables/kinship_generation_taxonomy.csv")[[
        "kin_code", "generation_class", "specific_relation", "is_affinal"
    ]]
    database = PROJECT_ROOT / config["database"]["working_db"]
    with connect_readonly(database, config["database"]["busy_timeout_ms"]) as connection:
        relations = pd.read_sql_query(
            "SELECT c_personid AS person_id, c_kin_id AS kin_id, c_kin_code AS kin_code FROM KIN_DATA",
            connection,
        )
        year_predicate_first = valid_historical_year_sql("c_firstyear")
        year_predicate_last = valid_historical_year_sql("c_lastyear")
        postings = pd.read_sql_query(
            f"""
            SELECT c_personid AS person_id,
                   MIN(CASE
                       WHEN {year_predicate_first} THEN c_firstyear
                       WHEN {year_predicate_last} THEN c_lastyear
                   END) AS earliest_posting_year
            FROM POSTED_TO_OFFICE_DATA
            WHERE c_personid>0
            GROUP BY c_personid
            """,
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
        ["person_id", "kin_id", "is_affinal", "kin_code"],
        ascending=[True, True, True, True], kind="mergesort",
    ).drop_duplicates(["person_id", "kin_id"], keep="first")

    direct = direct_lifetime_features(people, relations, targets)
    older = relations[
        relations["generation_class"].isin(["ancestor", "parent_generation"])
        & ~relations["is_affinal"].astype(bool)
    ].drop_duplicates(["person_id", "kin_id"])
    older_outcomes = older.merge(
        targets.rename(columns={"person_id": "kin_id", "target_entry_v1": "kin_entry", "target_posting": "kin_posting"}),
        on="kin_id", how="left", validate="many_to_one",
    )
    older_agg = older_outcomes.groupby("person_id").agg(
        n_eligible_older_kin=("kin_id", "nunique"),
        n_older_kin_ever_entry=("kin_entry", "sum"),
        n_older_kin_ever_posting=("kin_posting", "sum"),
    ).reset_index()
    older_agg["older_kin_entry_ratio"] = older_agg["n_older_kin_ever_entry"] / older_agg["n_eligible_older_kin"]
    older_agg["older_kin_posting_ratio"] = older_agg["n_older_kin_ever_posting"] / older_agg["n_eligible_older_kin"]
    older_agg["any_older_kin_ever_entry"] = older_agg["n_older_kin_ever_entry"].gt(0).astype("int8")
    older_agg["any_older_kin_ever_posting"] = older_agg["n_older_kin_ever_posting"].gt(0).astype("int8")

    timing = pd.read_parquet(
        PROJECT_ROOT / "data/interim/person_entry_timing.parquet",
        columns=["person_id", "earliest_entry_year"],
    )
    events = targets[["person_id"]].merge(timing, on="person_id", how="left", validate="one_to_one")
    events = events.merge(postings, on="person_id", how="left", validate="one_to_one")
    prebirth_direct = prebirth_direct_features(people, relations, events)
    prebirth_older = older_prebirth_features(people, older, events)

    features = direct.merge(older_agg, on="person_id", how="left", validate="one_to_one")
    features = features.merge(prebirth_direct, on="person_id", how="left", validate="one_to_one")
    features = features.merge(prebirth_older, on="person_id", how="left", validate="one_to_one")
    count_columns = ["n_eligible_older_kin", "n_older_kin_ever_entry", "n_older_kin_ever_posting"]
    for column in count_columns:
        features[column] = features[column].fillna(0).astype("int32")
    features = features.sort_values("person_id").reset_index(drop=True)
    ensure_unique_people(features)
    atomic_to_parquet(features, PROJECT_ROOT / "data/features/family_capital_features.parquet")

    audit_frame = people[["person_id", "dynasty_name", "target_entry_v1"]].merge(features, on="person_id", how="left", validate="one_to_one")
    audited_features = [column for column in features.columns if column != "person_id"]
    coverage = coverage_table(audit_frame, audited_features)
    atomic_to_csv(coverage, PROJECT_ROOT / "outputs/phase2/tables/family_feature_coverage.csv")
    logger.info(
        "Family capital complete: eligible older kin=%d; father ENTRY coverage=%.2f%%; prebirth father ENTRY coverage=%.2f%%",
        int(features["n_eligible_older_kin"].gt(0).sum()),
        100 * features["father_ever_entry"].notna().mean(),
        100 * features["father_entry_before_birth"].notna().mean(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
