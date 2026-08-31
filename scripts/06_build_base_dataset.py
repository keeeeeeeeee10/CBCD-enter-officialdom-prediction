#!/usr/bin/env python3
"""Build a one-row-per-person Version 0 dataset and Phase 1 sanity-check figures."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import configured_path, load_config
from src.db import connect_readonly
from src.utils import atomic_write_text, markdown_table, setup_logging


BASE_QUERY = """
WITH
entry_features AS (
    SELECT c_personid, COUNT(*) AS n_entry_records
    FROM ENTRY_DATA WHERE c_personid IS NOT NULL GROUP BY c_personid
),
kin_features AS (
    SELECT c_personid, COUNT(*) AS n_kin_records
    FROM KIN_DATA WHERE c_personid IS NOT NULL GROUP BY c_personid
),
assoc_features AS (
    SELECT c_personid, COUNT(*) AS n_assoc_records
    FROM ASSOC_DATA WHERE c_personid IS NOT NULL GROUP BY c_personid
),
address_features AS (
    SELECT c_personid, COUNT(*) AS n_address_records
    FROM BIOG_ADDR_DATA WHERE c_personid IS NOT NULL GROUP BY c_personid
),
status_features AS (
    SELECT c_personid, COUNT(*) AS n_status_records
    FROM STATUS_DATA WHERE c_personid IS NOT NULL GROUP BY c_personid
),
text_features AS (
    SELECT c_personid, COUNT(*) AS n_text_records
    FROM BIOG_TEXT_DATA WHERE c_personid IS NOT NULL GROUP BY c_personid
),
institution_features AS (
    SELECT c_personid, COUNT(*) AS n_institution_records
    FROM BIOG_INST_DATA WHERE c_personid IS NOT NULL GROUP BY c_personid
),
posting_features AS (
    SELECT c_personid, COUNT(*) AS n_posting_records
    FROM POSTING_DATA WHERE c_personid IS NOT NULL GROUP BY c_personid
)
SELECT
    b.c_personid AS person_id,
    CASE WHEN entry_features.c_personid IS NULL THEN 0 ELSE 1 END AS target_entry,
    b.c_female AS gender_code,
    CASE
        WHEN b.c_female=1 THEN 'female'
        WHEN b.c_female=0 THEN 'male'
        ELSE 'unknown'
    END AS gender,
    b.c_birthyear AS birth_year,
    b.c_deathyear AS death_year,
    b.c_index_year AS index_year,
    b.c_dy AS dynasty_code,
    d.c_dynasty AS dynasty,
    d.c_dynasty_chn AS dynasty_chn,
    CASE WHEN b.c_birthyear IS NOT NULL AND b.c_birthyear<>0 THEN 1 ELSE 0 END AS has_birth_year,
    CASE WHEN b.c_deathyear IS NOT NULL AND b.c_deathyear<>0 THEN 1 ELSE 0 END AS has_death_year,
    CASE WHEN b.c_index_year IS NOT NULL AND b.c_index_year<>0 THEN 1 ELSE 0 END AS has_index_year,
    CASE WHEN address_features.c_personid IS NULL THEN 0 ELSE 1 END AS has_address,
    CASE WHEN kin_features.c_personid IS NULL THEN 0 ELSE 1 END AS has_kin_record,
    CASE WHEN assoc_features.c_personid IS NULL THEN 0 ELSE 1 END AS has_assoc_record,
    CASE WHEN status_features.c_personid IS NULL THEN 0 ELSE 1 END AS has_status_record,
    CASE WHEN text_features.c_personid IS NULL THEN 0 ELSE 1 END AS has_text_record,
    CASE WHEN institution_features.c_personid IS NULL THEN 0 ELSE 1 END AS has_institution_record,
    CASE WHEN posting_features.c_personid IS NULL THEN 0 ELSE 1 END AS has_posting_record,
    COALESCE(kin_features.n_kin_records, 0) AS n_kin_records,
    COALESCE(assoc_features.n_assoc_records, 0) AS n_assoc_records,
    COALESCE(address_features.n_address_records, 0) AS n_address_records,
    COALESCE(status_features.n_status_records, 0) AS n_status_records,
    COALESCE(text_features.n_text_records, 0) AS n_text_records,
    COALESCE(institution_features.n_institution_records, 0) AS n_institution_records,
    COALESCE(posting_features.n_posting_records, 0) AS n_posting_records,
    COALESCE(entry_features.n_entry_records, 0) AS n_entry_records
