#!/usr/bin/env python3
"""Profile key CBDB tables, validate inferred joins, and report data-quality issues."""

from __future__ import annotations

import csv
import json
import math
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import configured_path, load_config
from src.db import actual_object_name, column_names, columns, connect_readonly, object_names, quote_identifier, scalar
from src.utils import atomic_write_text, markdown_escape, markdown_table, setup_logging


KEY_TABLES = [
    "BIOG_MAIN",
    "ENTRY_DATA",
    "KIN_DATA",
    "ASSOC_DATA",
    "STATUS_DATA",
    "BIOG_ADDR_DATA",
    "BIOG_INST_DATA",
    "BIOG_TEXT_DATA",
    "POSTING_DATA",
    "POSTED_TO_OFFICE_DATA",
]

CODE_TABLES = [
    "ADDRESSES",
    "DYNASTIES",
    "INDEXYEAR_TYPE_CODES",
    "ETHNICITY_TRIBE_CODES",
    "HOUSEHOLD_STATUS_CODES",
    "ENTRY_CODES",
    "ENTRY_TYPES",
    "ENTRY_CODE_TYPE_REL",
    "PARENTAL_STATUS_CODES",
    "KINSHIP_CODES",
    "ASSOC_CODES",
    "ASSOC_TYPES",
    "ASSOC_CODE_TYPE_REL",
    "STATUS_CODES",
    "STATUS_TYPES",
    "STATUS_CODE_TYPE_REL",
    "BIOG_ADDR_CODES",
    "ADDR_CODES",
    "BIOG_INST_CODES",
    "SOCIAL_INSTITUTION_CODES",
    "SOCIAL_INSTITUTION_NAME_CODES",
    "TEXT_ROLE_CODES",
    "TEXT_CODES",
    "OFFICE_CODES",
    "OFFICE_CATEGORIES",
    "APPOINTMENT_CODES",
    "ASSUME_OFFICE_CODES",
]


def profile_columns(connection, table: str, row_count: int, config: dict, logger) -> list[dict[str, Any]]:
    metadata = columns(connection, table)
    if not metadata:
        return []
    qtable = quote_identifier(table)
    expressions = []
    for column in metadata:
        qcolumn = quote_identifier(column["name"])
        expressions.append(f"SUM(CASE WHEN {qcolumn} IS NULL THEN 1 ELSE 0 END)")
        expressions.append(f"SUM(CASE WHEN typeof({qcolumn})='text' AND trim({qcolumn})='' THEN 1 ELSE 0 END)")
    values = connection.execute("SELECT " + ",".join(expressions) + f" FROM {qtable}").fetchone()

    exact_limit = int(config["analysis"]["exact_distinct_max_rows"])
    sample_target = int(config["analysis"]["distinct_sample_target_rows"])
    sampled = row_count > exact_limit
    if sampled:
        step = max(1, math.ceil(row_count / sample_target))
        sample_source = f"(SELECT * FROM {qtable} WHERE rowid % {step}=0 LIMIT {sample_target})"
    else:
        step = 1
        sample_source = qtable

    result = []
    for index, column in enumerate(metadata):
        name = column["name"]
        qcolumn = quote_identifier(name)
        try:
            n_unique = scalar(connection, f"SELECT COUNT(DISTINCT {qcolumn}) FROM {sample_source}")
        except Exception:
            sample_source = f"(SELECT * FROM {qtable} LIMIT {sample_target})"
            n_unique = scalar(connection, f"SELECT COUNT(DISTINCT {qcolumn}) FROM {sample_source}")
            sampled = row_count > sample_target
        examples = [
            row[0] for row in connection.execute(
                f"SELECT DISTINCT {qcolumn} FROM {sample_source} "
                f"WHERE {qcolumn} IS NOT NULL AND trim(CAST({qcolumn} AS TEXT))<>'' LIMIT 3"
            )
        ]
        null_count = int(values[index * 2] or 0)
        empty_count = int(values[index * 2 + 1] or 0)
        result.append(
            {
                "table": table,
                "column": name,
                "dtype": column["type"],
                "null_count": null_count,
                "null_rate": null_count / row_count if row_count else 0.0,
                "empty_count": empty_count,
                "empty_rate": empty_count / row_count if row_count else 0.0,
                "n_unique": n_unique,
                "sampled": sampled,
                "sample_step": step if sampled else 1,
                "example_values": json.dumps(examples, ensure_ascii=False, default=str),
            }
        )
    logger.info("Profiled %s: %d rows, %d columns, distinct_sampled=%s", table, row_count, len(metadata), sampled)
    return result


