#!/usr/bin/env python3
"""Build deterministic, manifest-verified Phase 3.1 submission archives."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 120 * 1024 * 1024
FIXED_TIME = (2026, 9, 1, 0, 0, 0)
SUBMISSION = ROOT / "submission/cbdb_final_submission_nature_revised.zip"
REVIEW = ROOT / "review_bundles/cbdb_final_paper_review_bundle_nature_revised.zip"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def add(entries: dict[str, Path], path: Path, archive_path: str | None = None) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    arc = archive_path or path.relative_to(ROOT).as_posix()
    if arc in entries and entries[arc] != path:
        raise RuntimeError(f"duplicate archive path: {arc}")
    entries[arc] = path


def add_tree(entries: dict[str, Path], parent: Path, suffixes: set[str] | None = None) -> None:
    if not parent.exists():
        return
    for path in sorted(parent.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        if suffixes is not None and path.suffix.lower() not in suffixes:
            continue
        add(entries, path)


def category(path: str) -> str:
    if "figures/" in path or "figure_data/" in path:
        return "figure"
    if path.startswith("paper/"):
        return "paper"
    if path.startswith("docs/"):
        return "report"
    if path.startswith("outputs/") or path.startswith("data/phase3_1/"):
        return "result"
    if path.startswith("scripts/") or path.startswith("src/"):
        return "code"
    if path.startswith("tests/"):
        return "test"
    if path.startswith("configs/"):
        return "configuration"
    return "project"


def manifest(entries: dict[str, Path]) -> tuple[bytes, bytes]:
    rows = []
    for arc, path in sorted(entries.items()):
        rows.append({
            "relative_path": arc,
            "file_size_bytes": path.stat().st_size,
            "sha256": sha256(path),
            "category": category(arc),
            "description": "Phase 3.1 audited payload",
        })
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=["relative_path", "file_size_bytes", "sha256", "category", "description"])
    writer.writeheader()
    writer.writerows(rows)
    lines = [
        "# ZIP manifest", "",
        "Every payload file is listed below. The manifest files themselves are excluded to avoid recursive hashes.", "",
        "| relative_path | bytes | sha256 | category | description |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(f"| `{row['relative_path']}` | {row['file_size_bytes']} | `{row['sha256']}` | {row['category']} | {row['description']} |")
    return stream.getvalue().encode("utf-8"), ("\n".join(lines) + "\n").encode("utf-8")


def write_bytes(archive: zipfile.ZipFile, arc: str, data: bytes) -> None:
    info = zipfile.ZipInfo(arc, FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data)


def validate(path: Path) -> dict[str, object]:
    errors: list[str] = []
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            errors.append(f"integrity:{bad}")
        names = set(archive.namelist())
        rows = list(csv.DictReader(archive.read("ZIP_MANIFEST.csv").decode("utf-8").splitlines()))
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
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "size_bytes": path.stat().st_size,
        "file_count": len(names),
        "sha256": sha256(path),
        "unzip_status": "PASS" if not errors else "FAIL",
        "manifest_status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }


def build(path: Path, entries: dict[str, Path]) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    csv_bytes, md_bytes = manifest(entries)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for arc, source in sorted(entries.items()):
            write_bytes(archive, arc, source.read_bytes())
        write_bytes(archive, "ZIP_MANIFEST.csv", csv_bytes)
        write_bytes(archive, "ZIP_MANIFEST.md", md_bytes)
    temporary.replace(path)
    if path.stat().st_size > MAX_BYTES:
        raise RuntimeError(f"archive exceeds 120 MiB: {path}")
    result = validate(path)
    if result["errors"]:
        raise RuntimeError(json.dumps(result, ensure_ascii=False))
    path.with_suffix(".sha256").write_text(f"{result['sha256']}  {path.name}\n", encoding="utf-8")
    return result


def submission_entries() -> dict[str, Path]:
    entries: dict[str, Path] = {}
    for name in [
        "cbdb_kdd_style_author_revised.pdf", "main_author_revised.tex", "main_body_revised.tex",
        "references_revised.bib", "reference_audit_revised.csv",
    ]:
        add(entries, ROOT / "paper/revised" / name)
    add_tree(entries, ROOT / "paper/revised/figures", {".png", ".pdf", ".svg"})
    add_tree(entries, ROOT / "paper/revised/tables", {".tex"})
    add(entries, ROOT / "docs/phase3_1/PACKAGE_README.md", "README.md")
    add(entries, ROOT / "docs/phase3_1/DATA_USAGE.md", "DATA_USAGE.md")
    add(entries, ROOT / "submission/LICENSE", "LICENSE")
    for name in ["requirements.txt", "environment.yml"]:
        add(entries, ROOT / name)
    add_tree(entries, ROOT / "configs")
    add_tree(entries, ROOT / "scripts", {".py", ".sh", ".tex"})
    add_tree(entries, ROOT / "src", {".py"})
    add_tree(entries, ROOT / "tests", {".py"})
    add_tree(entries, ROOT / "outputs/phase3_1/tables")
    add_tree(entries, ROOT / "outputs/phase3_1/figure_data")
    for name in [
        "revision_summary.md", "final_claim_evidence_map.md", "nature_statistics_audit.md",
        "nature_figure_audit.md", "nature_data_audit.md",
    ]:
        add(entries, ROOT / "docs/phase3_1" / name)
    return entries


def review_entries() -> dict[str, Path]:
    entries: dict[str, Path] = {}
    add(entries, ROOT / "docs/phase3_1/REVIEW_INDEX.md", "REVIEW_INDEX.md")
    for name in [
        "cbdb_kdd_style_author_revised.pdf", "cbdb_kdd_style_anonymous_revised.pdf",
        "main_author_revised.tex", "main_anonymous_revised.tex", "main_body_revised.tex",
        "references_revised.bib", "reference_audit_revised.csv",
    ]:
        add(entries, ROOT / "paper/revised" / name)
    add_tree(entries, ROOT / "paper/revised/figures", {".png", ".pdf", ".svg"})
    add_tree(entries, ROOT / "paper/revised/tables", {".tex"})
    for name in [
        "cbdb_kdd_style_author_revised.log", "cbdb_kdd_style_anonymous_revised.log",
        "cbdb_kdd_style_author_revised.build.log", "cbdb_kdd_style_anonymous_revised.build.log",
        "cbdb_kdd_style_author_revised.blg", "cbdb_kdd_style_anonymous_revised.blg",
    ]:
        add(entries, ROOT / "paper/revised" / name)
    add_tree(entries, ROOT / "docs/phase3_1")
    add_tree(entries, ROOT / "outputs/phase3_1/tables")
    add_tree(entries, ROOT / "outputs/phase3_1/figure_data")
    add_tree(entries, ROOT / "outputs/phase3_1/figures", {".png", ".pdf", ".svg"})
    add_tree(entries, ROOT / "outputs/phase3_1/logs")
    add(entries, ROOT / "data/phase3_1/final_model_test_predictions.parquet")
    for path in sorted((ROOT / "scripts").glob("*.py")):
        if path.name[:2].isdigit() and 61 <= int(path.name[:2]) <= 66:
            add(entries, path)
    add(entries, ROOT / "scripts/run_phase3_1_nature_revision.sh")
    for path in sorted((ROOT / "tests").glob("test_phase3_1_*.py")):
        add(entries, path)
    for name in ["requirements.txt", "environment.yml"]:
        add(entries, ROOT / name)
    add_tree(entries, ROOT / "configs")
    upstream = [
        "outputs/phase3/tables/main_model_performance.csv",
        "outputs/phase3/tables/robustness_summary.csv",
        "outputs/phase3/tables/source_holdout_status.json",
        "outputs/phase2_5/tables/family_decomposition_deltas.csv",
        "outputs/phase2_5/tables/paired_bootstrap_results.csv",
        "outputs/phase2_6/tables/final_model_metrics.csv",
        "outputs/phase2_6/tables/final_model_calibration.csv",
        "outputs/phase2_6/tables/final_feature_coverage.csv",
        "outputs/phase2_6/tables/matched_random_vs_spatial_results.csv",
        "outputs/phase2_6/tables/multiseed_delta_summary.csv",
        "outputs/tables/entry_vs_posting_contingency.csv",
    ]
    for relative in upstream:
        add(entries, ROOT / relative)
    return entries


def run_audit() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts/65_phase3_1_audits.py")], cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=["submission", "review", "both"], default="both")
    parser.add_argument("--finalize", action="store_true")
    args = parser.parse_args()
    results = []
    if args.kind in {"submission", "both"}:
        results.append(build(SUBMISSION, submission_entries()))
    if args.kind in {"review", "both"}:
        results.append(build(REVIEW, review_entries()))
    if args.finalize:
        if not SUBMISSION.exists() or not REVIEW.exists():
            raise RuntimeError("both preliminary archives are required before finalization")
        run_audit()
        results = [build(SUBMISSION, submission_entries()), build(REVIEW, review_entries())]
        run_audit()
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
