"""Deterministic, size-bounded packaging helpers for Phase 3."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path
from typing import Iterable

from src.phase3 import ROOT
from src.utils import sha256_file


MAX_ZIP_BYTES = 120 * 1024 * 1024
FIXED_ZIP_TIME = (2026, 8, 31, 0, 0, 0)


def _files(parent: Path, suffixes: set[str] | None = None) -> list[Path]:
    if not parent.exists():
        return []
    return sorted(
        path
        for path in parent.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and ".pytest_cache" not in path.parts
        and (suffixes is None or path.suffix.lower() in suffixes)
    )


def _add(entries: dict[str, Path], path: Path, archive_path: str | None = None) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    arc = archive_path or path.relative_to(ROOT).as_posix()
    if arc in entries and entries[arc] != path:
        raise RuntimeError(f"Duplicate archive path: {arc}")
    entries[arc] = path


def _add_tree(
    entries: dict[str, Path], parent: Path, suffixes: set[str] | None = None
) -> None:
    for path in _files(parent, suffixes):
        _add(entries, path)


def _category(path: str) -> str:
    if path.startswith("paper/figures") or path.startswith("outputs/phase3/figures"):
        return "figure"
    if path.startswith("paper/"):
        return "paper"
    if path.startswith("outputs/"):
        return "result"
    if path.startswith("docs/"):
        return "report"
    if path.startswith("scripts/") or path.startswith("src/"):
        return "code"
    if path.startswith("tests/"):
        return "test"
    if path.startswith("configs/"):
        return "configuration"
    if path.endswith(".log"):
        return "log"
    return "project"


def _description(path: str) -> str:
    category = _category(path)
    return {
        "figure": "Locally generated paper figure or figure input",
        "paper": "Final manuscript, source, reference, or generated table",
        "result": "Audited result table, provenance record, or invariant",
        "report": "Scientific report or reproducibility documentation",
        "code": "Pipeline, plotting, paper-generation, or packaging code",
        "test": "Automated scientific or packaging test",
        "configuration": "Frozen feature, model, or protocol configuration",
        "log": "Execution or validation log",
        "project": "Project metadata or reproducibility instruction",
    }[category]


def _manifest(entries: dict[str, Path]) -> tuple[bytes, bytes, list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    for arc, path in sorted(entries.items()):
        rows.append(
            {
                "relative_path": arc,
                "file_size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "category": _category(arc),
                "description": _description(arc),
            }
        )
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=["relative_path", "file_size_bytes", "sha256", "category", "description"],
    )
    writer.writeheader()
    writer.writerows(rows)
    csv_bytes = stream.getvalue().encode("utf-8")
    md_lines = [
        "# ZIP manifest",
        "",
        "The manifest covers every payload file. The two manifest files are excluded to avoid recursive hashes.",
        "",
        "| relative_path | bytes | sha256 | category | description |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for row in rows:
        md_lines.append(
            f"| `{row['relative_path']}` | {row['file_size_bytes']} | `{row['sha256']}` | "
            f"{row['category']} | {row['description']} |"
        )
    return csv_bytes, ("\n".join(md_lines) + "\n").encode("utf-8"), rows


def _zip_write_bytes(archive: zipfile.ZipFile, arc: str, data: bytes) -> None:
    info = zipfile.ZipInfo(arc, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data)


def build_zip(destination: Path, entries: dict[str, Path]) -> dict[str, object]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    csv_bytes, md_bytes, rows = _manifest(entries)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for arc, path in sorted(entries.items()):
            _zip_write_bytes(archive, arc, path.read_bytes())
        _zip_write_bytes(archive, "ZIP_MANIFEST.csv", csv_bytes)
        _zip_write_bytes(archive, "ZIP_MANIFEST.md", md_bytes)
    temporary.replace(destination)
    if destination.stat().st_size > MAX_ZIP_BYTES:
        raise RuntimeError(f"ZIP exceeds 120 MiB: {destination}")
    validation = validate_zip(destination, validate_manifest=True)
    if not validation["pass"]:
        raise RuntimeError(f"ZIP validation failed: {json.dumps(validation, ensure_ascii=False)}")
    digest = sha256_file(destination)
    destination.with_suffix(".sha256").write_text(f"{digest}  {destination.name}\n", encoding="utf-8")
    return {
        "path": destination.relative_to(ROOT).as_posix(),
        "size_bytes": destination.stat().st_size,
        "file_count": len(rows) + 2,
        "sha256": digest,
        "unzip_status": "PASS",
        "manifest_status": "PASS",
    }


def validate_zip(path: Path, validate_manifest: bool = True) -> dict[str, object]:
    payload: dict[str, object] = {
        "path": path.relative_to(ROOT).as_posix() if path.is_absolute() else path.as_posix(),
        "exists": path.is_file(),
        "under_120_mib": path.is_file() and path.stat().st_size <= MAX_ZIP_BYTES,
        "zip_integrity": False,
        "manifest_hashes": False,
        "pass": False,
    }
    if not path.is_file():
        return payload
    try:
        with zipfile.ZipFile(path) as archive:
            payload["zip_integrity"] = archive.testzip() is None
            names = set(archive.namelist())
            if validate_manifest and "ZIP_MANIFEST.csv" in names:
                rows = list(csv.DictReader(io.TextIOWrapper(archive.open("ZIP_MANIFEST.csv"), encoding="utf-8")))
                errors = []
                for row in rows:
                    relative = row["relative_path"]
                    if relative not in names:
                        errors.append(f"missing:{relative}")
                        continue
                    data = archive.read(relative)
                    if len(data) != int(row["file_size_bytes"]):
                        errors.append(f"size:{relative}")
                    if hashlib.sha256(data).hexdigest() != row["sha256"]:
                        errors.append(f"hash:{relative}")
                payload["manifest_hashes"] = not errors
                payload["manifest_entries"] = len(rows)
                payload["manifest_errors"] = errors
            elif not validate_manifest:
                payload["manifest_hashes"] = True
            payload["file_count"] = len(names)
    except (OSError, zipfile.BadZipFile, KeyError, ValueError) as exc:
        payload["error"] = str(exc)
    payload["pass"] = bool(
        payload["exists"]
        and payload["under_120_mib"]
        and payload["zip_integrity"]
        and payload["manifest_hashes"]
    )
    return payload


def write_support_files() -> None:
    submission = ROOT / "submission"
    submission.mkdir(parents=True, exist_ok=True)
    submission.joinpath("README.md").write_text(
        """# CBDB Phase 3 reproducible submission

