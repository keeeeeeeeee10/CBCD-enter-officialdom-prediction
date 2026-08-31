#!/usr/bin/env python3
"""Select conservative historical background addresses and build simple geography features."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.db import connect_readonly
from src.feature_builders import atomic_to_parquet, ensure_unique_people, load_yaml
from src.geography import assign_capitals, haversine_km
from src.utils import atomic_write_text, setup_logging


TYPE_PRIORITY = {
    1: 0,   # official Basic Affiliation / index address
    8: 1,   # birth address
    7: 2,   # household registration address
    16: 3,  # household address
    5: 4,   # ancestral address
    6: 5,   # actual residence
    14: 6,  # alternate basic affiliation
    13: 7,  # Qing banner background
}


def choose_primary_address(connection) -> tuple[pd.DataFrame, pd.DataFrame]:
    allowed = ",".join(map(str, TYPE_PRIORITY))
    relational = pd.read_sql_query(
        f"""
        SELECT d.c_personid AS person_id, d.c_addr_id AS addr_id,
               d.c_addr_type AS addr_type_code,
               c.c_addr_desc AS addr_type_name,
               d.c_sequence AS sequence, d.c_natal AS natal,
               CASE WHEN b.c_index_addr_id=d.c_addr_id THEN 1 ELSE 0 END AS index_match,
               'BIOG_ADDR_DATA' AS address_source
        FROM BIOG_ADDR_DATA d
        JOIN BIOG_MAIN b ON b.c_personid=d.c_personid
        LEFT JOIN BIOG_ADDR_CODES c ON c.c_addr_type=d.c_addr_type
        WHERE d.c_personid>0 AND d.c_addr_id>0
          AND d.c_addr_type IN ({allowed})
          AND COALESCE(d.c_delete,0)=0
        """,
        connection,
    )
    index_fallback = pd.read_sql_query(
        f"""
        SELECT b.c_personid AS person_id, b.c_index_addr_id AS addr_id,
               b.c_index_addr_type_code AS addr_type_code,
               c.c_addr_desc AS addr_type_name,
               NULL AS sequence, 0 AS natal, 1 AS index_match,
               'BIOG_MAIN_INDEX' AS address_source
        FROM BIOG_MAIN b
        LEFT JOIN BIOG_ADDR_CODES c ON c.c_addr_type=b.c_index_addr_type_code
        WHERE b.c_personid>0 AND b.c_index_addr_id>0
          AND b.c_index_addr_type_code IN ({allowed})
        """,
        connection,
    )
    candidates = pd.concat([relational, index_fallback], ignore_index=True)
    candidates["type_priority"] = candidates["addr_type_code"].map(TYPE_PRIORITY).fillna(99)
    candidates["sequence_priority"] = pd.to_numeric(candidates["sequence"], errors="coerce").fillna(9999)
    candidates["source_priority"] = candidates["address_source"].map({"BIOG_ADDR_DATA": 0, "BIOG_MAIN_INDEX": 1})
    candidates = candidates.sort_values(
        ["person_id", "type_priority", "index_match", "natal", "source_priority", "sequence_priority", "addr_id"],
        ascending=[True, True, False, False, True, True, True],
        kind="mergesort",
    )
    selected = candidates.drop_duplicates("person_id", keep="first").copy()
    return selected, candidates


def choose_historical_hierarchy(
    selected: pd.DataFrame,
    personal: pd.DataFrame,
    addresses: pd.DataFrame,
    address_codes: pd.DataFrame,
    dynasties: pd.DataFrame,
) -> pd.DataFrame:
    reference = personal[["person_id", "dynasty_code", "dynasty_name", "safe_birth_year"]].merge(
        dynasties, on="dynasty_code", how="left", validate="many_to_one"
    )
    valid_dynasty = reference["dynasty_start"].notna() & reference["dynasty_end"].notna() & reference["dynasty_end"].gt(reference["dynasty_start"])
    reference["dynasty_midpoint"] = ((reference["dynasty_start"] + reference["dynasty_end"]) / 2.0).where(valid_dynasty)
    reference["reference_year"] = reference["safe_birth_year"].fillna(reference["dynasty_midpoint"])
    base = selected.merge(reference, on="person_id", how="left", validate="one_to_one")
    expanded = base.merge(addresses, on="addr_id", how="left")
    start = pd.to_numeric(expanded["belongs_firstyear"], errors="coerce").where(lambda s: s.ne(0))
    end = pd.to_numeric(expanded["belongs_lastyear"], errors="coerce").where(lambda s: s.ne(0))
    ref = expanded["reference_year"]
    expanded["interval_match"] = ref.notna() & start.notna() & end.notna() & ref.between(start, end, inclusive="both")
    below = (start - ref).where(ref < start)
    above = (ref - end).where(ref > end)
    expanded["interval_distance"] = pd.concat([below, above], axis=1).min(axis=1, skipna=True).fillna(1e9)
    expanded.loc[expanded["interval_match"], "interval_distance"] = 0.0
    hierarchy_columns = [f"belongs{level}_ID" for level in range(1, 6)]
    expanded["hierarchy_depth"] = expanded[hierarchy_columns].notna().sum(axis=1)
    expanded["has_coordinates_row"] = expanded["x_coord"].notna() & expanded["y_coord"].notna()
    expanded["interval_span"] = (end - start).abs().fillna(1e9)
    expanded = expanded.sort_values(
        ["person_id", "interval_match", "interval_distance", "hierarchy_depth", "has_coordinates_row", "interval_span", "belongs_firstyear"],
        ascending=[True, False, True, False, False, True, False],
        kind="mergesort",
    ).drop_duplicates("person_id", keep="first")

    expanded = expanded.merge(
        address_codes.rename(columns={
            "name": "fallback_addr_name", "name_zh": "fallback_addr_name_zh",
            "admin_type": "fallback_admin_type", "longitude": "fallback_longitude",
            "latitude": "fallback_latitude",
        }),
        on="addr_id", how="left", validate="many_to_one",
    )
    expanded["addr_name"] = expanded["addr_name"].fillna(expanded["fallback_addr_name"])
    expanded["addr_name_zh"] = expanded["addr_name_zh"].fillna(expanded["fallback_addr_name_zh"])
    expanded["admin_type"] = expanded["admin_type"].fillna(expanded["fallback_admin_type"])
    expanded["longitude"] = pd.to_numeric(expanded["x_coord"], errors="coerce").fillna(expanded["fallback_longitude"])
    expanded["latitude"] = pd.to_numeric(expanded["y_coord"], errors="coerce").fillna(expanded["fallback_latitude"])
    valid_coordinates = (
        expanded["longitude"].between(-180, 180)
        & expanded["latitude"].between(-90, 90)
        & ~(expanded["longitude"].eq(0) & expanded["latitude"].eq(0))
    )
    expanded.loc[~valid_coordinates, ["longitude", "latitude"]] = np.nan
    return expanded


def assign_hierarchy_levels(frame: pd.DataFrame) -> pd.DataFrame:
    admin = frame["admin_type"].astype("string").fillna("").str.lower()
    county_like = admin.str.contains(r"xian|county|zizhixian|shixiaqu", regex=True)
    prefecture_like = admin.str.contains(r"(?:^|\s)(?:fu|zhou|lu|jun)(?:$|\s)|prefecture|dudufu|jiedu", regex=True)
    province_like = admin.str.contains(r"sheng|buzhengsi|province|(?:^|\s)dao(?:$|\s)|region", regex=True)

    frame["county_id"] = pd.Series(pd.NA, index=frame.index, dtype="Int64")
    frame.loc[county_like, "county_id"] = frame.loc[county_like, "addr_id"].astype("Int64")
    frame["prefecture_id"] = pd.to_numeric(frame["belongs1_ID"], errors="coerce").astype("Int64")
    frame.loc[prefecture_like, "prefecture_id"] = frame.loc[prefecture_like, "addr_id"].astype("Int64")
    frame["province_id"] = pd.to_numeric(frame["belongs2_ID"], errors="coerce").astype("Int64")
    frame.loc[prefecture_like, "province_id"] = pd.to_numeric(frame.loc[prefecture_like, "belongs1_ID"], errors="coerce").astype("Int64")
    frame.loc[province_like, "province_id"] = frame.loc[province_like, "addr_id"].astype("Int64")
    return frame


def main() -> int:
    logger = setup_logging("phase2_geography", PROJECT_ROOT / "outputs/logs/phase2_geography.log")
    config = load_config()
    database = PROJECT_ROOT / config["database"]["working_db"]
    personal = pd.read_parquet(PROJECT_ROOT / "data/features/personal_features.parquet")
    with connect_readonly(database, config["database"]["busy_timeout_ms"]) as connection:
        selected, candidates = choose_primary_address(connection)
        addresses = pd.read_sql_query(
            """
            SELECT c_addr_id AS addr_id, c_name AS addr_name, c_name_chn AS addr_name_zh,
                   c_admin_type AS admin_type, c_belongs_firstyear AS belongs_firstyear,
                   c_belongs_lastyear AS belongs_lastyear, x_coord, y_coord,
                   belongs1_ID, belongs1_Name, belongs1_Name_chn,
                   belongs2_ID, belongs2_Name, belongs2_Name_chn,
                   belongs3_ID, belongs3_Name, belongs3_Name_chn,
                   belongs4_ID, belongs4_Name, belongs4_Name_chn,
                   belongs5_ID, belongs5_Name, belongs5_Name_chn
            FROM ADDRESSES
            """,
            connection,
        )
        address_codes = pd.read_sql_query(
            """
            SELECT c_addr_id AS addr_id, c_name AS name, c_name_chn AS name_zh,
                   c_admin_type AS admin_type, x_coord AS longitude, y_coord AS latitude
            FROM ADDR_CODES WHERE c_addr_id>0
            """,
            connection,
        )
        dynasties = pd.read_sql_query(
            "SELECT c_dy AS dynasty_code, c_start AS dynasty_start, c_end AS dynasty_end FROM DYNASTIES",
            connection,
        )
    historical = choose_historical_hierarchy(selected, personal, addresses, address_codes, dynasties)
    historical = assign_hierarchy_levels(historical)
    count_map = selected.groupby("addr_id")["person_id"].nunique()
    historical["local_cbdb_person_count"] = historical["addr_id"].map(count_map).astype(float)
    historical["local_address_density"] = np.log1p(historical["local_cbdb_person_count"])
    capitals = assign_capitals(historical, load_yaml("configs/dynasty_capitals.yaml"))
    historical = pd.concat([historical, capitals], axis=1)
    historical["distance_to_dynasty_capital_km"] = haversine_km(
        historical["latitude"], historical["longitude"],
        historical["capital_latitude"], historical["capital_longitude"],
    )

    columns = [
        "person_id", "addr_id", "addr_type_code", "addr_type_name", "address_source",
        "addr_name", "addr_name_zh", "admin_type", "county_id", "prefecture_id", "province_id",
        "latitude", "longitude", "capital_name", "distance_to_dynasty_capital_km",
        "local_cbdb_person_count", "local_address_density",
    ]
    features = personal[["person_id"]].merge(historical[columns], on="person_id", how="left", validate="one_to_one")
    features["has_geography"] = features["addr_id"].notna().astype("int8")
    features = features[["person_id", "has_geography"] + [column for column in columns if column != "person_id"]]
    ensure_unique_people(features)
    atomic_to_parquet(features, PROJECT_ROOT / "data/features/geography_features.parquet")

    type_counts = selected["addr_type_name"].fillna("unknown").value_counts().head(10)
    doc = [
        "# Geography feature definition",
        "",
        "`primary_background_address` is selected only from official background-like address types: Basic Affiliation, Birth Address, Household Registration, Household Address, Ancestral Address, Actual Residence, Alternate Basic Affiliation, and Qing Banner background. Death, burial, exile, travel, migration-route, and other later-life types are excluded.",
        "",
        "Selection is deterministic: official address-type priority first; then agreement with `BIOG_MAIN.c_index_addr_id`, natal flag, relation-table source, sequence, and address ID. The official Basic Affiliation is preferred because CBDB defines it as the single judgment-based index affiliation. We do not select an arbitrary first address.",
        "",
        "For the time-varying `ADDRESSES` hierarchy, a valid SAFE birth year is the reference year; otherwise the dynasty midpoint is used as an approximation. The matching interval is preferred, followed by the nearest interval, hierarchy completeness, coordinate availability, and narrower interval. County/prefecture/province fields preserve historical hierarchy IDs and are not mapped to modern provinces.",
        "",
        "Capital distance uses Haversine kilometers. Multi-capital Song and Ming entries use SAFE birth year when available; otherwise a documented dynasty-level canonical capital is used. Missing or invalid coordinates remain missing. `local_cbdb_person_count` is a non-target count at the selected address and `local_address_density=log(1+count)`. `local_entry_prior` is deliberately absent here and is derived train-only/OOF inside the model pipeline.",
        "",
        f"Selected background geography for **{int(features.has_geography.sum()):,}** people ({features.has_geography.mean():.2%}); valid coordinates for **{int(features.latitude.notna().sum()):,}** people ({features.latitude.notna().mean():.2%}).",
        "",
        "Top selected address types:",
        "",
    ]
    doc.extend([f"- {name}: {count:,}" for name, count in type_counts.items()])
    doc.append("")
    atomic_write_text(PROJECT_ROOT / "docs/audit/geography_feature_definition.md", "\n".join(doc))
    logger.info(
        "Geography complete: selected=%d (%.2f%%) coordinates=%d (%.2f%%), candidates=%d",
        int(features.has_geography.sum()), 100 * features.has_geography.mean(),
        int(features.latitude.notna().sum()), 100 * features.latitude.notna().mean(), len(candidates),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
