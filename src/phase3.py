"""Phase 3 scientific-validation, provenance, and packaging utilities.

This module is deliberately read-only with respect to all Phase 1--2.6 assets.
Every file it creates is confined to the Phase 3 output, paper, submission, or
review directories.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score

from src.phase26 import expected_calibration_error, fit_phase26_model, load_phase26_dataset
from src.utils import sha256_file


ROOT = Path(__file__).resolve().parents[1]
DB_RAW = ROOT / "database/cbdb_20260829.sqlite3"
DB_WORKING = ROOT / "database/cbdb_working.sqlite3"
TARGET = ROOT / "data/interim/person_target.parquet"
BASE = ROOT / "data/processed/person_base_v0.parquet"
FEATURE_MASTER = ROOT / "data/modeling/person_phase2_features.parquet"
SPLITS = {
    "primary": ROOT / "data/splits/split_primary_dynasty_target.parquet",
    "random": ROOT / "data/splits/split_random_benchmark.parquet",
    "family": ROOT / "data/splits/split_family_group_robustness.parquet",
    "temporal": ROOT / "data/splits/split_safe_temporal.parquet",
}
EXPECTED_HASHES = {
    "database": "f620ca1a4c794411b81d5039adf5756df129fb9aa0f4509b4c843bb66e0caa2a",
    "working_db": "91ae03a46282eeb6fe39df5ceea5a781de0b893592bd4269cfcb5c5db5117ab8",
    "target": "0da45a25e63c6d241f88ff69399bf12c2de83730e7adc376f3f2ca3e00357112",
    "base": "f3e5fa26c024fc46da312dd77500db8313112d7cf1841214f37ea47a6878e771",
    "phase2_master": "40e6e93320001d520ea0fc541bd4718481809144f0a43cdc31b1f3cbed633d91",
    "primary": "35eb208370aa1dc67e6b6ab66bf52543a75f4d6f4a8aa35e9db3ce70d2f5c0cd",
    "random": "e9abde694fd6ceabafa35e56cbd927a180e3016cacaba0c880c98deb0eb456fc",
    "family": "9f6fb17147a9374ef36527173b74f7985dc12e2ec41c48702a82f6aff13d6387",
    "temporal": "bba7259aaaba40a5728a8d84ea5f5a4d5c633760d5869872aec845f9f7b97cbf",
}
PHASE3_TABLES = ROOT / "outputs/phase3/tables"
PHASE3_LOGS = ROOT / "outputs/phase3/logs"
PHASE3_FIGURES = ROOT / "outputs/phase3/figures"
PHASE3_FIGURE_DATA = ROOT / "outputs/phase3/figure_data"
PHASE3_DATA = ROOT / "data/phase3"
PHASE3_DOCS = ROOT / "docs/phase3"
FROZEN_SNAPSHOT = PHASE3_TABLES / "frozen_phase3_precheck_manifest.json"
SOURCE_STATUS = PHASE3_TABLES / "source_holdout_status.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_phase3_dirs() -> None:
    for path in [
        PHASE3_TABLES,
        PHASE3_LOGS,
        PHASE3_FIGURES,
        PHASE3_FIGURE_DATA,
        ROOT / "outputs/phase3/predictions",
        PHASE3_DATA / "splits",
        PHASE3_DATA / "predictions",
        PHASE3_DOCS,
        ROOT / "paper/figures",
        ROOT / "paper/tables",
        ROOT / "scripts/generated_tables",
        ROOT / "submission",
    ]:
        path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def file_manifest(paths: Iterable[Path]) -> dict[str, str]:
    files: dict[str, str] = {}
    for parent in paths:
        if not parent.exists():
            raise FileNotFoundError(parent)
        for path in sorted(p for p in parent.rglob("*") if p.is_file()):
            files[path.relative_to(ROOT).as_posix()] = sha256_file(path)
    return files


def _check_prior_manifest(path: Path) -> tuple[bool, list[str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    mismatches = []
    for relative, expected in payload["files"].items():
        candidate = ROOT / relative
        actual = sha256_file(candidate) if candidate.exists() else "MISSING"
        if actual != expected:
            mismatches.append(f"{relative}: expected {expected}, observed {actual}")
    return not mismatches, mismatches


def quick_check() -> str:
    con = sqlite3.connect(f"file:{DB_WORKING}?mode=ro", uri=True)
    try:
        con.execute("PRAGMA query_only=ON")
        return str(con.execute("PRAGMA quick_check").fetchone()[0])
    finally:
        con.close()


def frozen_precheck() -> dict[str, Any]:
    """Validate known hashes and snapshot every frozen result file."""
    ensure_phase3_dirs()
    observed = {
        "database": sha256_file(DB_RAW),
        "working_db": sha256_file(DB_WORKING),
        "target": sha256_file(TARGET),
        "base": sha256_file(BASE),
        "phase2_master": sha256_file(FEATURE_MASTER),
        **{name: sha256_file(path) for name, path in SPLITS.items()},
    }
    failures = {
        name: {"expected": EXPECTED_HASHES[name], "observed": value}
        for name, value in observed.items()
        if EXPECTED_HASHES[name] != value
    }
    phase2_ok, phase2_errors = _check_prior_manifest(
        ROOT / "outputs/phase2_5/tables/phase2_preservation_manifest.json"
    )
    phase25_ok, phase25_errors = _check_prior_manifest(
        ROOT / "outputs/phase2_6/tables/phase2_5_preservation_manifest.json"
    )
    if not phase2_ok:
        failures["phase2_outputs"] = phase2_errors
    if not phase25_ok:
        failures["phase2_5_outputs"] = phase25_errors
    db_check = quick_check()
    if db_check != "ok":
        failures["working_db_quick_check"] = db_check
    snapshot = {
        "created_at_utc": utc_now(),
        "status": "PASS" if not failures else "FAIL",
        "observed_core_sha256": observed,
        "working_db_quick_check": db_check,
        "phase2_preservation_manifest_pass": phase2_ok,
        "phase2_5_preservation_manifest_pass": phase25_ok,
        "frozen_files": file_manifest(
            [
                ROOT / "outputs/phase2",
                ROOT / "outputs/phase2_5",
                ROOT / "outputs/phase2_6",
                ROOT / "docs/phase2",
                ROOT / "docs/phase2_5",
                ROOT / "docs/phase2_6",
            ]
        ),
        "failures": failures,
    }
    write_json(FROZEN_SNAPSHOT, snapshot)
    if failures:
        raise RuntimeError(f"Frozen precheck failed: {json.dumps(failures, ensure_ascii=False)}")
    return snapshot


def verify_frozen_snapshot() -> dict[str, Any]:
    baseline = json.loads(FROZEN_SNAPSHOT.read_text(encoding="utf-8"))
    current = file_manifest(
        [
            ROOT / "outputs/phase2",
            ROOT / "outputs/phase2_5",
            ROOT / "outputs/phase2_6",
            ROOT / "docs/phase2",
            ROOT / "docs/phase2_5",
            ROOT / "docs/phase2_6",
        ]
    )
    changed = sorted(
        set(baseline["frozen_files"]) ^ set(current)
        | {
            path
            for path in set(baseline["frozen_files"]) & set(current)
            if baseline["frozen_files"][path] != current[path]
        }
    )
    core = {
        "database": sha256_file(DB_RAW),
        "working_db": sha256_file(DB_WORKING),
        "target": sha256_file(TARGET),
        "base": sha256_file(BASE),
        "phase2_master": sha256_file(FEATURE_MASTER),
        **{name: sha256_file(path) for name, path in SPLITS.items()},
    }
    core_changed = {k: v for k, v in core.items() if v != EXPECTED_HASHES[k]}
    return {
        "pass": not changed and not core_changed and quick_check() == "ok",
        "changed_frozen_files": changed,
        "changed_core_hashes": core_changed,
        "working_db_quick_check": quick_check(),
    }


def readonly_connection() -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{DB_WORKING}?mode=ro", uri=True)
    con.execute("PRAGMA query_only=ON")
    return con


def _object_metadata(con: sqlite3.Connection, name: str) -> dict[str, Any]:
    obj = con.execute(
        "SELECT type, sql FROM sqlite_master WHERE name = ?", (name,)
    ).fetchone()
    if obj is None:
        raise RuntimeError(f"Required source object is absent: {name}")
    columns = [
        {"name": row[1], "type": row[2], "not_null": bool(row[3]), "primary_key_order": row[5]}
        for row in con.execute(f'PRAGMA table_info("{name}")')
    ]
    rows = int(con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0])
    return {"name": name, "object_type": obj[0], "sql": obj[1], "rows": rows, "columns": columns}


def source_linkage_audit() -> dict[str, Any]:
    """Audit the actual source schema without presuming a table name."""
    ensure_phase3_dirs()
    con = readonly_connection()
    try:
        objects = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')")]
        source_objects = sorted(
            name for name in objects if any(token in name.upper() for token in ["SOURCE", "TEXT", "BIBL"])
        )
        metadata = {name: _object_metadata(con, name) for name in source_objects}
        required = {"BIOG_SOURCE_DATA", "TEXT_CODES", "TEXT_BIBLCAT_CODES"}
        missing = sorted(required - set(objects))
        if missing:
            raise RuntimeError(f"Source schema incomplete: {missing}")

        main_values = pd.read_sql_query(
            """SELECT COALESCE(CAST(c_main_source AS TEXT), 'NULL') AS value,
                      COUNT(*) AS n_records, COUNT(DISTINCT c_personid) AS n_people,
                      COUNT(DISTINCT c_textid) AS n_sources
               FROM BIOG_SOURCE_DATA GROUP BY c_main_source ORDER BY c_main_source""",
            con,
        )
        all_counts = con.execute(
            "SELECT COUNT(*), COUNT(DISTINCT c_personid), COUNT(DISTINCT c_textid) FROM BIOG_SOURCE_DATA"
        ).fetchone()
        primary_counts = con.execute(
            """SELECT COUNT(*), COUNT(DISTINCT c_personid), COUNT(DISTINCT c_textid)
               FROM BIOG_SOURCE_DATA WHERE c_main_source = 1"""
        ).fetchone()
        multiplicity = pd.read_sql_query(
            """SELECT n_primary_sources, COUNT(*) AS n_people FROM
                 (SELECT c_personid, COUNT(DISTINCT c_textid) AS n_primary_sources
                  FROM BIOG_SOURCE_DATA WHERE c_main_source = 1 GROUP BY c_personid)
               GROUP BY n_primary_sources ORDER BY n_primary_sources""",
            con,
        )
        orphan_people = int(
            con.execute(
                """SELECT COUNT(DISTINCT s.c_personid) FROM BIOG_SOURCE_DATA s
                   LEFT JOIN BIOG_MAIN b ON s.c_personid=b.c_personid
                   WHERE s.c_main_source=1 AND b.c_personid IS NULL"""
            ).fetchone()[0]
        )
        orphan_sources = int(
            con.execute(
                """SELECT COUNT(DISTINCT s.c_textid) FROM BIOG_SOURCE_DATA s
                   LEFT JOIN TEXT_CODES t ON s.c_textid=t.c_textid
                   WHERE s.c_main_source=1 AND t.c_textid IS NULL"""
            ).fetchone()[0]
        )
    finally:
        con.close()

    rows: list[dict[str, Any]] = []
    for name in source_objects:
        info = metadata[name]
        rows.append({
            "audit_section": "schema_object",
            "object_name": name,
            "field_name": "",
            "value": info["rows"],
            "status": "OBSERVED",
            "evidence": f"SQLite {info['object_type']} row count",
        })
        for column in info["columns"]:
            rows.append({
                "audit_section": "schema_column",
                "object_name": name,
                "field_name": column["name"],
                "value": column["type"],
                "status": "OBSERVED",
                "evidence": "PRAGMA table_info",
            })
    for row in main_values.itertuples(index=False):
        rows.append({
            "audit_section": "main_source_values",
            "object_name": "BIOG_SOURCE_DATA",
            "field_name": "c_main_source",
            "value": row.value,
            "status": "OBSERVED",
            "evidence": f"records={row.n_records}; people={row.n_people}; sources={row.n_sources}",
        })
    pd.DataFrame(rows).to_csv(PHASE3_TABLES / "source_linkage_audit.csv", index=False)
    payload = {
        "created_at_utc": utc_now(),
        "database_sha256": sha256_file(DB_RAW),
        "schema_scan_objects": source_objects,
        "person_source_link_table": "BIOG_SOURCE_DATA",
        "person_id_field": "c_personid",
        "source_id_field": "c_textid",
        "primary_source_field": "c_main_source",
        "sequence_field": None,
        "page_locator_field": "c_pages",
        "source_title_table": "TEXT_CODES",
        "source_title_fields": ["c_title_chn", "c_title", "c_title_trans"],
        "source_type_fields": ["TEXT_CODES.c_text_type_id", "TEXT_CODES.c_bibl_cat_code"],
        "source_type_lookup": "TEXT_BIBLCAT_CODES",
        "all_link_records": int(all_counts[0]),
        "all_linked_people": int(all_counts[1]),
        "all_linked_sources": int(all_counts[2]),
        "primary_link_records": int(primary_counts[0]),
        "primary_linked_people": int(primary_counts[1]),
        "primary_linked_sources": int(primary_counts[2]),
        "people_with_multiple_primary_sources": int(
            multiplicity.loc[multiplicity["n_primary_sources"].gt(1), "n_people"].sum()
        ),
        "primary_source_multiplicity": multiplicity.to_dict(orient="records"),
        "orphan_primary_people": orphan_people,
        "orphan_primary_sources": orphan_sources,
        "primary_field_reliability": "EXPLICIT_BUT_NOT_UNIQUE_PER_PERSON",
        "grouping_decision": (
            "Connected components of the bipartite graph restricted to rows with "
            "c_main_source=1; this preserves the explicit primary-source semantics "
            "while preventing any marked primary source from crossing partitions."
        ),
        "target_used_for_group_definition": False,
    }
    write_json(PHASE3_TABLES / "source_linkage_audit.json", payload)
    return payload


class UnionFind:
    def __init__(self, values: Iterable[int]):
        self.parent = {int(value): int(value) for value in values}
        self.rank = {int(value): 0 for value in values}

    def find(self, value: int) -> int:
        value = int(value)
        root = value
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[value] != value:
            nxt = self.parent[value]
            self.parent[value] = root
            value = nxt
        return root

    def union(self, left: int, right: int) -> None:
        a, b = self.find(left), self.find(right)
        if a == b:
            return
        if self.rank[a] < self.rank[b]:
            a, b = b, a
        self.parent[b] = a
        if self.rank[a] == self.rank[b]:
            self.rank[a] += 1


def stable_group_split(group_id: str, seed: int = 42) -> str:
    digest = hashlib.sha256(f"phase3-source|{seed}|{group_id}".encode("utf-8")).digest()
    value = int.from_bytes(digest[:8], "big") / 2**64
    return "train" if value < 0.70 else ("validation" if value < 0.85 else "test")


def build_source_groups() -> dict[str, Any]:
    """Build target-independent primary-source connected components and assess feasibility."""
    ensure_phase3_dirs()
    if not (PHASE3_TABLES / "source_linkage_audit.json").exists():
        source_linkage_audit()
    con = readonly_connection()
    try:
        edges = pd.read_sql_query(
            """SELECT DISTINCT c_personid AS person_id, c_textid AS source_id
               FROM BIOG_SOURCE_DATA WHERE c_main_source=1
               ORDER BY c_personid, c_textid""",
            con,
            dtype={"person_id": "int64", "source_id": "int64"},
        )
        titles = pd.read_sql_query(
            """SELECT t.c_textid AS source_id, t.c_title_chn, t.c_title,
                      t.c_text_type_id, t.c_bibl_cat_code,
                      b.c_text_cat_desc, b.c_text_cat_desc_chn
               FROM TEXT_CODES t LEFT JOIN TEXT_BIBLCAT_CODES b
                 ON t.c_bibl_cat_code=b.c_text_cat_code""",
            con,
        )
    finally:
        con.close()

    feature_ids = set(pd.read_parquet(FEATURE_MASTER, columns=["person_id"])["person_id"].astype(int))
    edges = edges.loc[edges["person_id"].isin(feature_ids)].drop_duplicates().copy()
    union_find = UnionFind(edges["source_id"].unique())
    for _, source_ids in edges.groupby("person_id", sort=False)["source_id"]:
        values = source_ids.to_numpy(dtype=np.int64)
        if len(values) > 1:
            anchor = int(values[0])
            for other in values[1:]:
                union_find.union(anchor, int(other))

    components: dict[int, list[int]] = {}
    for source_id in edges["source_id"].unique():
        components.setdefault(union_find.find(int(source_id)), []).append(int(source_id))
    canonical = {
        source_id: min(members)
        for members in components.values()
        for source_id in members
    }
    edges["source_group_id"] = edges["source_id"].map(
        lambda value: f"PRIMARY_CC_{canonical[int(value)]}"
    )
    membership = edges[["person_id", "source_group_id"]].drop_duplicates()
    duplicates = membership["person_id"].duplicated(keep=False)
    if duplicates.any():
        raise RuntimeError("Connected-component construction left people in multiple groups")
    membership = membership.sort_values("person_id").reset_index(drop=True)
    membership.to_parquet(PHASE3_DATA / "source_person_group_membership.parquet", index=False)

    group_people = membership.groupby("source_group_id")["person_id"].nunique().rename("n_people")
    source_groups = edges[["source_id", "source_group_id"]].drop_duplicates()
    group_sources = source_groups.groupby("source_group_id")["source_id"].nunique().rename("n_sources")
    representatives = (
        source_groups.sort_values("source_id")
        .groupby("source_group_id", as_index=False)
        .first()
        .merge(titles, on="source_id", how="left")
        .rename(columns={"source_id": "representative_source_id"})
    )
    summary = (
        pd.concat([group_people, group_sources], axis=1)
        .reset_index()
        .merge(representatives, on="source_group_id", how="left")
        .sort_values(["n_people", "source_group_id"], ascending=[False, True])
        .reset_index(drop=True)
    )
    eligible = int(membership["person_id"].nunique())
    summary["population_fraction"] = summary["n_people"] / eligible
    summary["rank_by_people"] = np.arange(1, len(summary) + 1)
    summary.to_csv(PHASE3_TABLES / "source_group_summary.csv", index=False)

    largest = int(summary["n_people"].max()) if len(summary) else 0
    largest_fraction = largest / eligible if eligible else 1.0
    structural_checks = {
        "eligible_people_at_least_20000": eligible >= 20_000,
        "source_groups_at_least_30": len(summary) >= 30,
        "largest_group_at_most_20_percent": largest_fraction <= 0.20,
        "group_definition_target_independent": True,
        "split_not_performance_selected": True,
        "one_group_per_person": not membership["person_id"].duplicated().any(),
    }
    reasons = [name for name, passed in structural_checks.items() if not passed]
    status = "STRUCTURALLY_FEASIBLE_PENDING_SPLIT_CLASS_CHECK" if not reasons else "SOURCE_GROUP_CONFIRMATION_NOT_FEASIBLE"

    split_summary_records: list[dict[str, Any]] = []
    overlap_payload: dict[str, Any] = {
        "status": "NOT_APPLICABLE_NOT_FEASIBLE",
        "group_overlap_count": None,
        "person_overlap_count": 0,
    }
    split_path = PHASE3_DATA / "splits/split_source_group_confirmation.parquet"
    if not reasons:
        group_split = {group: stable_group_split(group, 42) for group in summary["source_group_id"]}
        split = membership.copy()
        split["split"] = split["source_group_id"].map(group_split)
        # Only after target-independent assignment do we inspect label counts.
        target = pd.read_parquet(TARGET, columns=["person_id", "target_entry"]).rename(
            columns={"target_entry": "target_entry_v1"}
        )
        assessed = split.merge(target, on="person_id", how="left", validate="one_to_one")
        for partition, part in assessed.groupby("split"):
            split_summary_records.append({
                "split": partition,
                "n_people": int(len(part)),
                "n_groups": int(part["source_group_id"].nunique()),
                "positive_count": int(part["target_entry_v1"].sum()),
                "negative_count": int((1 - part["target_entry_v1"]).sum()),
                "positive_prevalence": float(part["target_entry_v1"].mean()),
            })
        test = next((x for x in split_summary_records if x["split"] == "test"), None)
        class_ok = bool(test and test["positive_count"] >= 1000 and test["negative_count"] >= 1000)
        if not class_ok:
            reasons.append("test_positive_and_negative_counts_at_least_1000")
            status = "SOURCE_GROUP_CONFIRMATION_NOT_FEASIBLE"
        else:
            status = "SOURCE_GROUP_CONFIRMATION_FEASIBLE"
            split.to_parquet(split_path, index=False)
            pd.DataFrame(split_summary_records).to_csv(
                PHASE3_TABLES / "source_split_summary.csv", index=False
            )
            partition_groups = {
                part: set(values)
                for part, values in split.groupby("split")["source_group_id"]
            }
            pairwise = {
                f"{a}_{b}": len(partition_groups.get(a, set()) & partition_groups.get(b, set()))
                for a, b in [("train", "validation"), ("train", "test"), ("validation", "test")]
            }
            overlap_payload = {
                "status": "PASS" if sum(pairwise.values()) == 0 else "FAIL",
                "group_overlap_count": int(sum(pairwise.values())),
                "person_overlap_count": 0,
                "pairwise_group_overlap": pairwise,
                "split_algorithm": "SHA256(source_group_id, seed=42) thresholds 0.70/0.85",
                "target_used_for_assignment": False,
                "performance_used_for_assignment": False,
            }
            write_json(PHASE3_TABLES / "source_split_overlap_check.json", overlap_payload)

    payload = {
        "created_at_utc": utc_now(),
        "status": status,
        "grouping_protocol": "connected_components_of_explicit_primary_source_edges",
        "eligible_people": eligible,
        "coverage_of_feature_master": eligible / len(feature_ids),
        "source_groups": int(len(summary)),
        "largest_group_people": largest,
        "largest_group_fraction": largest_fraction,
        "primary_source_edges": int(len(edges)),
        "source_ids": int(edges["source_id"].nunique()),
        "structural_checks": structural_checks,
        "test_class_check": (
            next((x for x in split_summary_records if x["split"] == "test"), None)
            if split_summary_records else "NOT_RUN_STRUCTURAL_GATE_FAILED"
        ),
        "failed_criteria": reasons,
        "target_used_for_group_definition": False,
        "target_used_for_split_assignment": False,
        "model_performance_used_for_split_assignment": False,
        "split_seed": 42,
        "split_path": split_path.relative_to(ROOT).as_posix() if split_path.exists() else None,
        "source_overlap_check": overlap_payload,
    }
    write_json(SOURCE_STATUS, payload)
    _write_source_feasibility_doc(payload)
    return payload


def _write_source_feasibility_doc(status: dict[str, Any]) -> None:
    failed = status["failed_criteria"]
    failure_lines = "\n".join(f"- `{value}`" for value in failed) if failed else "- None."
    outcome = (
        "The confirmation is feasible and may be run once with the locked models."
        if status["status"] == "SOURCE_GROUP_CONFIRMATION_FEASIBLE"
        else "No source-group model is run because the prespecified gate failed."
    )
    text = f"""# Source-holdout feasibility audit

