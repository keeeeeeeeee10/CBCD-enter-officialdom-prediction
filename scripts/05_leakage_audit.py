#!/usr/bin/env python3
"""Classify direct, post-entry, temporal, and safer-background feature sources."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import configured_path, load_config
from src.db import connect_readonly, scalar
from src.utils import atomic_write_text, markdown_table, setup_logging


CLASSIFICATION = [
    ("ENTRY_DATA", "table presence / entry_code / entry counts", 0, "Defines Target V1 and directly encodes entry mode.", False, False),
    ("ENTRY_CODES / ENTRY_TYPES / View_EntryData", "entry labels and enriched entry rows", 0, "Code labels are a decoded form of the direct target source.", False, False),
    ("person_base_v0", "n_entry_records", 0, "Count of records used to define the target.", False, False),
    ("POSTING_DATA", "has_posting_record / n_posting_records", 1, "A person's appointments normally reveal realized office holding.", True, False),
    ("POSTED_TO_OFFICE_DATA", "office IDs, dates, counts, ranks", 1, "Explicit realized office postings are strong post-entry outcome leakage.", True, False),
    ("POSTED_TO_ADDR_DATA", "posting locations and counts", 1, "Locations are attached to realized postings.", True, False),
    ("OFFICE_CODES / OFFICE_CATEGORIES", "office name, hierarchy, category", 1, "Decodes the person's realized office outcome.", True, False),
    ("View_PostingOfficeData / View_PostingAddrData", "enriched posting and office features", 1, "Denormalized views expose realized office and posting outcomes.", True, False),
    ("STATUS_DATA + STATUS_CODES", "explicit official/office/jinshi/government statuses", 1, "Several observed status labels directly identify office holding or examination outcomes.", True, False),
    ("ASSOC_DATA", "association presence, degree, type, dates", 2, "Relationships may have formed after entry and are not uniformly dated.", True, False),
    ("BIOG_INST_DATA", "institution roles and counts", 2, "Institutional affiliations may postdate entry or reflect official responsibility.", True, False),
    ("BIOG_TEXT_DATA / BIOG_SOURCE_DATA", "texts, roles, source/record counts", 2, "Later-life production and documentation intensity can follow official success.", True, False),
    ("STATUS_DATA", "non-explicit later-life status categories", 2, "Status observations can occur after entry; temporal anchoring is required.", True, False),
    ("BIOG_ADDR_DATA", "residence/migration/burial/death addresses", 2, "Some address types occur after entry; use only pre-entry-safe types and dates.", True, False),
    ("BIOG_MAIN", "gender", 3, "Substantive personal background field; retain unknown as missing.", True, True),
    ("BIOG_MAIN", "birth_year", 3, "Allowed only after field-aware sentinel/range validation.", True, True),
    ("BIOG_MAIN", "dynasty", 3, "Historical regime baseline; preserve missing/unknown category.", True, True),
    ("BIOG_MAIN", "raw_index_year", 1, "Some index years are algorithmically derived from ENTRY_DATA, examination years, death years, relatives or later-life events. Raw index year therefore mixes safe and unsafe provenance and cannot be used directly. Never use directly in a leakage-controlled / pre-entry model.", True, False),
    ("person_safe_time_anchor", "safe_index_year", 3, "Only provenance 01 (Based on Birth Year), after year validation.", True, True),
    ("BIOG_MAIN", "conditional_index_year", 2, "Kin/recursive provenance without explicit outcome evidence; sensitivity analysis only.", True, "sensitivity_only"),
    ("BIOG_MAIN", "unsafe_index_year", 1, "Derived from ENTRY/examination, death, descendants, or other later-life information.", True, False),
    ("BIOG_MAIN", "unknown_index_year", 1, "Unknown/unparsed provenance is never promoted to SAFE.", True, False),
    ("BIOG_MAIN + BIOG_ADDR_DATA", "index/basic/natal/ancestral geographic background", 3, "Background geography is usable when address semantics and timing precede entry.", True, True),
    ("KIN_DATA + KINSHIP_CODES", "kin structure and kin type", 3, "Family structure is background-like, but relatives' later outcomes require temporal controls.", True, True),
    ("relatives' ENTRY/POSTING data", "parent/grandparent political capital", 3, "Usable only if the relative outcome predates the focal person's entry/risk time.", True, "conditional"),
]


def main() -> int:
    config = load_config()
    tables_dir = configured_path(config, "paths", "tables")
    audit_dir = configured_path(config, "paths", "audit_docs")
    logger = setup_logging("leakage", configured_path(config, "paths", "logs") / "leakage_audit.log")
    database = configured_path(config, "database", "working_db")

    classification = pd.DataFrame(
        CLASSIFICATION,
        columns=["table", "feature_group", "leakage_level", "reason", "allowed_full_model", "allowed_pre_entry_model"],
    )
    classification["leakage_class"] = classification["leakage_level"].map({
        0: "DIRECT_TARGET", 1: "UNSAFE", 2: "CONDITIONAL", 3: "SAFE_OR_CONDITIONAL",
    })
    classification.loc[classification["feature_group"].eq("gender"), "leakage_class"] = "SAFE"
    classification.loc[classification["feature_group"].eq("birth_year"), "leakage_class"] = "SAFE"
    classification.loc[classification["feature_group"].eq("dynasty"), "leakage_class"] = "SAFE_BACKGROUND_REGIME"
    classification.loc[classification["feature_group"].eq("raw_index_year"), "leakage_class"] = "UNSAFE_AS_RAW_FEATURE"
    classification.loc[classification["feature_group"].eq("safe_index_year"), "leakage_class"] = "SAFE"
    classification.loc[classification["feature_group"].eq("unknown_index_year"), "leakage_class"] = "UNKNOWN"
    classification.to_csv(tables_dir / "feature_leakage_classification.csv", index=False)

    status_pattern = """
        lower(COALESCE(c.c_status_desc,'')) LIKE '%official%'
        OR lower(COALESCE(c.c_status_desc,'')) LIKE '%office%'
        OR lower(COALESCE(c.c_status_desc,'')) LIKE '%jinshi%'
        OR lower(COALESCE(c.c_status_desc,'')) LIKE '%government%'
        OR COALESCE(c.c_status_desc_chn,'') LIKE '%官%'
        OR COALESCE(c.c_status_desc_chn,'') LIKE '%進士%'
        OR COALESCE(c.c_status_desc_chn,'') LIKE '%进士%'
    """
    with connect_readonly(database, config["database"]["busy_timeout_ms"]) as connection:
        suspicious_statuses = pd.read_sql_query(
            f"""
            SELECT s.c_status_code AS status_code,
                   c.c_status_desc AS status_name_en,
                   c.c_status_desc_chn AS status_name_zh,
                   COUNT(*) AS record_count,
                   COUNT(DISTINCT s.c_personid) AS person_count
            FROM STATUS_DATA s LEFT JOIN STATUS_CODES c ON c.c_status_code=s.c_status_code
            WHERE {status_pattern}
            GROUP BY s.c_status_code,c.c_status_desc,c.c_status_desc_chn
            ORDER BY record_count DESC
            """,
            connection,
        )
        suspicious_statuses.to_csv(tables_dir / "suspicious_status_codes.csv", index=False)

        evidence_queries = {
            "entry_people": "SELECT COUNT(DISTINCT c_personid) FROM ENTRY_DATA WHERE c_personid IS NOT NULL",
            "posting_people": "SELECT COUNT(DISTINCT c_personid) FROM POSTING_DATA WHERE c_personid IS NOT NULL",
            "posted_to_office_people": "SELECT COUNT(DISTINCT c_personid) FROM POSTED_TO_OFFICE_DATA WHERE c_personid IS NOT NULL",
            "explicit_status_people": f"SELECT COUNT(DISTINCT s.c_personid) FROM STATUS_DATA s LEFT JOIN STATUS_CODES c ON c.c_status_code=s.c_status_code WHERE {status_pattern}",
            "entry_and_posting_people": """
                SELECT COUNT(*) FROM
                  (SELECT DISTINCT c_personid FROM ENTRY_DATA WHERE c_personid IS NOT NULL) e
                INNER JOIN
                  (SELECT DISTINCT c_personid FROM POSTING_DATA WHERE c_personid IS NOT NULL) p
                ON p.c_personid=e.c_personid
            """,
            "entry_and_explicit_status_people": f"""
                SELECT COUNT(*) FROM
                  (SELECT DISTINCT c_personid FROM ENTRY_DATA WHERE c_personid IS NOT NULL) e
                INNER JOIN
                  (SELECT DISTINCT s.c_personid FROM STATUS_DATA s
                   LEFT JOIN STATUS_CODES c ON c.c_status_code=s.c_status_code
                   WHERE {status_pattern}) suspicious
                ON suspicious.c_personid=e.c_personid
            """,
        }
        evidence = {name: int(scalar(connection, query) or 0) for name, query in evidence_queries.items()}

    status_rows = suspicious_statuses.head(30).itertuples(index=False, name=None)
    document = [
        "# Feature leakage audit",
        "",
        "The historical research target is presence in current CBDB `ENTRY_DATA`, not a cleanly timed intervention. "
        "This audit separates record-completeness prediction (Model A) from a temporally safer background model (Model B).",
        "",
        "## Model A — full information",
        "",
        "May use post-entry evidence as an upper-bound/record-completeness signal, but never `ENTRY_DATA`, decoded entry codes, or `n_entry_records`. "
        "Its performance must not be interpreted causally or as genuine ex-ante prediction.",
        "",
        "## Model B — leakage-controlled / pre-entry",
        "",
        "Uses only information demonstrably available before the person's entry/risk time. Personal postings, offices, explicit official outcomes, and unanchored later-life relations, statuses, institutions, and writings are excluded.",
        "",
        "## Levels",
        "",
        "- **Level 0 — Direct target:** the target table and decoded/count variants; prohibited everywhere.",
        "- **Level 1 — Strong post-entry leakage:** realized offices/postings and explicit official outcomes; Model A only.",
        "- **Level 2 — Potential temporal leakage:** associations, institutions, statuses, texts, and later addresses without reliable pre-entry timing.",
        "- **Level 3 — Safer background:** individually audited personal, family, and pre-entry geographic attributes, still subject to recording bias and temporal checks. Raw index year is explicitly excluded.",
        "",
        "## Classification",
        "",
        markdown_table(
            ["table/source", "feature group", "level", "reason", "full", "pre-entry", "class"],
            classification.itertuples(index=False, name=None),
        ),
        "",
        "## Observed overlap evidence",
        "",
        markdown_table(["metric", "people"], evidence.items()),
        "",
        "High overlap does not prove leakage by itself, but the semantics and timing of postings/offices make them outcome information. The overlap quantifies how strongly these sources could shortcut Target V1.",
        "",
        "## STATUS_DATA terms requiring exclusion or review",
        "",
        markdown_table(["code", "English", "中文", "records", "people"], status_rows),
        "",
        "The text search is deliberately inclusive (`official`, `office`, `jinshi`, `government`, 官, 進士/进士). False positives and statuses such as refusal/died-before-office must be reviewed rather than automatically treated as positive outcomes. In the strict pre-entry model, all explicitly outcome-bearing status fields remain excluded.",
        "",
        "## Frozen index-year rule",
        "",
        "Raw `BIOG_MAIN.c_index_year` mixes SAFE, CONDITIONAL, UNSAFE, and UNKNOWN provenance. Some index years are algorithmically derived from `ENTRY_DATA`, examination years, death years, relatives, or later-life events. Raw index year therefore cannot be used directly. **Never use directly** in a leakage-controlled/pre-entry model. Only separately materialized `safe_index_year` is allowed; `conditional_index_year` is sensitivity-only, while `unsafe_index_year` and `unknown_index_year` are denied.",
        "",
        "This boundary is enforced by `configs/feature_policy.yaml` and `src.feature_policy.validate_feature_set`; violations raise an exception.",
        "",
    ]
    atomic_write_text(audit_dir / "leakage_audit.md", "\n".join(document))
    logger.info("Leakage classification written: %d feature groups; %d suspicious status codes", len(classification), len(suspicious_statuses))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
