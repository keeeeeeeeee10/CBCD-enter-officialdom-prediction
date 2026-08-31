#!/usr/bin/env python3
"""Audit ENTRY timing, association timing, and candidate pre-entry anchors."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import configured_path, load_config
from src.db import connect_readonly
from src.phase15 import MAJOR_DYNASTIES, clean_year_series, year_predicate
from src.utils import atomic_write_text, markdown_table, setup_logging


def availability_row(group_type: str, group_name: str, frame: pd.DataFrame) -> dict[str, object]:
    n_people = int(frame["person_id"].nunique())
    valid_people = int(frame.loc[frame["has_valid_entry_year"].eq(1), "person_id"].nunique())
    return {
        "group_type": group_type,
        "group_name": group_name,
        "n_entry_positive_people": n_people,
        "n_with_valid_entry_year": valid_people,
        "valid_entry_year_rate": valid_people / n_people if n_people else 0.0,
        "n_entry_records": int(frame["n_entry_records"].sum()) if "n_entry_records" in frame else pd.NA,
        "n_valid_entry_year_records": int(frame["n_valid_entry_year_records"].sum()) if "n_valid_entry_year_records" in frame else pd.NA,
    }


def main() -> int:
    config = load_config()
    tables_dir = configured_path(config, "paths", "tables")
    interim_dir = configured_path(config, "paths", "interim")
    audit_dir = configured_path(config, "paths", "audit_docs")
    logger = setup_logging("temporal", configured_path(config, "paths", "logs") / "temporal_anchor_audit.log")
    database = configured_path(config, "database", "working_db")
    valid_entry = year_predicate("e.c_year", config)
    valid_assoc_first = year_predicate("a.c_assoc_first_year", config)
    valid_assoc_last = year_predicate("a.c_assoc_last_year", config)

    with connect_readonly(database, config["database"]["busy_timeout_ms"]) as connection:
        timing = pd.read_sql_query(
            f"""
            SELECT e.c_personid AS person_id,
                   COUNT(*) AS n_entry_records,
                   MIN(CASE WHEN {valid_entry} THEN e.c_year END) AS earliest_entry_year,
                   MAX(CASE WHEN {valid_entry} THEN e.c_year END) AS latest_entry_year,
                   COUNT(DISTINCT CASE WHEN {valid_entry} THEN e.c_year END) AS n_valid_entry_years,
                   SUM(CASE WHEN {valid_entry} THEN 1 ELSE 0 END) AS n_valid_entry_year_records,
                   MAX(CASE WHEN {valid_entry} THEN 1 ELSE 0 END) AS has_valid_entry_year,
                   b.c_dy AS dynasty_code, d.c_dynasty AS dynasty
            FROM ENTRY_DATA e
            INNER JOIN BIOG_MAIN b ON b.c_personid=e.c_personid
            LEFT JOIN DYNASTIES d ON d.c_dy=b.c_dy
            WHERE e.c_personid IS NOT NULL AND e.c_personid<>0
            GROUP BY e.c_personid,b.c_dy,d.c_dynasty
            ORDER BY e.c_personid
            """,
            connection,
        )
        entry_rows = pd.read_sql_query(
            f"""
            SELECT e.c_personid AS person_id, e.c_entry_code AS entry_code,
                   CASE WHEN {valid_entry} THEN 1 ELSE 0 END AS valid_year_record
            FROM ENTRY_DATA e WHERE e.c_personid IS NOT NULL AND e.c_personid<>0
            """,
            connection,
        )
        association = pd.read_sql_query(
            f"""
            WITH edges AS (
                SELECT a.c_personid, d.c_dynasty AS dynasty,
                       CASE WHEN {valid_assoc_first} THEN 1 ELSE 0 END AS valid_first,
                       CASE WHEN {valid_assoc_last} THEN 1 ELSE 0 END AS valid_last
                FROM ASSOC_DATA a
                LEFT JOIN BIOG_MAIN b ON b.c_personid=a.c_personid
                LEFT JOIN DYNASTIES d ON d.c_dy=b.c_dy
                WHERE a.c_personid IS NOT NULL AND a.c_personid<>0
            )
            SELECT 'all' AS group_type, 'Global' AS group_name,
                   COUNT(*) AS n_assoc_edges,
                   SUM(valid_first) AS valid_first_year_edges,
                   SUM(valid_last) AS valid_last_year_edges,
                   SUM(CASE WHEN valid_first=1 OR valid_last=1 THEN 1 ELSE 0 END) AS any_valid_year_edges,
                   SUM(CASE WHEN valid_first=0 AND valid_last=0 THEN 1 ELSE 0 END) AS invalid_or_missing_year_edges,
                   COUNT(DISTINCT c_personid) AS people_with_assoc,
                   COUNT(DISTINCT CASE WHEN valid_first=1 OR valid_last=1 THEN c_personid END) AS people_with_valid_year_assoc
            FROM edges
            UNION ALL
            SELECT 'dynasty', dynasty, COUNT(*), SUM(valid_first), SUM(valid_last),
                   SUM(CASE WHEN valid_first=1 OR valid_last=1 THEN 1 ELSE 0 END),
                   SUM(CASE WHEN valid_first=0 AND valid_last=0 THEN 1 ELSE 0 END),
                   COUNT(DISTINCT c_personid),
                   COUNT(DISTINCT CASE WHEN valid_first=1 OR valid_last=1 THEN c_personid END)
            FROM edges WHERE dynasty IN ('Tang','Song','Yuan','Ming','Qing') GROUP BY dynasty
            """,
            connection,
        )

    for column in ("n_entry_records", "n_valid_entry_years", "n_valid_entry_year_records"):
        timing[column] = timing[column].astype("int32")
    timing["has_valid_entry_year"] = timing["has_valid_entry_year"].astype("int8")
    timing_output = timing[[
        "person_id", "earliest_entry_year", "latest_entry_year", "n_valid_entry_years",
        "n_valid_entry_year_records", "has_valid_entry_year", "n_entry_records",
    ]]
    timing_output.to_parquet(interim_dir / "person_entry_timing.parquet", index=False, compression="zstd")

    availability_rows = [availability_row("all", "Global", timing)]
    for dynasty in MAJOR_DYNASTIES:
        availability_rows.append(availability_row("dynasty", dynasty, timing[timing["dynasty"].eq(dynasty)]))
    taxonomy = pd.read_csv(tables_dir / "target_v2_candidate_codes.csv")
    categorized = entry_rows.merge(taxonomy[["entry_code", "semantic_category"]], on="entry_code", how="left")
    category_people = categorized.groupby(["semantic_category", "person_id"], dropna=False).agg(
        has_valid_entry_year=("valid_year_record", "max"),
        n_entry_records=("entry_code", "size"),
        n_valid_entry_year_records=("valid_year_record", "sum"),
    ).reset_index()
    for category, frame in category_people.groupby("semantic_category", dropna=False):
        availability_rows.append(availability_row("semantic_category", str(category), frame))
    availability = pd.DataFrame(availability_rows)
    availability.to_csv(tables_dir / "entry_year_availability.csv", index=False)

    association["any_valid_year_edge_rate"] = association["any_valid_year_edges"] / association["n_assoc_edges"]
    association["people_valid_year_rate"] = association["people_with_valid_year_assoc"] / association["people_with_assoc"]
    association.to_csv(tables_dir / "association_temporal_coverage.csv", index=False)

    safe_time = pd.read_parquet(interim_dir / "person_safe_time_anchor.parquet")
    positive_anchor = safe_time[safe_time["target_entry_v1"].eq(1)].merge(timing_output, on="person_id", how="left", validate="one_to_one")
    positive_anchor["valid_birth_year"] = clean_year_series(positive_anchor["birth_year"], config)
    age_known = positive_anchor["valid_birth_year"].notna() & positive_anchor["earliest_entry_year"].notna()
    entry_age = positive_anchor.loc[age_known, "earliest_entry_year"] - positive_anchor.loc[age_known, "valid_birth_year"]
    global_time = pd.read_csv(tables_dir / "time_anchor_coverage.csv")
    global_row = global_time[(global_time["group_type"] == "all") & (global_time["group_name"] == "Global")].iloc[0]
    global_entry = availability[(availability["group_type"] == "all") & (availability["group_name"] == "Global")].iloc[0]
    assoc_global = association[(association["group_type"] == "all") & (association["group_name"] == "Global")].iloc[0]

    document = [
        "# Temporal anchor audit",
        "",
        "Phase 1.5 does not force a single precise risk year. Raw fields remain unchanged; year sentinels and implausible values are converted to missing only in derived audit fields.",
        "",
        "## Observed coverage",
        "",
        markdown_table(
            ["candidate", "people", "coverage"],
            [
                ["valid birth year", int(global_row.birth_year_valid), f"{global_row.birth_year_valid_rate:.2%}"],
                ["valid raw index year", int(global_row.index_year_valid), f"{global_row.index_year_valid_rate:.2%}"],
                ["SAFE index-year provenance", int(global_row.safe_index_year_valid), f"{global_row.safe_index_year_valid_rate:.2%}"],
                ["ENTRY positives with valid entry year", int(global_entry.n_with_valid_entry_year), f"{global_entry.valid_entry_year_rate:.2%}"],
            ],
        ),
        "",
        "## Anchor A — birth year + fixed age",
        "",
        f"Birth-year coverage is {global_row.birth_year_valid_rate:.2%}. Among {int(age_known.sum()):,} ENTRY-positive people with both a valid birth and earliest entry year, median recorded entry age is {entry_age.median():.1f}; {entry_age.lt(25).mean():.2%} enter before age 25 and {entry_age.lt(30).mean():.2%} before age 30. A +25/+30 landmark is genuinely background-based but changes the estimand and loses most people; it cannot be treated as each person's true entry-risk date.",
        "",
        "## Anchor B — safe index year + offset",
        "",
        f"SAFE index-year coverage is only {global_row.safe_index_year_valid_rate:.2%}. The only SAFE provenance is code `01`, based directly on birth year, so `safe_index_year + 20` is effectively another birth-cohort landmark rather than independent timing information. It is suitable only for sensitivity subsets, not as a universal anchor.",
        "",
        "## Anchor C — earliest ENTRY year plus matched pseudo-risk year",
        "",
        f"A valid earliest entry year is available for {global_entry.valid_entry_year_rate:.2%} of ENTRY positives. Matching negatives by dynasty, safe cohort and age can support a matched case-control analysis, but pseudo-risk assignment must occur inside training folds and preserve matching groups. It does not create a natural event time for all negatives.",
        "",
        "## Recommendation",
        "",
        "Use dynasty/cohort baselines on the safe-anchor subset and report the global cross-sectional record-prediction task separately. Anchor A and matched Anchor C should be parallel sensitivity designs. Current coverage does not justify manufacturing one universal pre-entry year.",
        "",
        "## Association timing",
        "",
        f"Only {int(assoc_global.any_valid_year_edges):,} of {int(assoc_global.n_assoc_edges):,} association rows ({assoc_global.any_valid_year_edge_rate:.2%}) contain a valid first or last year, covering {int(assoc_global.people_with_valid_year_assoc):,} people. Undated edges are not treated as pre-entry; network work remains a subset analysis without PageRank/GNN in this phase.",
        "",
    ]
    atomic_write_text(audit_dir / "temporal_anchor_audit.md", "\n".join(document))
    logger.info("Temporal audit complete: ENTRY positives=%d valid year=%d association valid edges=%d", len(timing), int(timing["has_valid_entry_year"].sum()), int(assoc_global.any_valid_year_edges))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

