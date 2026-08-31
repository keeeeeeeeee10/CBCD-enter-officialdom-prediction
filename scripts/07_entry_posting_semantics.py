#!/usr/bin/env python3
"""Quantify ENTRY/POSTING semantics and create non-destructive auxiliary outcomes."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import configured_path, load_config
from src.db import connect_readonly
from src.phase15 import MAJOR_DYNASTIES
from src.utils import atomic_write_text, markdown_table, setup_logging


OUTCOME_QUERY = """
WITH
entry_counts AS (
    SELECT c_personid, COUNT(*) AS n_entry_records
    FROM ENTRY_DATA WHERE c_personid IS NOT NULL AND c_personid<>0 GROUP BY c_personid
),
posting_union AS (
    SELECT c_personid, c_posting_id
    FROM POSTING_DATA WHERE c_personid IS NOT NULL AND c_personid<>0 AND c_posting_id>0
    UNION
    SELECT c_personid, c_posting_id
    FROM POSTED_TO_OFFICE_DATA WHERE c_personid IS NOT NULL AND c_personid<>0 AND c_posting_id>0
),
posting_counts AS (
    SELECT c_personid, COUNT(DISTINCT c_posting_id) AS n_posting_records
    FROM posting_union GROUP BY c_personid
)
SELECT
    b.c_personid AS person_id,
    CASE WHEN e.c_personid IS NULL THEN 0 ELSE 1 END AS target_entry_v1,
    CASE WHEN p.c_personid IS NULL THEN 0 ELSE 1 END AS target_posting,
    COALESCE(e.n_entry_records, 0) AS n_entry_records,
    COALESCE(p.n_posting_records, 0) AS n_posting_records,
    b.c_dy AS dynasty_code,
    d.c_dynasty AS dynasty,
    d.c_dynasty_chn AS dynasty_zh