def target_for_column(column: str) -> tuple[str, str] | None:
    lower = column.lower()
    if lower in {"c_personid", "c_personid1", "c_personid2", "c_kin_id", "c_assoc_id", "c_assoc_kin_id", "c_tertiary_personid", "c_assoc_claimer_id"} or lower.endswith("personid"):
        return "BIOG_MAIN", "c_personid"
    if lower in {"c_addr_id", "c_index_addr_id", "c_entry_addr_id", "c_natal"} or lower.endswith("_addr_id"):
        return "ADDR_CODES", "c_addr_id"
    direct = {
        "c_entry_code": ("ENTRY_CODES", "c_entry_code"),
        "c_kin_code": ("KINSHIP_CODES", "c_kincode"),
        "c_assoc_kin_code": ("KINSHIP_CODES", "c_kincode"),
        "c_assoc_code": ("ASSOC_CODES", "c_assoc_code"),
        "c_status_code": ("STATUS_CODES", "c_status_code"),
        "c_posting_id": ("POSTING_DATA", "c_posting_id"),
        "c_office_id": ("OFFICE_CODES", "c_office_id"),
        "c_office_id_backup": ("OFFICE_CODES", "c_office_id"),
        "c_dy": ("DYNASTIES", "c_dy"),
        "c_entry_dy": ("DYNASTIES", "c_dy"),
        "c_bi_role_code": ("BIOG_INST_CODES", "c_bi_role_code"),
        "c_role_id": ("TEXT_ROLE_CODES", "c_role_id"),
        "c_textid": ("TEXT_CODES", "c_textid"),
    }
    return direct.get(lower)


def infer_relationships(connection, existing: set[str], logger) -> list[dict[str, Any]]:
    relationships: list[dict[str, Any]] = []
    for table, kind in object_names(connection, ("table",)):
        for fk in connection.execute(f"PRAGMA foreign_key_list({quote_identifier(table)})"):
            relationships.append(
                {
                    "source_table": table,
                    "source_column": fk[3],
                    "target_table": fk[2],
                    "target_column": fk[4],
                    "relationship_type": "declared foreign key",
                    "nonnull_rows": "",
                    "matched_rows": "",
                    "match_rate": "",
                    "notes": f"ON UPDATE {fk[5]}; ON DELETE {fk[6]}",
                }
            )

    seen = set()
    for table in KEY_TABLES + ["ADDRESSES"]:
        if table not in existing:
            continue
        for column in column_names(connection, table):
            target = target_for_column(column)
            if not target or target[0] not in existing:
                continue
            target_table, target_column = target
            if table == target_table and column.lower() == target_column.lower():
                continue
            if target_column.lower() not in {name.lower() for name in column_names(connection, target_table)}:
                continue
            signature = (table, column, target_table, target_column)
            if signature in seen:
                continue
            seen.add(signature)
            qs, qc = quote_identifier(table), quote_identifier(column)
            qt, qtc = quote_identifier(target_table), quote_identifier(target_column)
            query = f"""
                SELECT COUNT(s.{qc}), COUNT(t.{qtc})
                FROM {qs} AS s
                LEFT JOIN {qt} AS t ON s.{qc}=t.{qtc}
            """
            nonnull, matched = connection.execute(query).fetchone()
            relationships.append(
                {
                    "source_table": table,
                    "source_column": column,
                    "target_table": target_table,
                    "target_column": target_column,
                    "relationship_type": "inferred join key",
                    "nonnull_rows": int(nonnull),
                    "matched_rows": int(matched),
                    "match_rate": (matched / nonnull) if nonnull else "",
                    "notes": "Name/semantic inference validated against observed values; not a declared constraint.",
                }
            )
            logger.info("Validated inferred join %s.%s -> %s.%s (%s/%s)", table, column, target_table, target_column, matched, nonnull)
    return relationships