FROM BIOG_MAIN AS b
LEFT JOIN DYNASTIES AS d ON d.c_dy=b.c_dy
LEFT JOIN entry_features ON entry_features.c_personid=b.c_personid
LEFT JOIN kin_features ON kin_features.c_personid=b.c_personid
LEFT JOIN assoc_features ON assoc_features.c_personid=b.c_personid
LEFT JOIN address_features ON address_features.c_personid=b.c_personid
LEFT JOIN status_features ON status_features.c_personid=b.c_personid
LEFT JOIN text_features ON text_features.c_personid=b.c_personid
LEFT JOIN institution_features ON institution_features.c_personid=b.c_personid
LEFT JOIN posting_features ON posting_features.c_personid=b.c_personid
ORDER BY b.c_personid
"""


BINARY_COLUMNS = [
    "target_entry",
    "has_birth_year",
    "has_death_year",
    "has_index_year",
    "has_address",
    "has_kin_record",
    "has_assoc_record",
    "has_status_record",
    "has_text_record",
    "has_institution_record",
    "has_posting_record",
]

COUNT_COLUMNS = [
    "n_kin_records",
    "n_assoc_records",
    "n_address_records",
    "n_status_records",
    "n_text_records",
    "n_institution_records",
    "n_posting_records",
    "n_entry_records",
]


def normalize_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    chunk["person_id"] = chunk["person_id"].astype("int64")
    for column in ("gender_code", "birth_year", "death_year", "index_year", "dynasty_code"):
        chunk[column] = chunk[column].astype("Int64")
    for column in BINARY_COLUMNS:
        chunk[column] = chunk[column].astype("int8")
    for column in COUNT_COLUMNS:
        chunk[column] = chunk[column].astype("int32")
    return chunk


def write_base_parquet(connection, path: Path, chunk_rows: int, logger) -> tuple[int, list[str]]:
    writer: pq.ParquetWriter | None = None
    total = 0
    columns: list[str] = []
    try:
        for chunk_index, chunk in enumerate(pd.read_sql_query(BASE_QUERY, connection, chunksize=chunk_rows), 1):
            chunk = normalize_chunk(chunk)
            table = pa.Table.from_pandas(chunk, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(path, table.schema, compression="zstd")
                columns = list(chunk.columns)
            writer.write_table(table)
            total += len(chunk)
            logger.info("Parquet chunk %d: %d rows (cumulative %d)", chunk_index, len(chunk), total)
    finally:
        if writer is not None:
            writer.close()
    if writer is None:
        raise RuntimeError("Base dataset SQL query returned no rows")
    return total, columns


def save_figure(path: Path, dpi: int) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close()


def create_figures(base: pd.DataFrame, tables_dir: Path, figures_dir: Path, dpi: int, logger) -> tuple[pd.DataFrame, pd.DataFrame]:
    sns.set_theme(style="whitegrid")

    target_counts = base["target_entry"].value_counts().reindex([0, 1], fill_value=0)
    plt.figure(figsize=(7, 5))
    ax = sns.barplot(x=["No ENTRY_DATA record", "Has ENTRY_DATA record"], y=target_counts.values, color="#4C72B0")
    ax.set(title="CBDB Target V1 class distribution", xlabel="Target class", ylabel="People")
    for patch, value in zip(ax.patches, target_counts.values):
        ax.annotate(f"{value:,}\n({value / len(base):.1%})", (patch.get_x() + patch.get_width() / 2, patch.get_height()), ha="center", va="bottom")
    save_figure(figures_dir / "target_class_distribution.png", dpi)

    plausible_index = (
        base.loc[base["index_year"].between(-1000, 2100) & base["index_year"].ne(0), "index_year"]
        .dropna()
        .astype("int64")
    )
    plt.figure(figsize=(10, 5))
    sns.histplot(plausible_index, bins=70, color="#55A868")
    plt.title("CBDB person index-year distribution (plausible historical range)")
    plt.xlabel("Index year")
    plt.ylabel("People")
    save_figure(figures_dir / "index_year_distribution.png", dpi)

    dynasty_counts = base.assign(dynasty_label=base["dynasty"].fillna("[NULL/unmapped]")).groupby("dynasty_label", dropna=False).size().sort_values(ascending=False).head(20)
    plt.figure(figsize=(10, 7))
    sns.barplot(x=dynasty_counts.values, y=dynasty_counts.index, color="#C44E52")
    plt.title("People by dynasty (top 20 by CBDB records)")
    plt.xlabel("People")
    plt.ylabel("Dynasty")
    save_figure(figures_dir / "people_by_dynasty.png", dpi)

    dynasty_rates = (
        base.assign(dynasty_label=base["dynasty"].fillna("[NULL/unmapped]"))
        .groupby("dynasty_label", dropna=False)["target_entry"]
        .agg(["size", "mean"])
        .sort_values("size", ascending=False)
        .head(20)
        .sort_values("mean")
    )
    plt.figure(figsize=(10, 7))
    sns.barplot(x=dynasty_rates["mean"], y=dynasty_rates.index, color="#8172B2")
    plt.title("Target V1 rate by dynasty (20 largest CBDB groups)")
    plt.xlabel("Share with ENTRY_DATA record")
    plt.ylabel("Dynasty")
    plt.xlim(0, max(0.05, min(1.0, float(dynasty_rates["mean"].max()) * 1.1)))
    save_figure(figures_dir / "target_rate_by_dynasty.png", dpi)

    missing_masks = {
        "gender": base["gender"].eq("unknown"),
        "birth_year": base["birth_year"].isna() | base["birth_year"].eq(0),
        "death_year": base["death_year"].isna() | base["death_year"].eq(0),
        "index_year": base["index_year"].isna() | base["index_year"].eq(0),
        "dynasty": base["dynasty_code"].isna() | base["dynasty_code"].eq(0),
        "address_record": base["has_address"].eq(0),
        "kin_record": base["has_kin_record"].eq(0),
        "association_record": base["has_assoc_record"].eq(0),
        "status_record": base["has_status_record"].eq(0),
        "text_record": base["has_text_record"].eq(0),
        "institution_record": base["has_institution_record"].eq(0),
        "posting_record": base["has_posting_record"].eq(0),
    }
    missingness = pd.DataFrame([
        {"field": field, "missing_count": int(mask.sum()), "missing_rate": float(mask.mean())}
        for field, mask in missing_masks.items()
    ]).sort_values("missing_rate", ascending=False)
    missingness.to_csv(tables_dir / "base_missingness.csv", index=False)
    plt.figure(figsize=(10, 6))
    sns.barplot(data=missingness.head(20), x="missing_rate", y="field", color="#CCB974")
    plt.title("Missing/absent information in person_base_v0")
    plt.xlabel("Missing or absent share")
    plt.ylabel("Field / record group")
    plt.xlim(0, 1)
    save_figure(figures_dir / "missing_values_top20.png", dpi)

    coverage_mapping = {
        "kinship": "has_kin_record",
        "association": "has_assoc_record",
        "address": "has_address",
        "posting": "has_posting_record",
        "text": "has_text_record",
        "institution": "has_institution_record",
        "status": "has_status_record",
    }
    coverage = pd.DataFrame([
        {
            "feature_group": label,
            "people_with_record": int(base[column].sum()),
            "coverage_rate": float(base[column].mean()),
        }
        for label, column in coverage_mapping.items()
    ]).sort_values("coverage_rate", ascending=False)
    coverage.to_csv(tables_dir / "coverage_summary.csv", index=False)
    plt.figure(figsize=(9, 5))
    sns.barplot(data=coverage, x="coverage_rate", y="feature_group", color="#64B5CD")
    plt.title("Coverage of key CBDB person-level record groups")
    plt.xlabel("Share of BIOG_MAIN people with at least one record")
    plt.ylabel("Record group")
    plt.xlim(0, 1)
    save_figure(figures_dir / "key_table_coverage.png", dpi)
    logger.info("Generated six 300-dpi sanity-check figures")
    return missingness, coverage


def main() -> int:
    config = load_config()
    processed_dir = configured_path(config, "paths", "processed")
    tables_dir = configured_path(config, "paths", "tables")
    figures_dir = configured_path(config, "paths", "figures")
    audit_dir = configured_path(config, "paths", "audit_docs")
    logger = setup_logging("base", configured_path(config, "paths", "logs") / "build_base_dataset.log")
    database = configured_path(config, "database", "working_db")
    output = processed_dir / "person_base_v0.parquet"

    with connect_readonly(database, config["database"]["busy_timeout_ms"]) as connection:
        total, output_columns = write_base_parquet(connection, output, int(config["analysis"]["parquet_chunk_rows"]), logger)
    base = pd.read_parquet(output)
    if len(base) != total or base["person_id"].duplicated().any():
        raise RuntimeError("Base dataset failed one-row-per-person integrity check")
    if not (base["target_entry"] == base["n_entry_records"].gt(0).astype("int8")).all():
        raise RuntimeError("target_entry is inconsistent with n_entry_records")
    base.head(1000).to_csv(processed_dir / "person_base_v0_sample.csv", index=False)

    missingness, coverage = create_figures(
        base,
        tables_dir,
        figures_dir,
        int(config["analysis"]["figure_dpi"]),
        logger,
    )

    data_dictionary = pd.DataFrame([
        ("person_id", "identifier", "BIOG_MAIN.c_personid", "No"),
        ("target_entry", "Target V1", "presence in ENTRY_DATA", "Target only"),
        ("gender_code / gender", "basic person", "BIOG_MAIN.c_female; observed codes 0/1/NULL", "Yes"),
        ("birth_year / death_year / index_year", "basic temporal", "BIOG_MAIN raw values; zero/sentinels retained", "Yes after quality handling"),
        ("dynasty_code / dynasty / dynasty_chn", "temporal category", "BIOG_MAIN.c_dy joined to DYNASTIES", "Yes"),
        ("has_* / n_*_records", "coverage/count", "separately aggregated child tables", "Depends on leakage class"),
        ("has_posting_record / n_posting_records", "post-entry outcome", "POSTING_DATA", "No (Model B)"),
        ("n_entry_records", "direct target", "ENTRY_DATA", "Never"),
    ], columns=["fields", "meaning", "source", "allowed_pre_entry_model"])
    data_dictionary.to_csv(tables_dir / "person_base_v0_data_dictionary.csv", index=False)

    document = [
        "# CBDB data limitations",
        "",
        "CBDB is not a random sample of the historical population of China. It is a prosopographical database assembled from surviving and selected historical sources, so its recorded people and fields reflect who was documented, which sources survived, and what editors encoded.",
        "",
        "## Required interpretation",
        "",
        f"In this release, **{int(base['target_entry'].sum()):,} of {len(base):,} CBDB people ({base['target_entry'].mean():.2%})** have at least one current `ENTRY_DATA` record. "
        "This is the **entry-record share among people included in CBDB**, not the true historical entry rate of people in China.",
        "",
        "`target_entry = 0` means **no entry record was found in the current CBDB ENTRY_DATA table**. It must not be described as “this person certainly never held office” or “never entered government.”",
        "",
        "## Main biases",
        "",
        "- **Selection bias:** inclusion follows research sources and database scope, not population sampling.",
        "- **Survivorship bias:** people and events in surviving texts are disproportionately observable.",
        "- **Recording bias:** a missing row or field can mean missing documentation or incomplete encoding, not absence in history.",
        "- **Elite bias:** officials, examination candidates, writers, and well-connected families are more likely to be documented.",
        "- **Gender bias:** women and gender-minority/unknown records have markedly different documentation coverage; `c_female=0` is retained as the database code and NULL remains unknown.",
        "- **Temporal coverage bias:** dynasties and periods have unequal source survival and CBDB coverage.",
        "- **Regional coverage bias:** place coverage and geocoding differ by region and period.",
        "",
        "## Modeling consequences",
        "",
        "Model A measures how well all non-target CBDB records identify database entry-record presence and is an upper bound on record-completeness prediction. "
        "Model B requires temporal anchoring and safer background features. Neither supports causal claims without a separate research design. Missingness and relationship counts may themselves encode scholarly attention, so even apparently neutral coverage indicators require interpretation.",
        "",
        "No anomalous or missing records are deleted in Phase 1. Exact issue counts are retained in `outputs/tables/data_quality_issues.csv`; field and relation coverage is retained in `base_missingness.csv` and `coverage_summary.csv`.",
        "",
    ]
    atomic_write_text(audit_dir / "data_limitations.md", "\n".join(document))
    logger.info("Base dataset complete: %d people, %d columns, %s", total, len(output_columns), output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