**Status:** `{status['status']}`

## Audited schema

The read-only SQLite schema contains `BIOG_SOURCE_DATA`, linking `c_personid` to
`c_textid`.  The explicit `c_main_source` flag identifies primary-source rows;
`TEXT_CODES` supplies titles and text/bibliographic type fields, with
`TEXT_BIBLCAT_CODES` as a category lookup.  There is no sequence field;
`c_pages` is a locator, not an ordering rule.

Because some people have multiple rows marked as primary, groups are connected
components of the person--source bipartite graph restricted to
`c_main_source=1`.  This target-independent rule neither selects a minimum/first
source per person nor allows a marked primary source to cross partitions.

## Prespecified gate

- Eligible linked people: **{status['eligible_people']:,}**
- Coverage of the 661,124-person feature master: **{status['coverage_of_feature_master']:.2%}**
- Connected source groups: **{status['source_groups']:,}**
- Largest group: **{status['largest_group_people']:,}** people (**{status['largest_group_fraction']:.2%}**)
- Primary-source edges: **{status['primary_source_edges']:,}**
- Target used to define groups or assign partitions: **No**
- Model performance used to choose the split: **No**

Failed criteria:

{failure_lines}

## Decision

{outcome}  This audit concerns source-group distribution shift only.  Even a
successful result would not constitute external ground-truth validation of the
latent historical state $T$.
"""
    (PHASE3_DOCS / "source_holdout_feasibility.md").write_text(text, encoding="utf-8")


def _bootstrap_metric_ci(y: np.ndarray, p: np.ndarray, seed: int = 42, n: int = 500) -> dict[str, tuple[float, float]]:
    rng = np.random.default_rng(seed)
    pos = np.flatnonzero(y == 1)
    neg = np.flatnonzero(y == 0)
    values = {name: [] for name in ["roc_auc", "pr_auc", "log_loss", "brier_score", "ece"]}
    for _ in range(n):
        idx = np.concatenate([rng.choice(pos, len(pos), replace=True), rng.choice(neg, len(neg), replace=True)])
        yy, pp = y[idx], p[idx]
        values["roc_auc"].append(roc_auc_score(yy, pp))
        values["pr_auc"].append(average_precision_score(yy, pp))
        values["log_loss"].append(log_loss(yy, pp, labels=[0, 1]))
        values["brier_score"].append(brier_score_loss(yy, pp))
        values["ece"].append(expected_calibration_error(yy, pp))
    return {name: tuple(np.quantile(vals, [0.025, 0.975]).astype(float)) for name, vals in values.items()}


def run_source_confirmation() -> dict[str, Any]:
    """Run exactly H_STRUCT and D5_MAIN once, only if the gate passed."""
    status = json.loads(SOURCE_STATUS.read_text(encoding="utf-8"))
    if status["status"] != "SOURCE_GROUP_CONFIRMATION_FEASIBLE":
        payload = {
            "status": "SOURCE_GROUP_CONFIRMATION_NOT_FEASIBLE",
            "models_trained": [],
            "reason": status["failed_criteria"],
        }
        write_json(PHASE3_TABLES / "source_group_confirmation_status.json", payload)
        (PHASE3_DOCS / "source_group_confirmation.md").write_text(
            "# Source-group distribution-shift confirmation\n\n"
            "**Status:** `SOURCE_GROUP_CONFIRMATION_NOT_FEASIBLE`\n\n"
            "No model was trained because the prespecified feasibility gate failed. "
            "See `source_holdout_feasibility.md` for the schema evidence and exact reason.\n",
            encoding="utf-8",
        )
        return payload

    split_path = ROOT / status["split_path"]
    dataset = load_phase26_dataset()
    metrics: list[dict[str, Any]] = []
    predictions: list[pd.DataFrame] = []
    for model_id in ["H_STRUCT", "D5_MAIN"]:
        run = fit_phase26_model(
            dataset,
            "Global",
            model_id,
            seed=42,
            split_path=split_path,
            split_protocol="source_group_distribution_shift",
        )
        pred = run.test_predictions.copy()
        probability = pred["y_probability_calibrated_if_available"].to_numpy(float)
        y = pred["y_true"].to_numpy(int)
        ci = _bootstrap_metric_ci(y, probability, seed=42, n=500)
        row = dict(run.metric)
        row.update({
            "evaluation_name": "Source-group distribution-shift confirmation",
            "positive_prevalence": float(y.mean()),
            "ece": expected_calibration_error(y, probability),
            "bootstrap_n": 500,
        })
        for metric_name, (lower, upper) in ci.items():
            row[f"{metric_name}_ci_lower"] = lower
            row[f"{metric_name}_ci_upper"] = upper
        metrics.append(row)
        predictions.append(pred)
    result = pd.DataFrame(metrics)
    result.to_csv(PHASE3_TABLES / "source_group_confirmation_results.csv", index=False)
    pd.concat(predictions, ignore_index=True).to_parquet(
        ROOT / "outputs/phase3/predictions/source_group_predictions.parquet", index=False
    )
    payload = {"status": "PASS", "models_trained": ["H_STRUCT", "D5_MAIN"], "seed": 42}
    write_json(PHASE3_TABLES / "source_group_confirmation_status.json", payload)
    lines = [
        "# Source-group distribution-shift confirmation",
        "",
        "This is a source-group distribution-shift confirmation, not external or ground-truth validation.",
        "Only the locked H_STRUCT and D5_MAIN definitions were fitted with seed 42; train-only derived features were refitted.",
        "",
        result.to_markdown(index=False),
        "",
    ]
    (PHASE3_DOCS / "source_group_confirmation.md").write_text("\n".join(lines), encoding="utf-8")
    return payload


def environment_payload() -> dict[str, Any]:
    import catboost
    import matplotlib
    import pyarrow
    import shap
    import sklearn

    return {
        "created_at_utc": utc_now(),
        "python": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "sqlite": sqlite3.sqlite_version,
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
        "catboost": catboost.__version__,
        "shap": shap.__version__,
        "matplotlib": matplotlib.__version__,
        "pyarrow": pyarrow.__version__,
        "seed": 42,
    }