def quality_row(issue: str, table: str, column: str, count: int, severity: str, details: str) -> dict[str, Any]:
    return {"issue": issue, "table": table, "column": column, "count": int(count), "severity": severity, "details": details}


def data_quality_checks(connection, existing: set[str]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    null_people = scalar(connection, "SELECT COUNT(*) FROM BIOG_MAIN WHERE c_personid IS NULL")
    duplicate_people = scalar(connection, "SELECT COALESCE(SUM(n-1),0) FROM (SELECT COUNT(*) n FROM BIOG_MAIN GROUP BY c_personid HAVING COUNT(*)>1)")
    issues.append(quality_row("null_person_id", "BIOG_MAIN", "c_personid", null_people, "error", "Primary person identifier is NULL."))
    issues.append(quality_row("duplicate_person_id", "BIOG_MAIN", "c_personid", duplicate_people, "error", "Rows beyond the first for duplicated person identifiers."))

    orphan_columns = {
        "ENTRY_DATA": ["c_personid"],
        "KIN_DATA": ["c_personid", "c_kin_id"],
        "ASSOC_DATA": ["c_personid", "c_assoc_id", "c_kin_id", "c_assoc_kin_id", "c_tertiary_personid", "c_assoc_claimer_id"],
    }
    for table, candidates in orphan_columns.items():
        if table not in existing:
            continue
        available = {name.lower(): name for name in column_names(connection, table)}
        for candidate in candidates:
            if candidate not in available:
                continue
            column = available[candidate]
            qcolumn = quote_identifier(column)
            nulls = scalar(connection, f"SELECT COUNT(*) FROM {quote_identifier(table)} WHERE {qcolumn} IS NULL")
            orphans = scalar(
                connection,
                f"SELECT COUNT(*) FROM {quote_identifier(table)} s WHERE s.{qcolumn} IS NOT NULL "
                f"AND NOT EXISTS (SELECT 1 FROM BIOG_MAIN b WHERE b.c_personid=s.{qcolumn})",
            )
            issues.append(quality_row("null_relation_person_id", table, column, nulls, "warning", "NULL identifier in a person relation field."))
            issues.append(quality_row("orphan_person_id", table, column, orphans, "warning", "Non-NULL identifier absent from BIOG_MAIN."))

    entry_duplicate_groups = scalar(
        connection,
        """SELECT COUNT(*) FROM (
               SELECT c_personid,c_entry_code,c_year,COUNT(*) n
               FROM ENTRY_DATA GROUP BY c_personid,c_entry_code,c_year HAVING COUNT(*)>1
           )""",
    )
    multiple_entries = scalar(
        connection,
        "SELECT COUNT(*) FROM (SELECT c_personid FROM ENTRY_DATA GROUP BY c_personid HAVING COUNT(*)>1)",
    )
    issues.append(quality_row("duplicate_person_entry_code_year_groups", "ENTRY_DATA", "c_personid,c_entry_code,c_year", entry_duplicate_groups, "info", "Groups sharing person, entry code, and year; distinct source/sequence records may be legitimate."))
    issues.append(quality_row("people_with_multiple_entry_records", "ENTRY_DATA", "c_personid", multiple_entries, "info", "Multiple ENTRY_DATA records are expected but are collapsed for Target V1."))

    year_columns: dict[str, list[str]] = {}
    for table in KEY_TABLES:
        if table in existing:
            year_columns[table] = [name for name in column_names(connection, table) if name.lower().endswith("year")]
    for table, names in year_columns.items():
        for column in names:
            qtable, qcolumn = quote_identifier(table), quote_identifier(column)
            negative, sentinel, extreme_high = connection.execute(
                f"SELECT SUM(CASE WHEN {qcolumn}<0 THEN 1 ELSE 0 END), "
                f"SUM(CASE WHEN {qcolumn}<=-9000 THEN 1 ELSE 0 END), "
                f"SUM(CASE WHEN {qcolumn}>2100 THEN 1 ELSE 0 END) FROM {qtable}"
            ).fetchone()
            if negative:
                issues.append(quality_row("negative_year_values", table, column, negative, "info", "May be valid BCE years; sentinel values are counted separately and no rows are removed."))
            minus_one = scalar(connection, f"SELECT COUNT(*) FROM {qtable} WHERE {qcolumn}=-1")
            if minus_one:
                issues.append(quality_row("year_value_minus_one", table, column, minus_one, "warning", "Could mean 1 BCE or an unknown-value sentinel; the observed frequency should guide field-specific treatment."))
            if sentinel:
                issues.append(quality_row("year_sentinel_le_minus_9000", table, column, sentinel, "warning", "Likely unknown-value sentinel; preserve raw value and treat explicitly during feature engineering."))
            if extreme_high:
                issues.append(quality_row("year_above_2100", table, column, extreme_high, "warning", "Outside plausible historical coverage; not removed in Phase 1."))

    comparisons = [
        ("birth_after_death", "c_birthyear>c_deathyear", "Birth year exceeds death year."),
        ("index_before_birth", "c_index_year<c_birthyear", "Index year precedes birth year."),
        ("index_after_death", "c_index_year>c_deathyear", "Index year follows death year."),
    ]
    for issue, predicate, detail in comparisons:
        relevant = predicate.replace(">", " ").replace("<", " ").split()
        nonmissing = " AND ".join(f"{column} IS NOT NULL AND {column}<>0" for column in relevant)
        count = scalar(connection, f"SELECT COUNT(*) FROM BIOG_MAIN WHERE {nonmissing} AND {predicate}")
        issues.append(quality_row(issue, "BIOG_MAIN", ",".join(relevant), count, "warning", detail + " Raw records are retained."))
    return issues


def table_document(connection, table: str, row_count: int, profiles: list[dict[str, Any]], relationships: list[dict[str, Any]]) -> str:
    table_columns = columns(connection, table)
    person_fields = [column["name"] for column in table_columns if "personid" in column["name"].lower() or column["name"].lower() in {"c_kin_id", "c_assoc_id", "c_assoc_kin_id"}]
    joins = [row for row in relationships if row["source_table"] == table]
    sample_rows = connection.execute(f"SELECT * FROM {quote_identifier(table)} LIMIT 5").fetchall()
    sample_headers = [column["name"] for column in table_columns]
    profile_rows = [row for row in profiles if row["table"] == table]
    sections = [
        f"# {table}",
        "",
        f"Rows: **{row_count:,}**; columns: **{len(table_columns)}**.",
        "",
        f"Person identifier fields observed: {', '.join(f'`{field}`' for field in person_fields) if person_fields else 'none'}.",
        "",
        "## Column audit",
        "",
        markdown_table(
            ["column", "SQLite type", "NULL", "NULL rate", "empty", "distinct", "sampled", "examples"],
            ([row["column"], row["dtype"], row["null_count"], f'{row["null_rate"]:.4%}', row["empty_count"], row["n_unique"], row["sampled"], row["example_values"]] for row in profile_rows),
        ),
        "",
        "Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.",
        "",
        "## Join-key evidence",
        "",
    ]
    if joins:
        sections.append(markdown_table(
            ["source key", "target", "basis", "matched/non-NULL", "match rate"],
            ([row["source_column"], f'{row["target_table"]}.{row["target_column"]}', row["relationship_type"], f'{row["matched_rows"]}/{row["nonnull_rows"]}', f'{row["match_rate"]:.4%}' if isinstance(row["match_rate"], float) else ""] for row in joins),
        ))
    else:
        sections.append("No declared or conservatively inferred join key was recorded for this table.")
    sections.extend(["", "## First five rows", ""])
    if sample_rows:
        sections.append(markdown_table(sample_headers, ([row[name] for name in sample_headers] for row in sample_rows)))
    else:
        sections.append("Table is empty.")
    sections.append("")
    return "\n".join(sections)


def main() -> int:
    config = load_config()
    schema_dir = configured_path(config, "paths", "schema_docs")
    tables_dir = configured_path(config, "paths", "tables")
    logger = setup_logging("schema", configured_path(config, "paths", "logs") / "schema_analysis.log")
    database = configured_path(config, "database", "working_db")

    with connect_readonly(database, config["database"]["busy_timeout_ms"]) as connection:
        existing = {name for name, _ in object_names(connection)}
        missing_key = [table for table in KEY_TABLES if table not in existing]
        if missing_key:
            raise RuntimeError(f"Required key tables are missing: {missing_key}")

        relationships = infer_relationships(connection, existing, logger)
        analyzed = [table for table in KEY_TABLES + CODE_TABLES if table in existing]
        all_profiles: list[dict[str, Any]] = []
        row_counts: dict[str, int] = {}
        for table in analyzed:
            row_count = int(scalar(connection, f"SELECT COUNT(*) FROM {quote_identifier(table)}"))
            row_counts[table] = row_count
            all_profiles.extend(profile_columns(connection, table, row_count, config, logger))

        for table in analyzed:
            atomic_write_text(
                schema_dir / f"{table}.md",
                table_document(connection, table, row_counts[table], all_profiles, relationships),
            )

        issues = data_quality_checks(connection, existing)

    profile_fields = ["table", "column", "dtype", "null_count", "null_rate", "empty_count", "empty_rate", "n_unique", "sampled", "sample_step", "example_values"]
    with (tables_dir / "key_table_columns.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=profile_fields)
        writer.writeheader()
        writer.writerows(all_profiles)

    relationship_fields = ["source_table", "source_column", "target_table", "target_column", "relationship_type", "nonnull_rows", "matched_rows", "match_rate", "notes"]
    with (tables_dir / "table_relationships.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=relationship_fields)
        writer.writeheader()
        writer.writerows(relationships)

    relationship_md = [
        "# CBDB table relationships",
        "",
        "`declared foreign key` means SQLite exposes a constraint through `PRAGMA foreign_key_list`. "
        "`inferred join key` means a conservative semantic/name match whose observed values were validated; it is not represented as a database constraint.",
        "",
        "## Required person-level paths",
        "",
        "- `BIOG_MAIN.c_personid` → `ENTRY_DATA.c_personid` (Target V1 source; reverse presentation of the validated child-to-parent join)",
        "- `BIOG_MAIN.c_personid` → `KIN_DATA.c_personid`",
        "- `BIOG_MAIN.c_personid` → `ASSOC_DATA.c_personid`",
        "- `BIOG_MAIN.c_personid` → `BIOG_ADDR_DATA.c_personid`",
        "- `BIOG_MAIN.c_personid` → `STATUS_DATA.c_personid`",
        "- `BIOG_MAIN.c_personid` → `POSTING_DATA.c_personid` / `POSTED_TO_OFFICE_DATA.c_personid`",
        "",
        "These are one-to-many paths. Each child must be aggregated to one person before joining; joining raw child tables together would create a Cartesian-like fan-out.",
        "",
        "## Machine-audited relationships",
        "",
        markdown_table(
            ["source", "target", "basis", "matched/non-NULL", "match rate"],
            ([f'{row["source_table"]}.{row["source_column"]}', f'{row["target_table"]}.{row["target_column"]}', row["relationship_type"], f'{row["matched_rows"]}/{row["nonnull_rows"]}' if row["nonnull_rows"] != "" else "", f'{row["match_rate"]:.4%}' if isinstance(row["match_rate"], float) else ""] for row in relationships),
        ),
        "",
    ]
    atomic_write_text(schema_dir / "table_relationships.md", "\n".join(relationship_md))

    with (tables_dir / "data_quality_issues.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["issue", "table", "column", "count", "severity", "details"])
        writer.writeheader()
        writer.writerows(issues)
    logger.info("Wrote %d column profiles, %d relationships, and %d quality checks", len(all_profiles), len(relationships), len(issues))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