FROM BIOG_MAIN b
LEFT JOIN entry_counts e ON e.c_personid=b.c_personid
LEFT JOIN posting_counts p ON p.c_personid=b.c_personid
LEFT JOIN DYNASTIES d ON d.c_dy=b.c_dy
ORDER BY b.c_personid
"""


def plot_matrix(contingency: pd.DataFrame, path: Path, dpi: int) -> None:
    matrix = contingency.pivot(index="has_entry", columns="has_posting", values="n_people").reindex(index=[0, 1], columns=[0, 1], fill_value=0)
    annotations = matrix.applymap(lambda value: f"{value:,}\n{value / matrix.to_numpy().sum():.1%}")
    plt.figure(figsize=(7, 5.5))
    sns.heatmap(matrix, annot=annotations, fmt="", cmap="Blues", cbar_kws={"label": "People"})
    plt.title("ENTRY_DATA presence vs posting-record presence")
    plt.xlabel("Has valid posting record")
    plt.ylabel("Has ENTRY_DATA record")
    plt.tight_layout()
    plt.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close()


def plot_dynasties(by_dynasty: pd.DataFrame, path: Path, dpi: int) -> None:
    major = by_dynasty[by_dynasty["dynasty"].isin(MAJOR_DYNASTIES)].copy()
    major["cell"] = major.apply(lambda row: f"E{int(row.has_entry)} P{int(row.has_posting)}", axis=1)
    chart = major.pivot(index="dynasty", columns="cell", values="fraction_within_dynasty").reindex(MAJOR_DYNASTIES).fillna(0)
    chart = chart.reindex(columns=["E0 P0", "E0 P1", "E1 P0", "E1 P1"], fill_value=0)
    ax = chart.plot(kind="bar", stacked=True, figsize=(10, 6), color=["#D9D9D9", "#DD8452", "#55A868", "#4C72B0"])
    ax.set_title("ENTRY/posting composition by major dynasty")
    ax.set_xlabel("Dynasty")
    ax.set_ylabel("Share within dynasty")
    ax.set_ylim(0, 1)
    ax.legend(title="Cell", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close()


def main() -> int:
    config = load_config()
    tables_dir = configured_path(config, "paths", "tables")
    interim_dir = configured_path(config, "paths", "interim")
    audit_dir = configured_path(config, "paths", "audit_docs")
    figures_dir = configured_path(config, "paths", "figures")
    logger = setup_logging("entry_posting", configured_path(config, "paths", "logs") / "entry_posting_semantics.log")
    database = configured_path(config, "database", "working_db")

    with connect_readonly(database, config["database"]["busy_timeout_ms"]) as connection:
        outcomes = pd.read_sql_query(OUTCOME_QUERY, connection)
    for column in ("target_entry_v1", "target_posting"):
        outcomes[column] = outcomes[column].astype("int8")
    for column in ("n_entry_records", "n_posting_records"):
        outcomes[column] = outcomes[column].astype("int32")

    auxiliary_columns = ["person_id", "target_entry_v1", "target_posting", "n_entry_records", "n_posting_records"]
    outcomes[auxiliary_columns].to_parquet(interim_dir / "person_auxiliary_outcomes.parquet", index=False, compression="zstd")

    contingency = outcomes.groupby(["target_entry_v1", "target_posting"], observed=False).size().rename("n_people").reset_index()
    contingency = contingency.rename(columns={"target_entry_v1": "has_entry", "target_posting": "has_posting"})
    contingency["fraction_all"] = contingency["n_people"] / len(outcomes)
    contingency["fraction_within_entry_group"] = contingency["n_people"] / contingency.groupby("has_entry")["n_people"].transform("sum")
    contingency.to_csv(tables_dir / "entry_vs_posting_contingency.csv", index=False)

    dynasty_sizes = outcomes.groupby("dynasty", dropna=False).size()
    threshold = int(config["phase1_5"]["large_dynasty_min_people"])
    included = set(dynasty_sizes[dynasty_sizes >= threshold].index).union(MAJOR_DYNASTIES)
    dynasty_subset = outcomes[outcomes["dynasty"].isin(included)].copy()
    by_dynasty = (
        dynasty_subset.groupby(["dynasty_code", "dynasty", "dynasty_zh", "target_entry_v1", "target_posting"], dropna=False)
        .size().rename("n_people").reset_index()
        .rename(columns={"target_entry_v1": "has_entry", "target_posting": "has_posting"})
    )
    dynasty_totals = by_dynasty.groupby(["dynasty_code", "dynasty"], dropna=False)["n_people"].transform("sum")
    entry_totals = by_dynasty.groupby(["dynasty_code", "dynasty", "has_entry"], dropna=False)["n_people"].transform("sum")
    by_dynasty["fraction_within_dynasty"] = by_dynasty["n_people"] / dynasty_totals
    by_dynasty["fraction_within_entry_group"] = by_dynasty["n_people"] / entry_totals
    by_dynasty.to_csv(tables_dir / "entry_vs_posting_by_dynasty.csv", index=False)

    dpi = int(config["analysis"]["figure_dpi"])
    sns.set_theme(style="whitegrid")
    plot_matrix(contingency, figures_dir / "entry_posting_matrix.png", dpi)
    plot_dynasties(by_dynasty, figures_dir / "entry_posting_by_dynasty.png", dpi)

    cells = {(int(row.has_entry), int(row.has_posting)): int(row.n_people) for row in contingency.itertuples()}
    both = cells[(1, 1)]
    entry_only = cells[(1, 0)]
    posting_only = cells[(0, 1)]
    neither = cells[(0, 0)]
    entry_total = both + entry_only
    posting_total = both + posting_only
    overlap_union = both + entry_only + posting_only
    document = [
        "# ENTRY × posting semantics",
        "",
        "This audit distinguishes presence in `ENTRY_DATA` from evidence of an actual recorded posting. A valid auxiliary posting outcome requires a nonzero person and posting ID in `POSTING_DATA` or `POSTED_TO_OFFICE_DATA`; records are deduplicated by person/posting ID.",
        "",
        markdown_table(
            ["ENTRY", "posting", "people", "share of all", "share within ENTRY group"],
            ([row.has_entry, row.has_posting, row.n_people, f"{row.fraction_all:.2%}", f"{row.fraction_within_entry_group:.2%}"] for row in contingency.itertuples()),
        ),
        "",
        f"- ENTRY-positive without a posting record: **{entry_only:,}** ({entry_only / entry_total:.2%} of ENTRY positives).",
        f"- ENTRY-negative with a posting record: **{posting_only:,}** ({posting_only / (len(outcomes) - entry_total):.2%} of ENTRY negatives).",
        f"- Both records present: **{both:,}**; this is {both / entry_total:.2%} of ENTRY positives and {both / posting_total:.2%} of posting positives.",
        f"- Jaccard overlap between the two recorded-person sets: **{both / overlap_union:.2%}**.",
        f"- Neither record present: **{neither:,}**.",
        "",
        "The incomplete overlap is substantive and also reflects source/editorial coverage. `ENTRY_DATA` includes degrees, student statuses and institutional routes that need not be appointments, while posting records can exist without a separately encoded ENTRY route.",
        "",
        "## Interpretation",
        "",
        "**Target V1 is ENTRY record presence. It must not be described as actual government office holding.** `target_posting` is retained as an auxiliary outcome for target-validity and robustness analysis, not as a Phase 1.5 training target.",
        "",
        "Dynasty-specific cells are in `outputs/tables/entry_vs_posting_by_dynasty.csv`; the chart reports within-dynasty composition and should be read as CBDB recording patterns, not population office-holding rates.",
        "",
    ]
    atomic_write_text(audit_dir / "entry_posting_semantics.md", "\n".join(document))
    logger.info("ENTRY/posting audit complete: both=%d entry_only=%d posting_only=%d neither=%d", both, entry_only, posting_only, neither)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

