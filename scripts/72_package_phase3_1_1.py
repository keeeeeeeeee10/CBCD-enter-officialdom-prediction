#!/usr/bin/env python3
"""Build deterministic Phase 3.1.1 submission and compact review archives."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "submission/cbdb_final_submission_phase3_1_1.zip"
LATEST = ROOT / "exports/cbdb_phase3_1_1_latest_results.zip"
REPORT = ROOT / "outputs/phase3_1_1/tables/release_validation_report.json"
FIXED_TIME = (2026, 9, 1, 0, 0, 0)
LATEST_MAX_BYTES = 20 * 1024 * 1024
Entry = Path | bytes


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def data(entry: Entry) -> bytes:
    return entry.read_bytes() if isinstance(entry, Path) else entry


def add(entries: dict[str, Entry], archive_path: str, source: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    if archive_path in entries:
        raise RuntimeError(f"Duplicate archive path: {archive_path}")
    entries[archive_path] = source


def add_tree(entries: dict[str, Entry], archive_prefix: str, source: Path, suffixes: set[str] | None = None) -> None:
    for path in sorted(source.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        if suffixes is not None and path.suffix.lower() not in suffixes:
            continue
        add(entries, f"{archive_prefix}/{path.relative_to(source).as_posix()}", path)


def category(path: str) -> str:
    return path.split("/", 1)[0] if "/" in path else "project"


def manifest_bytes(entries: dict[str, Entry]) -> tuple[bytes, bytes]:
    rows = []
    sums = []
    for path, entry in sorted(entries.items()):
        payload = data(entry)
        digest = sha256_bytes(payload)
        rows.append({"relative_path": path, "size_bytes": len(payload), "sha256": digest, "category": category(path)})
        sums.append(f"{digest}  {path}")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=["relative_path", "size_bytes", "sha256", "category"], delimiter="\t")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8"), ("\n".join(sums) + "\n").encode("utf-8")


def write_member(archive: zipfile.ZipFile, path: str, payload: bytes) -> None:
    info = zipfile.ZipInfo(path, FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, payload)


def build(path: Path, entries: dict[str, Entry], max_bytes: int | None = None) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest, sums = manifest_bytes(entries)
    temporary = path.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for archive_path, entry in sorted(entries.items()):
            write_member(archive, archive_path, data(entry))
        write_member(archive, "manifest/MANIFEST.tsv", manifest)
        write_member(archive, "manifest/SHA256SUMS", sums)
    temporary.replace(path)
    if max_bytes is not None and path.stat().st_size >= max_bytes:
        raise RuntimeError(f"Archive exceeds limit {max_bytes}: {path.stat().st_size}")
    digest = sha256_file(path)
    path.with_suffix(path.suffix + ".sha256").write_text(f"{digest}  {path.name}\n", encoding="utf-8")
    return validate(path)


def validate(path: Path) -> dict[str, object]:
    errors: list[str] = []
    prohibited = [".sqlite", ".sqlite3", ".cbm", "__pycache__", ".pytest_cache", ".aux", ".fls", ".fdb_latexmk", ".build.log", ".blg", ".out"]
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            errors.append(f"unzip:{bad}")
        names = archive.namelist()
        if len(names) != len(set(names)):
            errors.append("duplicate_names")
        if any(any(token in name.lower() for token in prohibited) for name in names):
            errors.append("prohibited_payload")
        required = {"manifest/MANIFEST.tsv", "manifest/SHA256SUMS"}
        if not required.issubset(names):
            errors.append("manifest_missing")
            rows = []
        else:
            rows = list(csv.DictReader(archive.read("manifest/MANIFEST.tsv").decode("utf-8").splitlines(), delimiter="\t"))
            sums = {}
            for line in archive.read("manifest/SHA256SUMS").decode("utf-8").splitlines():
                digest, name = line.split("  ", 1)
                sums[name] = digest
            for row in rows:
                name = row["relative_path"]
                if name not in names:
                    errors.append(f"missing:{name}")
                    continue
                payload = archive.read(name)
                observed = sha256_bytes(payload)
                if len(payload) != int(row["size_bytes"]):
                    errors.append(f"size:{name}")
                if observed != row["sha256"] or sums.get(name) != observed:
                    errors.append(f"hash:{name}")
            if set(sums) != {row["relative_path"] for row in rows}:
                errors.append("sha256sums_scope")
        canonical = {
            "paper/cbdb_kdd_style_author_final.pdf": ROOT / "paper/final/cbdb_kdd_style_author_final.pdf",
            "paper/cbdb_kdd_style_anonymous_final.pdf": ROOT / "paper/final/cbdb_kdd_style_anonymous_final.pdf",
        }
        for name, source in canonical.items():
            if name not in names or sha256_bytes(archive.read(name)) != sha256_file(source):
                errors.append(f"canonical_pdf:{name}")
    sidecar = path.with_suffix(path.suffix + ".sha256")
    if not sidecar.is_file() or sidecar.read_text().split()[0] != sha256_file(path):
        errors.append("external_sha256")
    return {
        "path": str(path.resolve()),
        "file_count": len(names),
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "unzip_t": "PASS" if not bad else "FAIL",
        "manifest": "PASS" if not errors else "FAIL",
        "external_sha256": "PASS" if "external_sha256" not in errors else "FAIL",
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def submission_entries() -> dict[str, Entry]:
    entries: dict[str, Entry] = {}
    add(entries, "README.md", ROOT / "docs/phase3_1_1/PACKAGE_README.md")
    add(entries, "PROJECT_README.md", ROOT / "README.md")
    add(entries, "LICENSE", ROOT / "submission/LICENSE")
    for name in ["requirements.txt", "environment.yml"]:
        add(entries, name, ROOT / name)
    for name in [
        "cbdb_kdd_style_author_final.pdf", "cbdb_kdd_style_anonymous_final.pdf",
        "main_author_final.tex", "main_anonymous_final.tex", "main_body_final.tex",
        "references_final.bib", "reference_audit_final.csv",
    ]:
        add(entries, f"paper/{name}", ROOT / "paper/final" / name)
    add_tree(entries, "paper/figures", ROOT / "paper/final/figures", {".png", ".pdf", ".svg"})
    add_tree(entries, "paper/tables", ROOT / "paper/final/tables", {".tex"})
    for number in [63, 67, 68, 69, 70, 71, 72]:
        matches = list((ROOT / "scripts").glob(f"{number}_*.py"))
        if len(matches) != 1:
            raise RuntimeError(f"Expected one script for {number}: {matches}")
        add(entries, f"scripts/{matches[0].name}", matches[0])
    add(entries, "scripts/run_phase3_1_1_final_polish.sh", ROOT / "scripts/run_phase3_1_1_final_polish.sh")
    for name in ["geography.py", "feature_builders.py", "phase26.py", "utils.py"]:
        add(entries, f"src/{name}", ROOT / "src" / name)
    for path in sorted((ROOT / "tests").glob("test_phase3_1_1_*.py")):
        add(entries, f"tests/{path.name}", path)
    add(entries, "tests/import_stubs/catboost.py", ROOT / "tests/import_stubs/catboost.py")
    for name in ["phase2_6_features.yaml", "phase2_6_models.yaml", "phase2_6_reporting.yaml", "phase2_6_shap.yaml", "dynasty_capitals.yaml", "feature_policy.yaml", "feature_registry.yaml"]:
        add(entries, f"configs/{name}", ROOT / "configs" / name)
    add_tree(entries, "docs/phase3_1_1", ROOT / "docs/phase3_1_1", {".md"})
    add_tree(entries, "outputs/phase3_1_1/tables", ROOT / "outputs/phase3_1_1/tables", {".csv", ".json"})
    add_tree(entries, "outputs/phase3_1_1/methods", ROOT / "outputs/phase3_1_1/methods", {".json"})
    add_tree(entries, "outputs/phase3_1_1/figure_data", ROOT / "outputs/phase3_1_1/figure_data", {".csv"})
    add(entries, "outputs/phase3_1_1/manifests/baseline_sha256.tsv", ROOT / "outputs/phase3_1_1/manifests/baseline_sha256.tsv")
    safe_sources = [
        "outputs/tables/entry_vs_posting_contingency.csv", "outputs/tables/target_by_dynasty.csv",
        "outputs/phase2_5/tables/family_decomposition_deltas.csv",
        "outputs/phase2_6/tables/final_gender_entry_rates.csv", "outputs/phase2_6/tables/entry_category_by_dynasty_records.csv",
        "outputs/phase2_6/tables/entry_category_by_dynasty_people.csv", "outputs/phase2_6/tables/address_semantics_deltas.csv",
        "outputs/phase2_6/tables/matched_random_vs_spatial_results.csv", "outputs/phase2_6/tables/final_model_calibration.csv",
        "outputs/phase2_6/tables/multiseed_delta_summary.csv", "outputs/phase2_6/shap/shap_group_summary.csv",
        "outputs/phase3/tables/main_model_performance.csv", "outputs/phase3/tables/safe_temporal_split_context.csv",
        "outputs/phase3/tables/source_holdout_status.json", "outputs/phase3/tables/robustness_summary.csv",
        "outputs/phase3_1/tables/grouped_ablation_corrected.csv", "outputs/phase3_1/tables/final_metric_recomputation.csv",
    ]
    for relative in safe_sources:
        add(entries, f"frozen_sources/{relative}", ROOT / relative)
    return entries


def latest_entries() -> dict[str, Entry]:
    entries: dict[str, Entry] = {}
    add(entries, "README_ZH.md", ROOT / "docs/phase3_1_1/README_ZH.md")
    add(entries, "README_EN.md", ROOT / "docs/phase3_1_1/README_EN.md")
    for name in ["cbdb_kdd_style_author_final.pdf", "cbdb_kdd_style_anonymous_final.pdf"]:
        add(entries, f"paper/{name}", ROOT / "paper/final" / name)
    add(entries, "results/latest_results_summary.md", ROOT / "docs/phase3_1_1/latest_results_summary.md")
    add(entries, "results/latest_results_summary.json", ROOT / "outputs/phase3_1_1/tables/latest_results_summary.json")
    add(entries, "results/course_task_alignment.md", ROOT / "docs/phase3_1_1/course_task_alignment.md")
    table_map = {
        "primary_test_metrics.csv": "outputs/phase3/tables/main_model_performance.csv",
        "grouped_ablation_results.csv": "outputs/phase3_1/tables/grouped_ablation_corrected.csv",
        "distribution_shift_results.csv": "outputs/phase3/tables/robustness_summary.csv",
        "split_support_summary.csv": "outputs/phase3_1_1/tables/split_support_summary.csv",
        "shift_support_summary.csv": "outputs/phase3_1_1/tables/shift_support_summary.csv",
        "selected_operating_parameters.csv": "outputs/phase3_1_1/tables/operating_parameters.csv",
        "frozen_feature_registry.csv": "outputs/phase2_6/tables/final_model_feature_lists.csv",
    }
    for archive_name, relative in table_map.items():
        add(entries, f"results/tables/{archive_name}", ROOT / relative)
    for path in sorted((ROOT / "outputs/phase3_1_1/figures").iterdir()):
        if path.suffix.lower() in {".png", ".pdf", ".svg"}:
            add(entries, f"results/figures/{path.name}", path)
    add(entries, "results/figures/figure_input_hashes.csv", ROOT / "outputs/phase3_1_1/tables/figure_input_hashes.csv")
    add(entries, "results/methods/local_target_prior_spec.md", ROOT / "docs/phase3_1_1/local_target_prior_spec.md")
    add(entries, "results/methods/local_target_prior_spec.json", ROOT / "outputs/phase3_1_1/methods/local_target_prior_spec.json")
    audit_map = {
        "final_claim_evidence_map.md": "docs/phase3_1_1/final_claim_evidence_map.md",
        "final_statistical_consistency_audit.md": "docs/phase3_1_1/final_statistical_consistency_audit.md",
        "final_figure_audit.md": "docs/phase3_1_1/final_figure_audit.md",
        "final_anonymity_audit.md": "docs/phase3_1_1/final_anonymity_audit.md",
        "final_reproducibility_audit.md": "docs/phase3_1_1/final_reproducibility_audit.md",
        "final_nature_review.md": "docs/phase3_1_1/final_nature_review.md",
        "release_validation_report.md": "docs/phase3_1_1/release_validation_report.md",
        "changelog_phase3_1_1.md": "docs/phase3_1_1/changelog_phase3_1_1.md",
    }
    for archive_name, relative in audit_map.items():
        add(entries, f"audits/{archive_name}", ROOT / relative)
    return entries


def main() -> None:
    submission = build(SUBMISSION, submission_entries())
    latest = build(LATEST, latest_entries(), LATEST_MAX_BYTES)
    result = {
        "status": "PASS" if submission["status"] == latest["status"] == "PASS" else "FAIL",
        "submission": submission,
        "latest_results": latest,
        "latest_under_20mb": latest["size_bytes"] < LATEST_MAX_BYTES,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if result["status"] != "PASS" or not result["latest_under_20mb"]:
        raise SystemExit(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
