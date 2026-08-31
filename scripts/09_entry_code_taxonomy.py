#!/usr/bin/env python3
"""Build an evidence-based ENTRY code taxonomy and non-final V2 candidate targets."""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import configured_path, load_config
from src.db import connect_readonly
from src.phase15 import safe_divide, year_predicate
from src.utils import atomic_write_text, markdown_table, setup_logging


BROAD_CATEGORIES = {
    "exam_degree",
    "recommendation",
    "hereditary_or_yin_privilege",
    "military_entry",
    "purchase_or_donation",
    "direct_appointment",
    "other_clear_entry",
}

TARGET_DISPLAY = {
    "V1": (
        "ENTRY record presence",
        "是否存在 ENTRY_DATA 记录",
        "Presence of at least one current CBDB ENTRY_DATA record; not proof of office holding.",
    ),
    "V2a": (
        "Broad formal entry/credential target",
        "广义正式入仕途径/资格记录",
        "Broad taxonomy-based formal entry route or credential candidate.",
    ),
    "V2b": (
        "High-confidence formal entry/credential target",
        "高置信度正式入仕途径/资格记录",
        "High-confidence formal entry route or credential candidate; not equivalent to a posting.",
    ),
    "posting": (
        "Recorded office-holding / posting outcome",
        "是否存在任官记录",
        "Auxiliary presence of a valid CBDB posting record; incomplete and not ground truth.",
    ),
}


def joined_text(name_en: object, name_zh: object) -> str:
    return f"{name_en or ''} {name_zh or ''}".lower()


def classify_code(type_codes: list[str], name_en: object, name_zh: object) -> dict[str, object]:
    text = joined_text(name_en, name_zh)
    type_set = set(type_codes)
    failed_terms = ("failed", "failure", "not degree", "求官不得", "不第")
    unknown_terms = ("not available", "missing data", "unknown", "to be deleted", "臨時保留", "未知")
    title_only_terms = ("honorific title", "investiture", "empress", "heir apparent", "emperor or king", "personal declaration", "religion", "ordination", "baptism", "monk", "lama")

    if "15" in type_set or any(term in text for term in failed_terms):
        category, confidence = "failed_entry", "NONE"
        reason = "Official entry type or description explicitly records an unsuccessful pursuit/examination."
    elif not type_codes or type_set & {"00", "99"} or any(term in text for term in unknown_terms):
        category, confidence = "unknown", "NONE"
        reason = "Official type/description is unknown, temporary, deprecated, or unmapped."
    elif any(term in text for term in title_only_terms) and "office granted" not in text:
        category, confidence = "ambiguous", "LOW"
        reason = "Palace, honorific, dynastic, or religious status does not by itself establish bureaucratic entry."
    elif any(code == "040103" or code.startswith("05") for code in type_set):
        category, confidence = "school_or_student_status", "LOW"
        reason = "Official taxonomy identifies a school, student, licentiate, academy, or tribute-student status; this is not automatically an appointment."
    elif any(code.startswith("04") for code in type_set):
        category = "exam_degree"
        success_terms = ("jinshi", "juren", "graduate", "passed", "degree granted", "進士", "舉人", "及第", "出身")
        confidence = "HIGH" if any(term in text for term in success_terms) else "MEDIUM"
        reason = "Official taxonomy places the code in an examination branch; confidence is high only when the description explicitly signals a passed degree/graduate outcome."
    elif "08" in type_set:
        category, confidence = "recommendation", "HIGH"
        reason = "Official taxonomy identifies recommendation as the entry route."
    elif type_set & {"02", "06"}:
        category = "hereditary_or_yin_privilege"
        explicit = any(term in text for term in ("yin privilege", "inheritance", "rank or office", "蔭", "荫", "世襲", "補官"))
        confidence = "HIGH" if explicit and "student" not in text and "生" not in str(name_zh or "") else "MEDIUM"
        reason = "Official taxonomy identifies kinship/yin privilege; strict inclusion requires explicit office/rank succession rather than clan or student status alone."
    elif "09" in type_set:
        category, confidence = "military_entry", "HIGH"
        reason = "Official taxonomy identifies military merit or military appointment as the route."
    elif "12" in type_set:
        category, confidence = "purchase_or_donation", "HIGH"
        reason = "Official taxonomy and description identify purchase/donation as the route."
    elif "07" in type_set:
        category, confidence = "direct_appointment", "HIGH"
        reason = "Official taxonomy identifies summons/recruitment; the description records direct recruitment or appointment."
    elif type_set & {"10", "11", "13", "16"}:
        explicit_office = any(term in text for term in ("office", "appointed", "appointment", "recruit", "補官", "授官", "除授", "幕僚"))
        if explicit_office:
            category, confidence = "direct_appointment", "HIGH"
            reason = "Specialized/grace/surrender route has description-level evidence of an office or appointment."
        elif len(type_set - {"90"}) == 1:
            category, confidence = "other_clear_entry", "MEDIUM"
            reason = "Official taxonomy records another institutional route, but description does not independently confirm appointment."
        else:
            category, confidence = "ambiguous", "LOW"
            reason = "Multiple official type mappings conflict or provide insufficient appointment semantics."
    elif "90" in type_set:
        military_terms = ("soldier", "military", "guardsman", "bannerman", "trooper", "militia", "軍", "兵", "護軍", "前鋒", "馬甲")
        office_terms = ("office", "official", "clerical", "secretary", "appointed", "promotion", "補官", "授官", "出職", "幕僚", "中書")
        if any(term in text for term in military_terms):
            category, confidence = "military_entry", "MEDIUM"
            reason = "Description indicates a military role, but the broad Other branch does not always prove a bureaucratic appointment."
        elif any(term in text for term in office_terms):
            category, confidence = "direct_appointment", "HIGH"
            reason = "Description within the Other branch explicitly indicates office, appointment, or promotion."
        else:
            category, confidence = "ambiguous", "LOW"
            reason = "The broad Other branch and description do not establish a uniform government-entry event."
    else:
        category, confidence = "ambiguous", "LOW"
        reason = "Official type is semantically heterogeneous or not sufficient to infer government entry."

    include_v2a = category in BROAD_CATEGORIES
    include_v2b = category in BROAD_CATEGORIES and confidence == "HIGH"
    manual = category in {"ambiguous", "unknown"} or category == "school_or_student_status" or confidence in {"LOW", "MEDIUM"}
    return {
        "semantic_category": category,
        "government_entry_confidence": confidence,
        "include_target_v2_candidate": bool(include_v2a),
        "include_target_v2b_candidate": bool(include_v2b),
        "reason": reason,
        "manual_review_needed": bool(manual),
    }


