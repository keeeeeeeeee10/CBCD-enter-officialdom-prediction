#!/usr/bin/env python3
"""Classify CBDB kin codes and build a direction-preserving deduplicated edge table."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.cleaning import clean_person_identifier
from src.config import configured_path, load_config
from src.db import connect_readonly
from src.utils import atomic_write_text, markdown_table, setup_logging


UNKNOWN_STEP = 90
NON_BLOOD_MARKERS = ("^", "*", "°", "#", "%")
NON_BLOOD_TEXT = (
    "adopt", "step", "heir", "nominal", "not biolog", "betroth",
    "養", "嗣", "繼", "非親", "許配", "聘",
)


def normalise_relation(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return text.replace("–", "-").replace("—", "-").replace("−", "-")


def classify_kin_code(row: pd.Series) -> dict[str, object]:
    code = int(row["kin_code"])
    up = int(row["upstep"])
    down = int(row["downstep"])
    marriage = int(row["marstep"])
    collateral = int(row["colstep"])
    relation = normalise_relation(row["relation_code"])
    simplified = normalise_relation(row["relation_simplified"])
    labels = " ".join(
        str(row.get(column, "") or "")
        for column in ("relation_zh", "relation_en")
    ).lower()

    invalid_steps = any(value < 0 or value >= UNKNOWN_STEP for value in (up, down, marriage, collateral))
    if code <= 0 or invalid_steps or relation in {"", "U", "ZZZZZZZ", "[missing data]"}:
        generation_class = "unknown"
        reason = "Sentinel/unmapped code or unknown direction step in official KINSHIP_CODES."
    elif marriage > 0 and up == 0 and down == 0 and collateral == 0:
        generation_class = "spouse"
        reason = "Official marriage step with no generational/collateral displacement."
    elif marriage > 0:
        generation_class = "affinal"
        reason = "Official c_marstep identifies an affinal relation."
    elif up > down:
        generation_class = "parent_generation" if up - down == 1 else "ancestor"
        reason = "Official upward/downward steps place the relative in an older generation."
    elif down > up:
        generation_class = "descendant"
        reason = "Official upward/downward steps place the relative in a younger generation."
    elif collateral > 0 or up == down:
        generation_class = "same_generation"
        reason = "Balanced generation steps/collateral step identify a same-generation relation."
    else:
        generation_class = "other"
        reason = "Official direction fields do not map cleanly to the frozen generation classes."

    if relation == "F":
        specific = "father"
    elif relation == "M":
        specific = "mother"
    elif relation == "FF":
        specific = "paternal_grandfather"
    elif relation == "FM":
        specific = "paternal_grandmother"
    elif relation == "MF":
        specific = "maternal_grandfather"
    elif relation == "MM":
        specific = "maternal_grandmother"
    elif generation_class == "same_generation" and simplified in {"B", "Z"}:
        if "+" in relation or relation in {"B1", "Z1"}:
            specific = "older_sibling"
        elif "-" in relation or relation in {"By", "Zy"}:
            specific = "younger_sibling"
        else:
            specific = "sibling_age_unknown"
    elif generation_class == "descendant" and up == 0 and down == 1 and collateral == 0 and marriage == 0 and simplified == "S":
        specific = "son"
    elif generation_class == "descendant" and up == 0 and down == 1 and collateral == 0 and marriage == 0 and simplified == "D":
        specific = "daughter"
    elif generation_class == "spouse" and (relation.startswith("H") or simplified == "H"):
        specific = "husband"
    elif generation_class == "spouse" and (relation.startswith("W") or simplified == "W"):
        specific = "wife"
    elif generation_class == "spouse" and relation == "C":
        specific = "concubine"
    else:
        specific = generation_class

    explicitly_non_blood = any(marker in relation for marker in NON_BLOOD_MARKERS) or any(
        token in labels for token in NON_BLOOD_TEXT
    )
    direct_lineal = specific in {
        "father", "mother", "paternal_grandfather", "paternal_grandmother",
        "maternal_grandfather", "maternal_grandmother", "son", "daughter",
    }
    core_sibling = specific in {"older_sibling", "younger_sibling", "sibling_age_unknown"}
    # The official half-sibling symbol ½ is allowed; step/adoptive markers are not.
    is_blood_core = bool(marriage == 0 and not explicitly_non_blood and (direct_lineal or core_sibling))
    is_affinal = bool(generation_class in {"spouse", "affinal"})
    return {
        "generation_class": generation_class,
        "specific_relation": specific,
        "is_blood_core": is_blood_core,
        "is_affinal": is_affinal,
        "classification_reason": reason,
    }


def atomic_to_csv(frame: pd.DataFrame, path: Path) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, path)


def main() -> int:
    config = load_config()
    database = configured_path(config, "database", "working_db")
    interim = configured_path(config, "paths", "interim")
    tables = configured_path(config, "paths", "tables")
    audit = configured_path(config, "paths", "audit_docs")
    logger = setup_logging(
        "prepare_family_graph",
        configured_path(config, "paths", "logs") / "prepare_family_graph.log",
    )

    with connect_readonly(database, config["database"]["busy_timeout_ms"]) as connection:
        codes = pd.read_sql_query(
            """
            SELECT k.c_kincode AS kin_code,
                   k.c_kin_pair1 AS kin_pair1,
                   k.c_kin_pair2 AS kin_pair2,
                   k.c_kinrel_chn AS relation_zh,
                   k.c_kinrel AS relation_code,
                   k.c_kinrel_alt AS relation_en,
                   k.c_kinrel_simplified AS relation_simplified,
                   k.c_upstep AS upstep,
                   k.c_dwnstep AS downstep,
                   k.c_marstep AS marstep,
                   k.c_colstep AS colstep,
                   COUNT(d.c_personid) AS n_records
            FROM KINSHIP_CODES k
            LEFT JOIN KIN_DATA d ON d.c_kin_code=k.c_kincode
            GROUP BY k.c_kincode
            ORDER BY k.c_kincode
            """,
            connection,
        )
        raw_edges = pd.read_sql_query(
            """
            SELECT c_personid AS person_id, c_kin_id AS kin_id, c_kin_code AS kin_code
            FROM KIN_DATA
            """,
            connection,
        )
        valid_people = pd.read_sql_query(
            "SELECT c_personid AS person_id FROM BIOG_MAIN ORDER BY c_personid",
            connection,
        )["person_id"].astype("int64")

    classifications = pd.DataFrame([classify_kin_code(row) for _, row in codes.iterrows()])
    taxonomy = pd.concat([codes.reset_index(drop=True), classifications], axis=1)
    atomic_to_csv(taxonomy, tables / "kinship_generation_taxonomy.csv")

    n_raw = len(raw_edges)
    raw_edges["person_id"] = clean_person_identifier(raw_edges["person_id"])
    raw_edges["kin_id"] = clean_person_identifier(raw_edges["kin_id"])
    clean = raw_edges.dropna(subset=["person_id", "kin_id"]).copy()
    clean["person_id"] = clean["person_id"].astype("int64")
    clean["kin_id"] = clean["kin_id"].astype("int64")
    clean = clean[clean["person_id"].ne(clean["kin_id"])]
    known = set(valid_people.tolist())
    known_mask = clean["person_id"].isin(known) & clean["kin_id"].isin(known)
    n_unknown_endpoint = int((~known_mask).sum())
    clean = clean.loc[known_mask].copy()
    clean = clean.merge(taxonomy, on="kin_code", how="left", validate="many_to_one")
    if clean["generation_class"].isna().any():
        missing_codes = sorted(clean.loc[clean["generation_class"].isna(), "kin_code"].unique())
        raise RuntimeError(f"KIN_DATA has unmapped kin codes: {missing_codes}")

    low = np.minimum(clean["person_id"].to_numpy(), clean["kin_id"].to_numpy())
    high = np.maximum(clean["person_id"].to_numpy(), clean["kin_id"].to_numpy())
    clean["canonical_pair_id"] = pd.Series(low.astype(str)) + "-" + pd.Series(high.astype(str))
    clean["canonical_relation_class"] = np.where(
        clean["is_blood_core"],
        "blood_core",
        np.where(clean["is_affinal"], clean["generation_class"], clean["generation_class"]),
    )
    clean["direction_from_lower_id"] = clean["person_id"].eq(low)
    specific_priority = {
        "father": 0, "mother": 1, "son": 2, "daughter": 3,
        "paternal_grandfather": 4, "paternal_grandmother": 5,
        "maternal_grandfather": 6, "maternal_grandmother": 7,
        "older_sibling": 8, "younger_sibling": 9, "sibling_age_unknown": 10,
    }
    clean["relation_priority"] = clean["specific_relation"].map(specific_priority).fillna(50).astype(int)
    # One representative record per unordered pair removes reciprocal/mirror rows.
    # The selected original direction and official code/steps remain in the output.
    group_columns = ["canonical_pair_id"]
    stats = clean.groupby(group_columns, sort=False).agg(
        n_source_rows=("kin_code", "size"),
        n_source_directions=("person_id", "nunique"),
    ).reset_index()
    chosen = (
        clean.sort_values(
            group_columns + ["is_blood_core", "is_affinal", "relation_priority", "direction_from_lower_id", "kin_code"],
            ascending=[True, False, True, True, False, True],
            kind="mergesort",
        )
        .drop_duplicates(group_columns, keep="first")
        .merge(stats, on=group_columns, how="left", validate="one_to_one")
    )
    chosen["reciprocal_observed"] = chosen["n_source_directions"].gt(1)
    output_columns = [
        "person_id", "kin_id", "kin_code", "generation_class", "specific_relation",
        "is_blood_core", "is_affinal", "canonical_pair_id", "canonical_relation_class",
        "relation_code", "relation_zh", "relation_en",
        "upstep", "downstep", "marstep", "colstep", "direction_from_lower_id",
        "n_source_rows", "reciprocal_observed",
    ]
    chosen[output_columns].to_parquet(
        interim / "family_edges_core.parquet", index=False, compression="zstd"
    )

    category_summary = taxonomy.groupby("generation_class", dropna=False).agg(
        n_codes=("kin_code", "size"), n_records=("n_records", "sum")
    ).reset_index().sort_values("n_records", ascending=False)
    specific = taxonomy[taxonomy["specific_relation"].isin({
        "father", "mother", "paternal_grandfather", "paternal_grandmother",
        "maternal_grandfather", "maternal_grandmother", "older_sibling",
        "younger_sibling", "son", "daughter",
    })].groupby("specific_relation").agg(
        n_codes=("kin_code", "size"), n_records=("n_records", "sum")
    ).reset_index().sort_values("n_records", ascending=False)
    core_edges = int(chosen["is_blood_core"].sum())
    document = [
        "# Kinship generation and core-family policy",
        "",
        "The real database tables are `KINSHIP_CODES` (488 official codes) and `KIN_DATA`. Classification first uses `c_upstep`, `c_dwnstep`, `c_marstep`, and `c_colstep`; standardized official relation symbols identify the requested specific relations. Chinese/English labels are secondary evidence, mainly for conservative non-blood exclusions.",
        "",
        "## Generation taxonomy",
        "",
        markdown_table(
            ["class", "official codes", "KIN_DATA records"],
            category_summary.itertuples(index=False, name=None),
        ),
        "",
        "## Specifically identified relations",
        "",
        markdown_table(
            ["relation", "official codes", "KIN_DATA records"],
            specific.itertuples(index=False, name=None),
        ),
        "",
        "## Frozen core graph rule",
        "",
        "Core blood-family edges include direct biological parent/child, grandparent/grandchild, and identifiable full/half sibling relations. Official step/adoptive/betrothed markers, all marriage/affinal relations, distant kin, unknown `99/100` direction steps, invalid identifiers, self-loops, and endpoints absent from `BIOG_MAIN` are excluded from components.",
        "",
        f"The normalized edge table retains **{len(chosen):,}** unique unordered person pairs, of which **{core_edges:,}** are core blood-family edges. It excluded **{n_raw - len(raw_edges.dropna()):,}** rows during identifier cleaning before endpoint/self-loop checks and **{n_unknown_endpoint:,}** rows with an endpoint outside the modeling population. Reciprocal source rows are collapsed while the selected original direction, code, and official step fields are retained.",
        "",
        "Descendants are classified but excluded from Strict Temporal Family features in the first specification. Same-generation relatives remain CONDITIONAL. Spouse and affinal relations never enter the first core-family component graph.",
        "",
    ]
    atomic_write_text(audit / "kinship_generation_policy.md", "\n".join(document))
    logger.info(
        "Family edges prepared: raw=%d canonical=%d core=%d unknown_endpoint=%d",
        n_raw, len(chosen), core_edges, n_unknown_endpoint,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
