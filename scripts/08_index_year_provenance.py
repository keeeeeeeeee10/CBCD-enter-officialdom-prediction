#!/usr/bin/env python3
"""Audit actual index-year provenance chains and expose only confirmed-safe anchors."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import configured_path, load_config
from src.db import connect_readonly
from src.phase15 import MAJOR_DYNASTIES, clean_year_series
from src.utils import atomic_write_text, markdown_table, setup_logging


BIRTH_COMPONENTS = {"01", "03", "11", "13", "15", "17", "19", "21", "23", "25", "27"}
DEATH_COMPONENTS = {"02", "29", "30"}
ENTRY_COMPONENTS = {"05", "06", "07", "08", "09", "10"}
KIN_COMPONENTS = set(f"{value:02d}" for value in range(3, 29)) - {"05", "07", "09"}
DESCENDANT_COMPONENTS = {"13", "14", "15", "16", "23", "24", "25", "26"}
SPOUSE_COMPONENTS = {"03", "04", "06", "08", "10", "17", "18"}


def normalize_code(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def parse_provenance(code: str, official_codes: set[str]) -> list[str] | None:
    """Parse exact or concatenated two-character provenance chains found in BIOG_MAIN."""
    if not code:
        return None
    if code in official_codes:
        return [code]
    if not code.isdigit() or len(code) % 2:
        return None
    components = [code[index : index + 2] for index in range(0, len(code), 2)]
    return components if all(component in official_codes for component in components) else None


def classify(code: str, components: list[str] | None, descriptions: dict[str, dict]) -> dict[str, object]:
    if not components or "00" in components:
        return {
            "parsed_components": "" if not components else ";".join(components),
            "uses_birth_information": False,
            "uses_death_information": False,
            "uses_kin_information": False,
            "uses_entry_information": False,
            "uses_posting_information": False,
            "uses_other_future_event": False,
            "safe_for_pre_entry_model": "UNKNOWN",
            "confidence": "LOW",
            "reason": "Blank, unknown, or unparseable provenance; UNKNOWN is not treated as safe.",
        }
    uses_birth = bool(set(components) & BIRTH_COMPONENTS)
    uses_death = bool(set(components) & DEATH_COMPONENTS)
    uses_entry = bool(set(components) & ENTRY_COMPONENTS)
    uses_kin = bool(set(components) & KIN_COMPONENTS)
    uses_future = uses_death or bool(set(components) & (DESCENDANT_COMPONENTS | SPOUSE_COMPONENTS))
    labels = [descriptions[component]["en"] for component in components]

    if uses_entry:
        leakage_class, confidence = "UNSAFE", "HIGH"
        reason = "Provenance chain explicitly uses jinshi/juren/xiucai entry information: " + " -> ".join(labels)
    elif uses_death:
        leakage_class, confidence = "UNSAFE", "HIGH"
        reason = "Provenance chain uses death year, a future outcome relative to a pre-entry prediction: " + " -> ".join(labels)
    elif set(components) & DESCENDANT_COMPONENTS:
        leakage_class, confidence = "UNSAFE", "HIGH"
        reason = "Provenance uses a child or son-in-law, which can be observed after the focal prediction time: " + " -> ".join(labels)
    elif components == ["01"]:
        leakage_class, confidence = "SAFE", "HIGH"
        reason = "Official provenance is directly based on the focal person's birth year and contains no career/future chain component."
    else:
        leakage_class, confidence = "CONDITIONAL", "MEDIUM"
        reason = "Kin/spouse or recursively derived index information is not direct target evidence, but its timing and upstream provenance are not uniformly guaranteed: " + " -> ".join(labels)
    return {
        "parsed_components": ";".join(components),
        "uses_birth_information": uses_birth,
        "uses_death_information": uses_death,
        "uses_kin_information": uses_kin,
        "uses_entry_information": uses_entry,
        "uses_posting_information": False,
        "uses_other_future_event": uses_future,
        "safe_for_pre_entry_model": leakage_class,
        "confidence": confidence,
        "reason": reason,
    }


def coverage_row(frame: pd.DataFrame, group_type: str, group_name: str, sentinels: list[int], lower: int, upper: int) -> dict[str, object]:
    n = len(frame)
    row: dict[str, object] = {"group_type": group_type, "group_name": group_name, "n_people": n}
    for field, clean_field in (("birth_year", "valid_birth_year"), ("death_year", "valid_death_year"), ("index_year", "valid_index_year")):
        valid_count = int(frame[clean_field].notna().sum())
        row[f"{field}_valid"] = valid_count
        row[f"{field}_valid_rate"] = valid_count / n if n else 0.0
        numeric = pd.to_numeric(frame[field], errors="coerce")
        for sentinel in sentinels:
            label = str(sentinel).replace("-", "minus_")
            row[f"{field}_sentinel_{label}"] = int(numeric.eq(sentinel).sum())
        row[f"{field}_below_{lower}"] = int(numeric.lt(lower).sum())
        row[f"{field}_above_{upper}"] = int(numeric.gt(upper).sum())
    safe_count = int(frame["safe_index_year_available"].sum())
    row["safe_index_year_valid"] = safe_count
    row["safe_index_year_valid_rate"] = safe_count / n if n else 0.0
    comparable = frame["valid_birth_year"].notna() & frame["valid_death_year"].notna()
    row["birth_after_death"] = int((comparable & frame["valid_birth_year"].gt(frame["valid_death_year"])).sum())
    return row


def main() -> int:
    config = load_config()
    tables_dir = configured_path(config, "paths", "tables")
    interim_dir = configured_path(config, "paths", "interim")
    audit_dir = configured_path(config, "paths", "audit_docs")
    logger = setup_logging("index_provenance", configured_path(config, "paths", "logs") / "index_year_provenance.log")
    database = configured_path(config, "database", "working_db")

    with connect_readonly(database, config["database"]["busy_timeout_ms"]) as connection:
        code_table = pd.read_sql_query("SELECT * FROM INDEXYEAR_TYPE_CODES ORDER BY c_index_year_type_code", connection, dtype=str)
        people = pd.read_sql_query(
            """
            SELECT b.c_personid AS person_id, b.c_birthyear AS birth_year,
                   b.c_deathyear AS death_year, b.c_index_year AS index_year,
                   b.c_index_year_type_code AS index_year_type_code,
                   b.c_index_year_source_id AS index_year_source_id,
                   b.c_dy AS dynasty_code, d.c_dynasty AS dynasty,
                   CASE WHEN e.c_personid IS NULL THEN 0 ELSE 1 END AS target_entry_v1
            FROM BIOG_MAIN b
            LEFT JOIN DYNASTIES d ON d.c_dy=b.c_dy
            LEFT JOIN (SELECT DISTINCT c_personid FROM ENTRY_DATA WHERE c_personid IS NOT NULL) e
              ON e.c_personid=b.c_personid
            ORDER BY b.c_personid
            """,
            connection,
        )
        source_matches = pd.read_sql_query(
            """
            SELECT COALESCE(b.c_index_year_type_code, '') AS index_year_type_code,
                   SUM(CASE WHEN b.c_index_year_source_id IS NOT NULL AND b.c_index_year_source_id<>0 THEN 1 ELSE 0 END) AS n_source_id_present,
                   SUM(CASE WHEN s.c_personid IS NOT NULL AND b.c_index_year_source_id<>0 THEN 1 ELSE 0 END) AS n_source_id_matches_biog
            FROM BIOG_MAIN b LEFT JOIN BIOG_MAIN s ON s.c_personid=b.c_index_year_source_id
            GROUP BY COALESCE(b.c_index_year_type_code, '')
            """,
            connection,
        )

    descriptions = {
        str(row.c_index_year_type_code).strip(): {
            "en": row.c_index_year_type_desc,
            "zh": row.c_index_year_type_hz,
            "notes": row.c_notes,
        }
        for row in code_table.itertuples()
    }
    official_codes = set(descriptions)
    people["index_year_type_code"] = people["index_year_type_code"].map(normalize_code)
    people["valid_birth_year"] = clean_year_series(people["birth_year"], config)
    people["valid_death_year"] = clean_year_series(people["death_year"], config)
    people["valid_index_year"] = clean_year_series(people["index_year"], config)

    aggregate = (
        people.groupby("index_year_type_code", dropna=False)
        .agg(n_people=("person_id", "size"), n_entry_positive=("target_entry_v1", "sum"), n_valid_index_year=("valid_index_year", lambda x: int(x.notna().sum())))
        .reset_index()
    )
    aggregate["entry_positive_rate"] = aggregate["n_entry_positive"] / aggregate["n_people"]
    source_matches["index_year_type_code"] = source_matches["index_year_type_code"].map(normalize_code)
    aggregate = aggregate.merge(source_matches, on="index_year_type_code", how="left")

    taxonomy_rows = []
    class_lookup: dict[str, str] = {}
    for row in aggregate.itertuples(index=False):
        code = normalize_code(row.index_year_type_code)
        components = parse_provenance(code, official_codes)
        flags = classify(code, components, descriptions)
        class_lookup[code] = str(flags["safe_for_pre_entry_model"])
        if components:
            description_en = " -> ".join(descriptions[item]["en"] for item in components)
            description_zh = " -> ".join(descriptions[item]["zh"] for item in components)
        else:
            description_en = "Unknown/unmapped provenance"
            description_zh = "未知／未映射来源"
        taxonomy_rows.append({
            "index_year_type_code": code,
            "description_zh": description_zh,
            "description_en": description_en,
            "n_people": int(row.n_people),
            "n_entry_positive": int(row.n_entry_positive),
            "entry_positive_rate": float(row.entry_positive_rate),
            "n_valid_index_year": int(row.n_valid_index_year),
            "n_source_id_present": int(row.n_source_id_present or 0),
            "n_source_id_matches_biog": int(row.n_source_id_matches_biog or 0),
            **flags,
        })
    provenance = pd.DataFrame(taxonomy_rows).sort_values("n_people", ascending=False)
    provenance.to_csv(tables_dir / "index_year_provenance.csv", index=False)

    people["index_year_leakage_class"] = people["index_year_type_code"].map(class_lookup).fillna("UNKNOWN")
    people["safe_index_year"] = people["valid_index_year"].where(people["index_year_leakage_class"].eq("SAFE"))
    people["safe_index_year_available"] = people["safe_index_year"].notna().astype("int8")
    safe_output = people[[
        "person_id", "birth_year", "index_year", "safe_index_year", "index_year_type_code",
        "index_year_leakage_class", "target_entry_v1",
    ]].copy()
    safe_output["safe_index_year_available"] = people["safe_index_year_available"]
    safe_output.to_parquet(interim_dir / "person_safe_time_anchor.parquet", index=False, compression="zstd")

    lower = int(config["phase1_5"]["historical_year_lower_bound"])
    upper = int(config["phase1_5"]["historical_year_upper_bound"])
    sentinels = [int(value) for value in config["phase1_5"]["year_sentinels"]]
    coverage_rows = [coverage_row(people, "all", "Global", sentinels, lower, upper)]
    for dynasty in MAJOR_DYNASTIES:
        coverage_rows.append(coverage_row(people[people["dynasty"].eq(dynasty)], "dynasty", dynasty, sentinels, lower, upper))
    coverage_rows.append(coverage_row(people[people["target_entry_v1"].eq(1)], "target", "ENTRY positive", sentinels, lower, upper))
    coverage_rows.append(coverage_row(people[people["target_entry_v1"].eq(0)], "target", "ENTRY negative", sentinels, lower, upper))
    coverage = pd.DataFrame(coverage_rows)
    coverage.to_csv(tables_dir / "time_anchor_coverage.csv", index=False)

    class_summary = people.groupby("index_year_leakage_class").size().sort_values(ascending=False)
    unsafe_entry_types = provenance[(provenance["uses_entry_information"]) & (provenance["n_people"] > 0)]
    source_present = int(pd.to_numeric(people["index_year_source_id"], errors="coerce").fillna(0).ne(0).sum())
    document = [
        "# Index-year provenance audit",
        "",
        "The real schema is `BIOG_MAIN.c_index_year`, `c_index_year_type_code`, and `c_index_year_source_id`, decoded by `INDEXYEAR_TYPE_CODES`. Observed type values include official two-character codes and concatenated chains such as `2912` and `0512`; every observed chain is parsed component by component.",
        "",
        "Only exact provenance `01` (directly based on the focal person's birth year) is classified SAFE. UNKNOWN is never promoted to SAFE. Kin/recursive chains without explicit career outcomes are CONDITIONAL; any chain using examinations/entry, death, or descendant information is UNSAFE.",
        "",
        "## Person-level classification",
        "",
        markdown_table(["class", "people", "share"], ([name, value, f"{value / len(people):.2%}"] for name, value in class_summary.items())),
        "",
        f"`c_index_year_source_id` is nonzero for **{source_present:,}** people. Match counts to `BIOG_MAIN` are reported per provenance value; it is an upstream source-person identifier, not a calendar year.",
        "",
        "## Provenance explicitly dependent on ENTRY information",
        "",
        markdown_table(
            ["observed code", "components", "description", "people", "ENTRY positives", "class"],
            ([row.index_year_type_code or "[blank]", row.parsed_components, row.description_en, row.n_people, row.n_entry_positive, row.safe_for_pre_entry_model] for row in unsafe_entry_types.head(30).itertuples()),
        ),
        "",
        "Official components `05`/`06`/`07`/`08`/`09`/`10` use jinshi, juren or xiucai years (including a husband's examination year). This creates the path `ENTRY information → index_year → predict ENTRY` and is direct derived-target leakage.",
        "",
        "The safe person-level field is written separately as `safe_index_year`; raw `index_year` is preserved. Invalid year sentinels and values outside the configured historical range are never copied into the safe field.",
        "",
    ]
    atomic_write_text(audit_dir / "index_year_provenance.md", "\n".join(document))
    logger.info("Index provenance complete: %d observed codes/chains; safe anchor people=%d", len(provenance), int(people["safe_index_year_available"].sum()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