def in_clause(values: list[int]) -> str:
    return ",".join(str(int(value)) for value in sorted(values)) if values else "NULL"


def main() -> int:
    config = load_config()
    tables_dir = configured_path(config, "paths", "tables")
    interim_dir = configured_path(config, "paths", "interim")
    audit_dir = configured_path(config, "paths", "audit_docs")
    logger = setup_logging("entry_taxonomy", configured_path(config, "paths", "logs") / "entry_code_taxonomy.log")
    database = configured_path(config, "database", "working_db")

    with connect_readonly(database, config["database"]["busy_timeout_ms"]) as connection:
        logger.info("Inspecting real ENTRY code schemas")
        codes = pd.read_sql_query("SELECT c_entry_code AS entry_code, c_entry_desc AS entry_name_en, c_entry_desc_chn AS entry_name_zh FROM ENTRY_CODES ORDER BY c_entry_code", connection)
        types = pd.read_sql_query("SELECT c_entry_type AS entry_type_code, c_entry_type_desc AS entry_type_name_en, c_entry_type_desc_chn AS entry_type_name_zh FROM ENTRY_TYPES", connection)
        relations = pd.read_sql_query("SELECT c_entry_code AS entry_code, c_entry_type AS entry_type_code FROM ENTRY_CODE_TYPE_REL", connection)
        valid_year = year_predicate("c_year", config)
        stats = pd.read_sql_query(
            f"""
            SELECT c_entry_code AS entry_code, COUNT(*) AS n_records,
                   COUNT(DISTINCT c_personid) AS n_people,
                   MIN(CASE WHEN {valid_year} THEN c_year END) AS first_year,
                   MAX(CASE WHEN {valid_year} THEN c_year END) AS last_year,
                   SUM(CASE WHEN {valid_year} THEN 1 ELSE 0 END) AS n_valid_year_records
            FROM ENTRY_DATA GROUP BY c_entry_code
            """,
            connection,
        )

    relation_labels = relations.merge(types, on="entry_type_code", how="left")
    type_map: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in relation_labels.itertuples(index=False):
        type_map[int(row.entry_code)].append({
            "code": str(row.entry_type_code),
            "en": str(row.entry_type_name_en),
            "zh": str(row.entry_type_name_zh),
        })

    inventory = codes.merge(stats, on="entry_code", how="left")
    for column in ("n_records", "n_people", "n_valid_year_records"):
        inventory[column] = inventory[column].fillna(0).astype("int64")
    inventory_rows = []
    for row in inventory.itertuples(index=False):
        mappings = sorted(type_map.get(int(row.entry_code), []), key=lambda item: item["code"])
        type_codes = [item["code"] for item in mappings]
        classification = classify_code(type_codes, row.entry_name_en, row.entry_name_zh)
        inventory_rows.append({
            "entry_code": int(row.entry_code),
            "entry_type_code": ";".join(type_codes),
            "entry_type_name": "; ".join(item["en"] for item in mappings),
            "entry_type_name_zh": "; ".join(item["zh"] for item in mappings),
            "entry_name_zh": row.entry_name_zh,
            "entry_name_en": row.entry_name_en,
            "n_records": int(row.n_records),
            "n_people": int(row.n_people),
            "first_year": row.first_year,
            "last_year": row.last_year,
            "n_valid_year_records": int(row.n_valid_year_records),
            **classification,
        })
    taxonomy = pd.DataFrame(inventory_rows).sort_values("entry_code")
    taxonomy["target_v2a_semantic_name"] = TARGET_DISPLAY["V2a"][0]
    taxonomy["target_v2b_semantic_name"] = TARGET_DISPLAY["V2b"][0]
    inventory_columns = [
        "entry_code", "entry_type_code", "entry_type_name", "entry_type_name_zh", "entry_name_zh", "entry_name_en",
        "n_records", "n_people", "first_year", "last_year", "n_valid_year_records",
    ]
    taxonomy[inventory_columns].to_csv(tables_dir / "entry_code_full_inventory.csv", index=False)
    taxonomy.to_csv(tables_dir / "target_v2_candidate_codes.csv", index=False)

    v2a_codes = taxonomy.loc[taxonomy["include_target_v2_candidate"], "entry_code"].astype(int).tolist()
    v2b_codes = taxonomy.loc[taxonomy["include_target_v2b_candidate"], "entry_code"].astype(int).tolist()
    with connect_readonly(database, config["database"]["busy_timeout_ms"]) as connection:
        targets = pd.read_sql_query(
            f"""
            WITH person_flags AS (
                SELECT c_personid,
                       1 AS target_entry_v1,
                       MAX(CASE WHEN c_entry_code IN ({in_clause(v2a_codes)}) THEN 1 ELSE 0 END) AS target_entry_v2a,
                       MAX(CASE WHEN c_entry_code IN ({in_clause(v2b_codes)}) THEN 1 ELSE 0 END) AS target_entry_v2b
                FROM ENTRY_DATA WHERE c_personid IS NOT NULL AND c_personid<>0 GROUP BY c_personid
            )
            SELECT b.c_personid AS person_id,
                   COALESCE(f.target_entry_v1,0) AS target_entry_v1,
                   COALESCE(f.target_entry_v2a,0) AS target_entry_v2a,
                   COALESCE(f.target_entry_v2b,0) AS target_entry_v2b
            FROM BIOG_MAIN b LEFT JOIN person_flags f ON f.c_personid=b.c_personid
            ORDER BY b.c_personid
            """,
            connection,
        )
    auxiliary = pd.read_parquet(interim_dir / "person_auxiliary_outcomes.parquet", columns=["person_id", "target_entry_v1", "target_posting"])
    targets = targets.merge(auxiliary, on=["person_id", "target_entry_v1"], how="left", validate="one_to_one")
    for column in ("target_entry_v1", "target_entry_v2a", "target_entry_v2b", "target_posting"):
        targets[column] = targets[column].fillna(0).astype("int8")
    targets.to_parquet(interim_dir / "person_targets_v1_v2.parquet", index=False, compression="zstd")

    comparison_rows = []
    v1 = targets["target_entry_v1"].eq(1)
    posting = targets["target_posting"].eq(1)
    for target_key, column in (("V1", "target_entry_v1"), ("V2a", "target_entry_v2a"), ("V2b", "target_entry_v2b"), ("posting", "target_posting")):
        mask = targets[column].eq(1)
        positives = int(mask.sum())
        with_v1 = int((mask & v1).sum())
        with_posting = int((mask & posting).sum())
        display_name, display_name_zh, description = TARGET_DISPLAY[target_key]
        comparison_rows.append({
            "target_key": target_key,
            "target": display_name,
            "display_name": display_name,
            "display_name_zh": display_name_zh,
            "description": description,
            "positive_count": positives,
            "positive_rate": safe_divide(positives, len(targets)),
            "overlap_with_v1_count": with_v1,
            "overlap_with_v1_rate_of_target": safe_divide(with_v1, positives),
            "overlap_with_posting_count": with_posting,
            "overlap_with_posting_rate_of_target": safe_divide(with_posting, positives),
            "jaccard_with_posting": safe_divide(with_posting, positives + int(posting.sum()) - with_posting),
        })
    comparison = pd.DataFrame(comparison_rows)
    comparison.to_csv(tables_dir / "target_definition_comparison.csv", index=False)

    used = taxonomy[taxonomy["n_records"] > 0].copy()
    category_summary = (
        used.groupby("semantic_category")
        .agg(n_used_codes=("entry_code", "size"), n_records=("n_records", "sum"), code_person_sum=("n_people", "sum"), n_manual_review=("manual_review_needed", "sum"))
        .sort_values("n_records", ascending=False)
        .reset_index()
    )
    top20 = used.sort_values("n_records", ascending=False).head(20)
    document = [
        "# ENTRY code taxonomy and Target V2 candidates",
        "",
        f"The official schema contains **{len(taxonomy)}** `ENTRY_CODES`; **{len(used)}** are used by `ENTRY_DATA`. Classifications use official Chinese/English descriptions and `ENTRY_CODE_TYPE_REL → ENTRY_TYPES`, never code number alone.",
        "",
        "## Semantic categories among used codes",
        "",
        markdown_table(
            ["category", "used codes", "records", "sum of per-code people", "manual-review codes"],
            category_summary.itertuples(index=False, name=None),
        ),
        "",
        "The per-code people column is not a unique category-person count because one person may have multiple codes. Person-level target counts are reported below.",
        "",
        "## Candidate policy",
        "",
        "- **V1:** any `ENTRY_DATA` record; unchanged.",
        "- **V2a — Broad formal entry/credential target:** exam degree, recommendation, hereditary/yin, military, purchase/donation, direct appointment, and other clear entry. School/student status is conservatively excluded pending manual review.",
        "- **V2b — High-confidence formal entry/credential target:** only V2a codes with HIGH semantic confidence. Examination codes require description-level evidence of passing/degree/graduate status. Credentials are not equivalent to actual posting; this remains a candidate, not the sole official target.",
        "- **Auxiliary Posting — Recorded office-holding / posting outcome:** also an incomplete historical record, not ground-truth verification of ENTRY_DATA. Posting overlap is diagnostic only.",
        "- Failed, ambiguous, unknown, honorific-only, palace/dynastic, religious, and unsupported school/student records are excluded from both candidates.",
        "",
        markdown_table(
            ["target", "positives", "rate", "overlap V1", "overlap posting", "posting overlap rate", "posting Jaccard"],
            ([row.display_name, row.positive_count, f"{row.positive_rate:.2%}", row.overlap_with_v1_count, row.overlap_with_posting_count, f"{row.overlap_with_posting_rate_of_target:.2%}", f"{row.jaccard_with_posting:.2%}"] for row in comparison.itertuples()),
        ),
        "",
        "## Twenty largest used codes",
        "",
        markdown_table(
            ["code", "English", "中文", "official type", "category", "confidence", "records", "people", "V2a", "V2b"],
            ([row.entry_code, row.entry_name_en, row.entry_name_zh, row.entry_type_code, row.semantic_category, row.government_entry_confidence, row.n_records, row.n_people, row.include_target_v2_candidate, row.include_target_v2b_candidate] for row in top20.itertuples()),
        ),
        "",
        "All LOW/MEDIUM, school/student, ambiguous, and unknown cases are explicitly marked for manual review in `target_v2_candidate_codes.csv`. These rules are reproducible hypotheses, not final historical adjudications.",
        "",
    ]
    atomic_write_text(audit_dir / "entry_code_taxonomy.md", "\n".join(document))
    logger.info("ENTRY taxonomy complete: official=%d used=%d V2a codes=%d V2b codes=%d", len(taxonomy), len(used), len(v2a_codes), len(v2b_codes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