This package supports the paper *Who Leaves a Recorded Path into Government? A Documentation-Aware Data Mining Study of CBDB*.

The target is observed `ENTRY_DATA` record presence (E), not latent true historical entry (T). The full CBDB database and the 661,124-row feature master are intentionally excluded. Run `python scripts/01_download_cbdb.py` to obtain the official release and verify its declared hash, then run the phase scripts in order. With the frozen Phase 1--2.6 artifacts present, `bash scripts/run_phase3.sh` rebuilds and validates Phase 3.

Author: Xiaoke Lu, ShanghaiTech University. Canonical seed: 42.
""",
        encoding="utf-8",
    )
    submission.joinpath("DATA_USAGE.md").write_text(
        """# Data usage

CBDB is obtained from the official CBDB release channel and is not redistributed in this archive. Users must review the current official CBDB terms and citation guidance. The provided downloader records provenance and checks SHA256. Outputs describe CBDB-covered records and must not be interpreted as population-level historical rates or causal effects.
""",
        encoding="utf-8",
    )
    submission.joinpath("LICENSE").write_text(
        """MIT License

Copyright (c) 2026 Xiaoke Lu

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the \"Software\"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, subject to the condition that this notice is included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND. This license covers project code and documentation only; it does not grant rights to redistribute CBDB data.
""",
        encoding="utf-8",
    )


def submission_entries() -> dict[str, Path]:
    write_support_files()
    entries: dict[str, Path] = {}
    _add(entries, ROOT / "paper/cbdb_kdd_style_author.pdf")
    for name in ["main_author.tex", "references.bib", "reference_audit.csv"]:
        _add(entries, ROOT / "paper" / name)
    _add_tree(entries, ROOT / "paper/figures", {".png", ".pdf", ".svg"})
    _add_tree(entries, ROOT / "paper/tables", {".tex"})
    _add(entries, ROOT / "submission/README.md", "README.md")
    _add(entries, ROOT / "submission/DATA_USAGE.md", "DATA_USAGE.md")
    _add(entries, ROOT / "submission/LICENSE", "LICENSE")
    for name in ["requirements.txt", "environment.yml"]:
        _add(entries, ROOT / name)
    _add_tree(entries, ROOT / "configs")
    _add_tree(entries, ROOT / "scripts", {".py", ".sh", ".tex"})
    _add_tree(entries, ROOT / "src", {".py"})
    _add_tree(entries, ROOT / "tests", {".py"})
    _add_tree(entries, ROOT / "docs/phase3")
    _add_tree(entries, ROOT / "outputs/phase3/tables")
    _add_tree(entries, ROOT / "outputs/phase3/figure_data")
    _add_tree(entries, ROOT / "outputs/phase3/figures", {".png", ".pdf", ".svg"})
    upstream = [
        "outputs/tables/entry_vs_posting_contingency.csv",
        "outputs/tables/target_by_dynasty.csv",
        "outputs/phase2/tables/model_metrics.csv",
        "outputs/phase2_5/tables/personal_decomposition_deltas.csv",
        "outputs/phase2_5/tables/family_decomposition_deltas.csv",
        "outputs/phase2_5/tables/family_decomposition_results.csv",
        "outputs/phase2_5/tables/family_holdout_decomposition_results.csv",
        "outputs/phase2_5/tables/paired_bootstrap_results.csv",
        "outputs/phase2_6/tables/final_model_metrics.csv",
        "outputs/phase2_6/tables/final_model_feature_lists.csv",
        "outputs/phase2_6/tables/final_model_calibration.csv",
        "outputs/phase2_6/tables/final_gender_entry_rates.csv",
        "outputs/phase2_6/tables/entry_category_by_dynasty_records.csv",
        "outputs/phase2_6/tables/entry_category_by_dynasty_people.csv",
        "outputs/phase2_6/tables/address_semantics_deltas.csv",
        "outputs/phase2_6/tables/matched_random_vs_spatial_results.csv",
        "outputs/phase2_6/tables/multiseed_delta_summary.csv",
        "outputs/phase2_6/shap/shap_group_summary.csv",
    ]
    for relative in upstream:
        _add(entries, ROOT / relative)
    tree = ROOT / "submission/project_tree.txt"
    tree.write_text("\n".join(sorted(entries)) + "\n", encoding="utf-8")
    _add(entries, tree, "project_tree.txt")
    return entries


def write_review_index() -> Path:
    source = json.loads((ROOT / "outputs/phase3/tables/source_holdout_status.json").read_text())
    quality = json.loads((ROOT / "outputs/phase3/tables/paper_quality_check.json").read_text())
    path = ROOT / "review_bundles/REVIEW_INDEX.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# CBDB final paper review index

## Status and task

- Project: Phase 3 final scientific validation and KDD-style paper
- Data version: `cbdb_20260829.sqlite3`
- E: observed `ENTRY_DATA` record presence; P: observed valid posting presence; T: latent true historical entry. E != T, P != T, and E != P.
- Main paper: `paper/cbdb_kdd_style_author.pdf`
- Anonymous paper: `paper/cbdb_kdd_style_anonymous.pdf`

## Locked models and main result

- `H_STRUCT`: historical structural benchmark.
- `D5_MAIN`: designated main predictive model; Global ROC-AUC 0.936956 and PR-AUC 0.882535.
- `D6_UPPER`: database-internal record-structure upper bound.

## Recommended reading order

1. Author PDF and `docs/phase3/final_report_chinese_summary.md`.
2. `docs/phase3/final_scientific_validation.md` and the five generated tables.
3. Figure manifest and figure data.
4. Source feasibility audit, then Phase 2.6 interpretation reports.

## Critical limitations

The model predicts E, not T. CBDB is not a random historical-population sample; documentation and selection processes are strong signals. Spatial transport declines. Frozen temporal and Qing performance were unavailable, so Phase 3 did not create post-hoc estimates. Source confirmation is `{source['status']}` because the largest connected component contains {source['largest_group_people']:,} people ({source['largest_group_fraction']:.2%}).

## Key artifacts

- Performance: `outputs/phase3/tables/main_model_performance.csv`
- Ablation: `outputs/phase3/tables/grouped_ablation_summary.csv`
- Robustness: `outputs/phase3/tables/robustness_summary.csv`
- Figures: `paper/figures/` and `outputs/phase3/tables/figure_manifest.csv`
- Paper QA: main content {quality['author']['main_content_pages']} pages; `outputs/phase3/tables/paper_quality_check.json`
""",
        encoding="utf-8",
    )
    return path


