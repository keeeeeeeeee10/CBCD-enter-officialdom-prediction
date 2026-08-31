#!/usr/bin/env python3
"""Create the reproducible Target V1 from ENTRY_DATA presence and audit its meaning."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import configured_path, load_config
from src.db import connect_readonly, scalar
from src.utils import atomic_write_text, markdown_table, setup_logging


TARGET_QUERY = """
WITH entry_counts AS (
    SELECT c_personid, COUNT(*) AS entry_record_count
    FROM ENTRY_DATA
    WHERE c_personid IS NOT NULL
    GROUP BY c_personid
)
SELECT
    b.c_personid AS person_id,
    CASE WHEN e.c_personid IS NULL THEN 0 ELSE 1 END AS target_entry,
    COALESCE(e.entry_record_count, 0) AS entry_record_count
FROM BIOG_MAIN AS b
LEFT JOIN entry_counts AS e ON e.c_personid=b.c_personid
ORDER BY b.c_personid
"""


def main() -> int:
    config = load_config()
    interim_dir = configured_path(config, "paths", "interim")
    tables_dir = configured_path(config, "paths", "tables")
    audit_dir = configured_path(config, "paths", "audit_docs")
    logger = setup_logging("target", configured_path(config, "paths", "logs") / "target_definition.log")
    database = configured_path(config, "database", "working_db")

    with connect_readonly(database, config["database"]["busy_timeout_ms"]) as connection:
        logger.info("Building person target with SQL aggregation")
        target = pd.read_sql_query(TARGET_QUERY, connection, dtype={"person_id": "int64", "target_entry": "int8", "entry_record_count": "int32"})
        if target["person_id"].duplicated().any():
            raise RuntimeError("Target output is not one row per person; BIOG_MAIN identifiers are duplicated")

        n_people = len(target)
        n_positive = int(target["target_entry"].sum())
        n_negative = n_people - n_positive
        summary = pd.DataFrame([{
            "N_people": n_people,
            "N_positive": n_positive,
            "N_negative": n_negative,
            "positive_rate": n_positive / n_people,
            "negative_rate": n_negative / n_people,
        }])

        dynasty = pd.read_sql_query(
            """
            WITH people AS (
                SELECT b.c_personid, b.c_dy,
                       CASE WHEN e.c_personid IS NULL THEN 0 ELSE 1 END target_entry
                FROM BIOG_MAIN b
                LEFT JOIN (SELECT DISTINCT c_personid FROM ENTRY_DATA WHERE c_personid IS NOT NULL) e
                  ON e.c_personid=b.c_personid
            )
            SELECT p.c_dy AS dynasty_code,
                   COALESCE(d.c_dynasty, '[NULL/unmapped]') AS dynasty,
                   COALESCE(d.c_dynasty_chn, '[NULL/unmapped]') AS dynasty_chn,
                   COUNT(*) AS n_people,
                   SUM(target_entry) AS n_positive,
                   AVG(target_entry * 1.0) AS target_rate
            FROM people p LEFT JOIN DYNASTIES d ON d.c_dy=p.c_dy
            GROUP BY p.c_dy, d.c_dynasty, d.c_dynasty_chn
            ORDER BY n_people DESC
            """,
            connection,
        )
        by_index_year = pd.read_sql_query(
            """
            WITH entry_people AS (SELECT DISTINCT c_personid FROM ENTRY_DATA WHERE c_personid IS NOT NULL)
            SELECT b.c_index_year AS index_year,
                   COUNT(*) AS n_people,
                   SUM(CASE WHEN e.c_personid IS NULL THEN 0 ELSE 1 END) AS n_positive,
                   AVG(CASE WHEN e.c_personid IS NULL THEN 0.0 ELSE 1.0 END) AS target_rate
            FROM BIOG_MAIN b LEFT JOIN entry_people e ON e.c_personid=b.c_personid
            GROUP BY b.c_index_year ORDER BY b.c_index_year
            """,
            connection,
        )
        entry_codes = pd.read_sql_query(
            """
            WITH type_labels AS (
                SELECT r.c_entry_code,
                       group_concat(t.c_entry_type, '; ') AS entry_type_codes,
                       group_concat(t.c_entry_type_desc, '; ') AS entry_type_names,
                       group_concat(t.c_entry_type_desc_chn, '; ') AS entry_type_names_chn
                FROM ENTRY_CODE_TYPE_REL r
                LEFT JOIN ENTRY_TYPES t ON t.c_entry_type=r.c_entry_type
                GROUP BY r.c_entry_code
            )
            SELECT e.c_entry_code AS entry_code,
                   COALESCE(c.c_entry_desc, '[unmapped]') AS entry_name_en,
                   COALESCE(c.c_entry_desc_chn, '[unmapped]') AS entry_name_zh,
                   COALESCE(t.entry_type_codes, '[unmapped]') AS entry_type_codes,
                   COALESCE(t.entry_type_names, '[unmapped]') AS entry_type_names_en,
                   COALESCE(t.entry_type_names_chn, '[unmapped]') AS entry_type_names_zh,
                   COUNT(*) AS record_count,
                   COUNT(DISTINCT e.c_personid) AS person_count
            FROM ENTRY_DATA e
            LEFT JOIN ENTRY_CODES c ON c.c_entry_code=e.c_entry_code
            LEFT JOIN type_labels t ON t.c_entry_code=e.c_entry_code
            GROUP BY e.c_entry_code, c.c_entry_desc, c.c_entry_desc_chn,
                     t.entry_type_codes, t.entry_type_names, t.entry_type_names_chn
            ORDER BY record_count DESC
            """,
            connection,
        )
        entry_types = pd.read_sql_query(
            """
            SELECT r.c_entry_type AS entry_type_code,
                   COALESCE(t.c_entry_type_desc, '[unmapped]') AS entry_type_name_en,
                   COALESCE(t.c_entry_type_desc_chn, '[unmapped]') AS entry_type_name_zh,
                   COUNT(*) AS record_count,
                   COUNT(DISTINCT e.c_personid) AS person_count
            FROM ENTRY_DATA e
            LEFT JOIN ENTRY_CODE_TYPE_REL r ON r.c_entry_code=e.c_entry_code
            LEFT JOIN ENTRY_TYPES t ON t.c_entry_type=r.c_entry_type
            GROUP BY r.c_entry_type, t.c_entry_type_desc, t.c_entry_type_desc_chn
            ORDER BY record_count DESC
            """,
            connection,
        )

        audit = {
            "entry_rows": int(scalar(connection, "SELECT COUNT(*) FROM ENTRY_DATA")),
            "entry_unique_people": int(scalar(connection, "SELECT COUNT(DISTINCT c_personid) FROM ENTRY_DATA WHERE c_personid IS NOT NULL")),
            "entry_null_person_ids": int(scalar(connection, "SELECT COUNT(*) FROM ENTRY_DATA WHERE c_personid IS NULL")),
            "entry_orphan_rows": int(scalar(connection, "SELECT COUNT(*) FROM ENTRY_DATA e WHERE e.c_personid IS NOT NULL AND NOT EXISTS (SELECT 1 FROM BIOG_MAIN b WHERE b.c_personid=e.c_personid)")),
            "entry_orphan_unique_ids": int(scalar(connection, "SELECT COUNT(DISTINCT e.c_personid) FROM ENTRY_DATA e WHERE e.c_personid IS NOT NULL AND NOT EXISTS (SELECT 1 FROM BIOG_MAIN b WHERE b.c_personid=e.c_personid)")),
            "people_with_multiple_entry_rows": int(scalar(connection, "SELECT COUNT(*) FROM (SELECT c_personid FROM ENTRY_DATA GROUP BY c_personid HAVING COUNT(*)>1)")),
            "max_entry_rows_per_person": int(scalar(connection, "SELECT MAX(n) FROM (SELECT COUNT(*) n FROM ENTRY_DATA GROUP BY c_personid)")),
            "duplicate_person_code_year_groups": int(scalar(connection, "SELECT COUNT(*) FROM (SELECT c_personid,c_entry_code,c_year FROM ENTRY_DATA GROUP BY c_personid,c_entry_code,c_year HAVING COUNT(*)>1)")),
            "unmapped_entry_code_rows": int(scalar(connection, "SELECT COUNT(*) FROM ENTRY_DATA e LEFT JOIN ENTRY_CODES c ON c.c_entry_code=e.c_entry_code WHERE c.c_entry_code IS NULL")),
        }

    target_path = interim_dir / "person_target.parquet"
    target.to_parquet(target_path, index=False, compression="zstd")
    summary.to_csv(tables_dir / "target_summary.csv", index=False)
    dynasty.to_csv(tables_dir / "target_by_dynasty.csv", index=False)
    by_index_year.to_csv(tables_dir / "target_by_index_year.csv", index=False)
    entry_codes.to_csv(tables_dir / "entry_code_distribution.csv", index=False)
    entry_types.to_csv(tables_dir / "entry_type_distribution.csv", index=False)

    top_rows = entry_codes.head(25).itertuples(index=False, name=None)
    document = [
        "# Target definition and audit",
        "",
        "## Default: Target V1",
        "",
        "`target_entry = 1` exactly when a non-NULL `BIOG_MAIN.c_personid` appears at least once in `ENTRY_DATA`; otherwise it is 0. "
        "Counts are aggregated in SQLite before the one-person target table is materialized.",
        "",
        "> Interpret 0 as “no entry record found in the current CBDB `ENTRY_DATA`”, not as proof that the historical person never entered office.",
        "",
        "## Population statistics",
        "",
        markdown_table(
            ["people", "positive", "negative", "positive rate", "negative rate"],
            [[n_people, n_positive, n_negative, f"{n_positive / n_people:.4%}", f"{n_negative / n_people:.4%}"]],
        ),
        "",
        "## Integrity checks",
        "",
        markdown_table(["check", "value"], audit.items()),
        "",
        "Multiple rows per person and repeated person/code/year groups are reported rather than deleted: sources, sequences, institutions, or other fields may legitimately distinguish them. Target V1 collapses all such rows to presence.",
        "",
        "## Entry modes observed",
        "",
        markdown_table(
            ["code", "English", "中文", "type", "type English", "type 中文", "records", "people"],
            top_rows,
        ),
        "",
        "`ENTRY_DATA` contains heterogeneous modes including examinations, school/student statuses, kin privilege, inheritance, purchase, military service, palace routes, recommendations, and unknown/deprecated values. Therefore table presence is reproducible but not synonymous with a single, uniform act of entering government service.",
        "",
        "## Frozen Phase 1.5 Patch display semantics",
        "",
        markdown_table(
            ["key", "display name", "中文解释", "role"],
            [
                ["V1", "ENTRY record presence", "是否存在 ENTRY_DATA 记录", "Primary record-presence target; unchanged"],
                ["V2a", "Broad formal entry/credential target", "广义正式入仕途径/资格记录", "Taxonomy-based sensitivity candidate"],
                ["V2b", "High-confidence formal entry/credential target", "高置信度正式入仕途径/资格记录", "Higher-confidence sensitivity candidate; credentials do not imply posting"],
                ["Posting", "Recorded office-holding / posting outcome", "是否存在任官记录", "Auxiliary robustness outcome"],
            ],
        ),
        "",
        "`POSTING_DATA` is also an incomplete historical record and is not treated as ground-truth verification of `ENTRY_DATA`. Lower overlap with Posting does not automatically imply a worse target definition. V2 semantics follow historical interpretation plus official CBDB code descriptions; overlap with Posting is only an auxiliary diagnostic.",
        "",
        "No codes are silently removed from V1; the V2 columns remain versioned sensitivity candidates and do not replace the Phase 1 target.",
        "",
        "## Group diagnostics",
        "",
        "Target rates by dynasty and index year are in `outputs/tables/target_by_dynasty.csv` and `outputs/tables/target_by_index_year.csv`. "
        "They are coverage diagnostics, not estimates of population-level historical entry rates.",
        "",
    ]
    atomic_write_text(audit_dir / "target_definition.md", "\n".join(document))
    logger.info("Target complete: people=%d positive=%d (%.4f%%)", n_people, n_positive, 100 * n_positive / n_people)
    logger.info("Wrote %s", target_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
