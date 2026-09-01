#!/usr/bin/env python3
"""Freeze the pre-edit Phase 3.1 manuscript and scientific artifacts."""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/phase3_1_1/baseline_frozen_manifest.md"
TSV = ROOT / "outputs/phase3_1_1/manifests/baseline_sha256.tsv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def expand_artifacts() -> list[Path]:
    exact = [
        "database/cbdb_20260829.sqlite3",
        "database/cbdb_working.sqlite3",
        "data/interim/person_target.parquet",
        "data/processed/person_base_v0.parquet",
        "data/modeling/person_phase2_features.parquet",
        "data/splits/split_manifest.json",
        "data/splits/split_primary_dynasty_target.parquet",
        "data/splits/split_random_benchmark.parquet",
        "data/splits/split_family_group_robustness.parquet",
        "data/splits/split_safe_temporal.parquet",
        "data/phase2_6/predictions/final_model_predictions.parquet",
        "data/phase2_6/predictions/final_model_validation_predictions.parquet",
        "data/phase3_1/final_model_test_predictions.parquet",
        "outputs/phase2_6/tables/final_model_lock_manifest.json",
        "outputs/phase2_6/tables/final_model_metrics.csv",
        "outputs/phase2_6/tables/final_model_calibration.csv",
        "outputs/phase2_6/tables/final_model_feature_lists.csv",
        "outputs/phase2_6/tables/matched_random_vs_spatial_results.csv",
        "outputs/phase2_6/tables/multiseed_delta_summary.csv",
        "outputs/phase2_5/tables/family_decomposition_deltas.csv",
        "outputs/phase2_5/tables/paired_bootstrap_results.csv",
        "outputs/phase3/tables/main_model_performance.csv",
        "outputs/phase3/tables/robustness_summary.csv",
        "outputs/phase3/tables/source_holdout_status.json",
        "paper/revised/main_body_revised.tex",
        "paper/revised/main_author_revised.tex",
        "paper/revised/main_anonymous_revised.tex",
        "paper/revised/references_revised.bib",
        "paper/revised/tables/tableA2_full_metrics.tex",
        "paper/revised/tables/tableA3_full_ablation.tex",
        "paper/revised/tables/tableA4_full_robustness.tex",
        "paper/revised/cbdb_kdd_style_author_revised.pdf",
        "paper/revised/cbdb_kdd_style_anonymous_revised.pdf",
    ]
    patterns = [
        "outputs/phase2_6/models/**/*.cbm",
        "outputs/phase2_6/models/**/*.json",
        "data/phase2_5/splits/*.parquet",
        "data/phase2_5/predictions/*.parquet",
        "outputs/phase3_1/figures/*",
        "outputs/phase3_1/figure_data/*",
    ]
    paths = [ROOT / relative for relative in exact]
    for pattern in patterns:
        paths.extend(ROOT.glob(pattern))
    unique = sorted({path.resolve() for path in paths})
    missing = [path for path in unique if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing baseline artifacts: " + ", ".join(str(p) for p in missing))
    return unique


def git_status() -> str:
    result = subprocess.run(
        ["git", "status", "--short", "--branch"], cwd=ROOT,
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        return "NOT_A_GIT_REPOSITORY"
    return result.stdout.strip() or "CLEAN"


def pdf_pages(path: Path) -> int:
    result = subprocess.run(["pdfinfo", str(path)], text=True, capture_output=True, check=True)
    match = re.search(r"^Pages:\s+(\d+)$", result.stdout, re.MULTILINE)
    if not match:
        raise RuntimeError(f"Cannot determine pages for {path}")
    return int(match.group(1))


def aux_page(path: Path, label: str) -> int:
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"\\newlabel\{" + re.escape(label) + r"\}\{\{.*?\}\{(\d+)\}", text)
    if not match:
        raise RuntimeError(f"Missing {label} in {path}")
    return int(match.group(1))


def manuscript_counts() -> dict[str, int]:
    body = (ROOT / "paper/revised/main_body_revised.tex").read_text(encoding="utf-8")
    aux = ROOT / "paper/revised/cbdb_kdd_style_author_revised.aux"
    return {
        "total_pages": pdf_pages(ROOT / "paper/revised/cbdb_kdd_style_author_revised.pdf"),
        "main_pages": aux_page(aux, "mainend") - 1,
        "references_start": aux_page(aux, "mainend"),
        "appendix_start": aux_page(aux, "appendixstart"),
        "numbered_sections_in_source": len(re.findall(r"^\\section\{", body, re.MULTILINE)),
        "numbered_subsections_in_source": len(re.findall(r"^\\subsection\{", body, re.MULTILINE)),
        "figure_environments": len(re.findall(r"^\\begin\{figure\*?\}", body, re.MULTILINE)),
        "table_inputs": len(re.findall(r"\\input\{tables/table", body)),
        "bibliography_entries": len(re.findall(r"^@\w+\{", (ROOT / "paper/revised/references_revised.bib").read_text(encoding="utf-8"), re.MULTILINE)),
    }


def main() -> None:
    paths = expand_artifacts()
    TSV.parent.mkdir(parents=True, exist_ok=True)
    DOC.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in paths:
        rows.append((path.relative_to(ROOT).as_posix(), path.stat().st_size, sha256(path)))
    TSV.write_text(
        "relative_path\tsize_bytes\tsha256\n" +
        "".join(f"{relative}\t{size}\t{digest}\n" for relative, size, digest in rows),
        encoding="utf-8",
    )
    counts = manuscript_counts()
    lines = [
        "# Phase 3.1 frozen baseline", "",
        "This manifest records the last accepted Phase 3.1 state before the non-experimental Phase 3.1.1 polish. It is an audit record, not a new scientific result.", "",
        "## Repository state", "",
        f"- Git status: `{git_status()}`",
        "- Existing Phase 3.1 precheck: `PASS: Phase 1--3 frozen artifacts unchanged`",
        "- Existing focused test suite: `21 passed`",
        f"- SHA-256 inventory: `{TSV.relative_to(ROOT).as_posix()}` ({len(rows)} files)", "",
        "## Manuscript state", "",
    ]
    labels = {
        "total_pages": "Total PDF pages",
        "main_pages": "Main-text pages",
        "references_start": "References start page",
        "appendix_start": "Appendix start page",
        "numbered_sections_in_source": "Section commands in source",
        "numbered_subsections_in_source": "Subsection commands in source",
        "figure_environments": "Figure environments",
        "table_inputs": "Table inputs",
        "bibliography_entries": "Bibliography entries",
    }
    lines.extend(f"- {labels[key]}: {value}" for key, value in counts.items())
    lines += [
        "", "## Frozen scientific invariants", "",
        "- Global D5_MAIN: ROC-AUC 0.936956; PR-AUC 0.882535; raw LogLoss 0.315106; raw Brier 0.097356; validation-calibrated ECE 0.003438.",
        "- Table A2, Table A3 and Table A4 values are frozen; Physical geography retains a dash for unavailable confidence intervals.",
        "- Model, split and prediction hashes in the inventory are immutable Phase 3.1.1 release checks.",
        "- Phase 3.1 outputs remain in place and are never overwritten by the Phase 3.1.1 generation scripts.",
    ]
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"PASS: froze {len(rows)} baseline files; {counts['total_pages']} pages; {counts['bibliography_entries']} references")


if __name__ == "__main__":
    main()
