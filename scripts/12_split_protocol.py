#!/usr/bin/env python3
"""Materialize reproducible split assignments and document future ablation rules."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import configured_path, load_config
from src.utils import atomic_write_text, markdown_table, setup_logging


def group_seed(seed: int, key: tuple[object, ...]) -> int:
    digest = hashlib.sha256((str(seed) + "|" + "|".join(map(str, key))).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "little") % (2**32 - 1)


def exact_stratified_assignments(
    frame: pd.DataFrame,
    group_columns: list[str],
    seed: int,
    train_fraction: float,
    validation_fraction: float,
) -> pd.Series:
    assignments = pd.Series(index=frame.index, dtype="object")
    grouper = group_columns[0] if len(group_columns) == 1 else group_columns
    for key, subset in frame.groupby(grouper, dropna=False, sort=True):
        key_tuple = key if isinstance(key, tuple) else (key,)
        indices = subset.sort_values("person_id").index.to_numpy(copy=True)
        rng = np.random.default_rng(group_seed(seed, key_tuple))
        rng.shuffle(indices)
        n = len(indices)
        train_end = int(np.floor(n * train_fraction))
        validation_end = train_end + int(np.floor(n * validation_fraction))
        assignments.loc[indices[:train_end]] = "train"
        assignments.loc[indices[train_end:validation_end]] = "validation"
        assignments.loc[indices[validation_end:]] = "test"
    return assignments


def split_summary_rows(frame: pd.DataFrame, protocol: str, column: str) -> list[dict[str, object]]:
    rows = []
    for split, subset in frame.groupby(column, dropna=False):
        rows.append({
            "protocol": protocol,
            "split": split,
            "n_people": len(subset),
            "entry_v1_positive": int(subset["target_entry_v1"].sum()),
            "entry_v1_rate": float(subset["target_entry_v1"].mean()) if len(subset) else 0.0,
            "safe_time_coverage": float(subset["has_safe_time_anchor"].mean()) if len(subset) else 0.0,
        })
    return rows


def main() -> int:
    config = load_config()
    interim_dir = configured_path(config, "paths", "interim")
    tables_dir = configured_path(config, "paths", "tables")
    audit_dir = configured_path(config, "paths", "audit_docs")
    logger = setup_logging("splits", configured_path(config, "paths", "logs") / "split_protocol.log")
    population_path = interim_dir / "person_modeling_population.parquet"
    population = pd.read_parquet(population_path, columns=[
        "person_id", "dynasty_code", "dynasty", "safe_index_year", "has_safe_time_anchor", "target_entry_v1",
    ])

    settings = config["phase1_5"]
    seed = int(config["seed"])
    train_fraction = float(settings["split_train_fraction"])
    validation_fraction = float(settings["split_validation_fraction"])
    test_fraction = float(settings["split_test_fraction"])
    if not np.isclose(train_fraction + validation_fraction + test_fraction, 1.0):
        raise ValueError("Configured Phase 1.5 split fractions must sum to one")

    assignments = population.copy()
    assignments["split_random_stratified"] = exact_stratified_assignments(
        assignments, ["target_entry_v1"], seed, train_fraction, validation_fraction
    )
    assignments["dynasty_stratum"] = assignments["dynasty_code"].astype("string").fillna("[NULL]")
    assignments["split_dynasty_stratified"] = exact_stratified_assignments(
        assignments, ["dynasty_stratum", "target_entry_v1"], seed, train_fraction, validation_fraction
    )

    assignments["split_temporal_safe"] = "not_eligible"
    eligible = assignments["has_safe_time_anchor"].eq(1) & assignments["safe_index_year"].notna()
    safe_years = assignments.loc[eligible, "safe_index_year"].astype(float)
    train_cutoff = float(safe_years.quantile(train_fraction, interpolation="higher"))
    validation_cutoff = float(safe_years.quantile(train_fraction + validation_fraction, interpolation="higher"))
    assignments.loc[eligible & assignments["safe_index_year"].le(train_cutoff), "split_temporal_safe"] = "train"
    assignments.loc[eligible & assignments["safe_index_year"].gt(train_cutoff) & assignments["safe_index_year"].le(validation_cutoff), "split_temporal_safe"] = "validation"
    assignments.loc[eligible & assignments["safe_index_year"].gt(validation_cutoff), "split_temporal_safe"] = "test"

    assignments["split_holdout_qing"] = "excluded"
    assignments.loc[assignments["dynasty"].isin(["Song", "Yuan", "Ming"]), "split_holdout_qing"] = "train"
    assignments.loc[assignments["dynasty"].eq("Qing"), "split_holdout_qing"] = "test"
    assignments["leave_one_major_dynasty_fold"] = assignments["dynasty"].where(assignments["dynasty"].isin(["Tang", "Song", "Yuan", "Ming", "Qing"]), "not_major_dynasty")

    split_output = assignments[[
        "person_id", "split_random_stratified", "split_dynasty_stratified", "split_temporal_safe",
        "split_holdout_qing", "leave_one_major_dynasty_fold",
    ]]
    split_output.to_parquet(interim_dir / "person_split_assignments.parquet", index=False, compression="zstd")

    summary_rows = []
    for protocol, column in (
        ("A_random_stratified", "split_random_stratified"),
        ("B_dynasty_target_stratified", "split_dynasty_stratified"),
        ("C_temporal_SAFE_anchor", "split_temporal_safe"),
        ("D_Song_Yuan_Ming_to_Qing", "split_holdout_qing"),
    ):
        summary_rows.extend(split_summary_rows(assignments, protocol, column))
    split_summary = pd.DataFrame(summary_rows)
    split_summary.to_csv(tables_dir / "split_assignment_summary.csv", index=False)

    population_summary = pd.read_csv(tables_dir / "modeling_population_summary.csv")
    key_populations = population_summary[population_summary["population"].isin(["Global", "Song", "Ming", "Qing"])]
    document = [
        "# Modeling, split, ablation, and family-leakage protocol",
        "",
        "Phase 1.5 freezes protocols but trains no formal model. Any future preprocessing, imputation, category consolidation, family aggregation, matching, and feature selection must be fitted on training data only. Test labels remain untouched until the final locked evaluation.",
        "",
        "## Modeling populations",
        "",
        markdown_table(
            ["population", "people", "V1 rate", "posting rate", "kin", "address", "association", "SAFE time"],
            ([row.population, row.n_people, f"{row.entry_v1_rate:.2%}", f"{row.posting_rate:.2%}", f"{row.kin_coverage:.2%}", f"{row.address_coverage:.2%}", f"{row.assoc_coverage:.2%}", f"{row.safe_time_anchor_coverage:.2%}"] for row in key_populations.itertuples()),
        ),
        "",
        "Population choice must balance target definition, family/geography coverage, safe time coverage, and institutional comparability—not sample size alone. Global and dynasty-specific results must be reported separately.",
        "",
        "## Required baselines and ablations",
        "",
        "- **Baseline 0 / M0a — dynasty only.**",
        "- **Baseline 1 / M0 — dynasty + SAFE cohort/time.**",
        "- **M1 Personal — M0 + gender and safe personal background.**",
        "- **M2 Geography — M1 + pre-entry geographic background.**",
        "- **M3 Family — M2 + temporally valid family political capital.**",
        "- **M4 Network — M3 + dated, pre-entry social-network features on the eligible subset.**",
        "- **M5 Documentation — documentation-only indicators/intensity.**",
        "- **Full historical — M0+M1+M2+M3+M4.**",
        "- **Historical + documentation — all safe historical and documentation features.**",
        "",
        "Every extension reports ΔROC-AUC, ΔPR-AUC, and ΔLogLoss relative to the relevant dynasty/time baseline, with uncertainty. V1 is always described as current CBDB ENTRY-record presence; V2 candidates and posting are robustness outcomes.",
        "",
        "## Split A — random target-stratified",
        "",
        f"A deterministic {train_fraction:.0%}/{validation_fraction:.0%}/{test_fraction:.0%} assignment with seed {seed}. It is a standard ML benchmark only and cannot be the sole historical validation.",
        "",
        "## Split B — dynasty + target stratified (recommended primary benchmark)",
        "",
        "The same proportions are assigned independently within every `(dynasty_code, target)` stratum. This prevents major dynasty concentration in one partition while preserving a locked test set. Family-connected people may later require group-aware refinement to prevent relatives crossing folds.",
        "",
        "## Split C — Global chronological distribution-shift sensitivity",
        "",
        f"Only SAFE time-anchor people are eligible. Whole years are kept together: train through {train_cutoff:g}, validation through {validation_cutoff:g}, and later years test. This is not pure temporal generalization: calendar time, dynasty/regime composition, source composition, and recording practice shift together. It is a Global chronological distribution-shift sensitivity, not a replacement for the main split.",
        "",
        "## Split D — dynasty holdout",
        "",
        "The concrete Qing holdout trains on Song+Yuan+Ming and tests on Qing. Additional leave-one-major-dynasty-out evaluations should rotate Tang/Song/Yuan/Ming/Qing. These evaluate transport across institutional regimes; low performance is informative rather than a tuning failure.",
        "",
        "## Two-track family leakage protocol",
        "",
        "The large-sample Cross-sectional Family Capital track uses explicitly named `ever_*` lifetime-record variables and supports predictive association analysis only. The Strict Temporal Family Capital track requires a SAFE focal anchor and a valid relative event year strictly before that anchor. Undated relative outcomes remain missing. Full frozen rules are in `family_feature_protocol.md`.",
        "",
        "Use the real `KINSHIP_CODES` direction fields (`c_upstep`, `c_dwnstep`, `c_marstep`) plus labels to classify relations:",
        "",
        "- `ancestor`: upstep > 1, no descendant step; highest priority older ancestors.",
        "- `parent_generation`: upstep = 1; prioritize father, maternal elder, and known parents.",
        "- `same_generation`: neither upward nor downward generation after resolving collaterals; siblings are not automatically pre-entry-safe.",
        "- `descendant`: dwnstep > 0; excluded by default from a pre-entry background model.",
        "- `marital`: marstep > 0; allowed only when marriage timing precedes the focal anchor.",
        "- `other`: missing/sentinel/conflicting direction; manual review or exclusion.",
        "",
        "A relative's ENTRY/posting/status can contribute to `father_official`, `grandfather_official`, or family entry rates only if the relative outcome year is valid and no later than the focal person's training-fold risk anchor. Undated career outcomes are excluded from the strict feature, retained only in sensitivity variants. Children, younger descendants, and later-life siblings are prohibited by default. Family components must be calculated after split assignment; connected-family grouping should be considered to avoid relational leakage across train/test.",
        "",
        "## Documentation-bias separation",
        "",
        "Documentation indicators exclude ENTRY and posting. M5 is evaluated alone, then added to the historical feature set. Differences are predictive associations with database recording intensity and must not be interpreted as historical causes.",
        "",
        "## Family-group robustness split",
        "",
        "The primary benchmark remains dynasty × target stratified. A separately saved robustness split assigns whole core blood-family groups to one partition; marriage, affinal relations, and distant-kin propagation are excluded from component construction.",
        "",
        "## Within-dynasty temporal plan",
        "",
        "Phase 2/3 should audit SAFE-time counts within Song, Ming, and Qing and, where support is sufficient, save early/middle/late or 70%/15%/15% chronological cohorts. This is designed for within-regime temporal generalization and is not forced while SAFE-time coverage remains low.",
        "",
    ]
    atomic_write_text(audit_dir / "split_protocol.md", "\n".join(document))

    sentinel_document = [
        "# Sentinel and field-aware missingness policy",
        "",
        "CBDB sentinel handling is field-specific. Raw database columns and Phase 1 files are never overwritten, and global operations such as `df.replace(0, np.nan)` are prohibited.",
        "",
        "| Field semantic | Derived treatment | Rationale |",
        "| --- | --- | --- |",
        "| Calendar years | `0`, `-1`, `-999`, `-9999`, values below -1200 or above 2100 → missing | Explicit Phase 1.5 time policy; retain raw companion columns |",
        "| Person/kin/association IDs used as graph nodes | `0`, `-1`, `-999`, `-9999`, `-10000` → invalid ID | Never create person 0 or unknown-person nodes |",
        "| Address/office/institution relation IDs | Zero/negative sentinels excluded from edges, but raw value retained | Code tables may contain an Unknown row, which is not a substantive place/office edge |",
        "| Code-table categories | Keep mapped 0/−1 as explicit Unknown/Missing categories when the code table defines them | Categorical semantics differ from identifier semantics |",
        "| Counts and presence flags | Zero remains zero | It represents observed absence in the selected table, not missing numeric data |",
        "| `BIOG_MAIN.c_female` | 0 remains the database's male code; NULL is unknown | Zero is substantive here |",
        "",
        "The shared `src/cleaning.py` helpers require callers to declare year or identifier semantics. Ambiguous fields remain raw until their code table and empirical distribution are audited.",
        "",
    ]
    atomic_write_text(audit_dir / "sentinel_policy.md", "\n".join(sentinel_document))
    logger.info("Split assignments and protocols complete: train cutoff=%s validation cutoff=%s", train_cutoff, validation_cutoff)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