def review_entries() -> dict[str, Path]:
    index = write_review_index()
    entries: dict[str, Path] = {}
    _add(entries, index, "REVIEW_INDEX.md")
    for name in [
        "cbdb_kdd_style_author.pdf",
        "cbdb_kdd_style_anonymous.pdf",
        "main_author.tex",
        "main_anonymous.tex",
        "references.bib",
        "reference_audit.csv",
    ]:
        _add(entries, ROOT / "paper" / name)
    _add_tree(entries, ROOT / "paper/figures", {".png", ".pdf", ".svg"})
    _add_tree(entries, ROOT / "paper/tables", {".tex"})
    _add_tree(entries, ROOT / "docs/phase3")
    for name in ["final_data_analysis.md", "final_model_report.md", "final_interpretation_and_limitations.md"]:
        _add(entries, ROOT / "docs/phase2_6" / name)
    _add_tree(entries, ROOT / "outputs/phase3/tables")
    _add_tree(entries, ROOT / "outputs/phase3/figures", {".png", ".pdf", ".svg"})
    _add_tree(entries, ROOT / "outputs/phase3/figure_data")
    prior = [
        "outputs/phase2_6/tables/final_model_metrics.csv",
        "outputs/phase2_6/tables/final_model_feature_lists.csv",
        "outputs/phase2_6/tables/multiseed_delta_summary.csv",
        "outputs/phase2_6/tables/matched_random_vs_spatial_results.csv",
        "outputs/phase2_5/tables/paired_bootstrap_results.csv",
        "outputs/phase2_5/tables/target_sensitivity_results.csv",
    ]
    for relative in prior:
        _add(entries, ROOT / relative)
    _add(
        entries,
        ROOT / "outputs/phase2_5/tables/calibration_audit.csv",
        "outputs/phase2_5/tables/calibration_results.csv",
    )
    for name in [
        "shap_group_summary.csv",
        "shap_feature_summary.csv",
        "shap_direction_summary.csv",
        "shap_additivity_check.json",
    ]:
        _add(entries, ROOT / "outputs/phase2_6/shap" / name)
    _add_tree(entries, ROOT / "configs")
    _add_tree(entries, ROOT / "src", {".py"})
    _add_tree(entries, ROOT / "tests", {".py"})
    for path in sorted((ROOT / "scripts").glob("*.py")):
        if path.name[:2].isdigit() and 53 <= int(path.name[:2]) <= 60:
            _add(entries, path)
    _add(entries, ROOT / "scripts/run_phase3.sh")
    for relative in [
        "outputs/phase3/logs/run_phase3.log",
        "outputs/phase3/logs/pytest_phase3.log",
        "outputs/phase3/logs/latex_author.log",
        "outputs/phase3/logs/latex_anonymous.log",
    ]:
        path = ROOT / relative
        if path.exists():
            _add(entries, path)
    for name in ["requirements.txt", "environment.yml"]:
        _add(entries, ROOT / name)
    tree = ROOT / "review_bundles/project_tree.txt"
    tree.write_text("\n".join(sorted(entries)) + "\n", encoding="utf-8")
    _add(entries, tree, "project_tree.txt")
    return entries
