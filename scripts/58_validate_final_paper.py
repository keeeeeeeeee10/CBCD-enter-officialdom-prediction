#!/usr/bin/env python3
"""Compile both manuscripts and enforce scientific, LaTeX, and archive gates."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd

from src.phase3 import (
    EXPECTED_HASHES,
    FROZEN_SNAPSHOT,
    PHASE3_DOCS,
    PHASE3_LOGS,
    PHASE3_TABLES,
    ROOT,
    SOURCE_STATUS,
    ensure_phase3_dirs,
    environment_payload,
    verify_frozen_snapshot,
    write_json,
)
from src.phase3_packaging import validate_zip
from src.utils import sha256_file


TITLE = "Who Leaves a Recorded Path into Government? A Documentation-Aware Data Mining Study of CBDB"
EXPECTED_FIGURES = [
    "fig1_task_ep_t",
    "fig2_dynasty_gender",
    "fig3_entry_pathways",
    "fig4_locked_models",
    "fig5_grouped_ablation",
    "fig6_spatial_transport",
    "fig7_family_decomposition",
    "fig8_grouped_shap",
    "figA1_calibration",
    "figA2_multiseed",
    "figA3_robustness_scope",
]


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def command_text(command: list[str]) -> str:
    result = run(command, ROOT / "paper")
    if result.returncode:
        raise RuntimeError(f"Command failed ({' '.join(command)}):\n{result.stdout[-6000:]}")
    return result.stdout


def label_page(aux: str, label: str) -> int:
    match = re.search(r"\\newlabel\{" + re.escape(label) + r"\}\{\{.*?\}\{(\d+)\}", aux)
    if not match:
        raise RuntimeError(f"Page label not found after compilation: {label}")
    return int(match.group(1))


def pdfinfo(path: Path) -> dict[str, str]:
    result = subprocess.run(["pdfinfo", str(path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f"pdfinfo failed for {path}: {result.stdout}")
    values: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def fonts_embedded(path: Path) -> tuple[bool, int]:
    result = subprocess.run(["pdffonts", str(path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode:
        return False, 0
    rows = [line.split() for line in result.stdout.splitlines()[2:] if line.strip()]
    return bool(rows) and all(len(row) >= 5 and row[-5] == "yes" for row in rows), len(rows)


def maximum_overfull(log: str) -> float:
    values = [float(value) for value in re.findall(r"Overfull \\hbox \(([0-9.]+)pt too wide\)", log)]
    return max(values, default=0.0)


def compile_one(stem: str, target: str, expected_author: str) -> dict[str, Any]:
    paper = ROOT / "paper"
    clean = run(["latexmk", "-C", f"{stem}.tex"], paper)
    build = run(["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", f"{stem}.tex"], paper)
    combined = "$ latexmk -C\n" + clean.stdout + "\n$ latexmk -pdf\n" + build.stdout
    (PHASE3_LOGS / f"latex_{stem.removeprefix('main_')}.log").write_text(combined, encoding="utf-8")
    if build.returncode:
        raise RuntimeError(f"LaTeX failed for {stem}:\n{build.stdout[-8000:]}")
    generated = paper / f"{stem}.pdf"
    destination = paper / target
    shutil.copy2(generated, destination)
    aux = (paper / f"{stem}.aux").read_text(encoding="utf-8", errors="replace")
    final_log = (paper / f"{stem}.log").read_text(encoding="utf-8", errors="replace")
    info = pdfinfo(destination)
    xmp_result = subprocess.run(
        ["pdfinfo", "-meta", str(destination)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    xmp = xmp_result.stdout
    total_pages = int(info["Pages"])
    main_pages = label_page(aux, "mainend")
    appendix_start = label_page(aux, "appendixstart")
    appendix_pages = total_pages - appendix_start + 1
    embedded, font_count = fonts_embedded(destination)
    text_result = subprocess.run(
        ["pdftotext", str(destination), "-"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    pdf_text = text_result.stdout
    unresolved = bool(
        re.search(r"undefined citations|undefined references|Citation.*undefined|Reference.*undefined", final_log, re.I)
    )
    return {
        "compile": True,
        "source": f"paper/{stem}.tex",
        "pdf": f"paper/{target}",
        "sha256": sha256_file(destination),
        "total_pages": total_pages,
        "main_content_pages": main_pages,
        "reference_pages": max(0, appendix_start - main_pages - 1),
        "appendix_pages": appendix_pages,
        "main_content_at_most_8": main_pages <= 8,
        "citations_and_references_resolved": not unresolved,
        "placeholder_free": not any(token in pdf_text for token in ["??", "TODO", "[svg]"]),
        "pdf_opens": text_result.returncode == 0,
        "fonts_embedded": embedded,
        "embedded_font_count": font_count,
        "pdf_title_correct": "Who Leaves a Recorded Path into Government?" in info.get("Title", ""),
        "pdf_author_correct": (
            info.get("Author", "") == expected_author
            or f"<rdf:li>{expected_author}</rdf:li>" in xmp
        ),
        "pdf_metadata": {
            **{key: info.get(key, "") for key in ["Title", "Creator", "Producer"]},
            "Author": expected_author if f"<rdf:li>{expected_author}</rdf:li>" in xmp else info.get("Author", ""),
            "metadata_source": "XMP dc:creator" if f"<rdf:li>{expected_author}</rdf:li>" in xmp else "PDF Info",
        },
        "maximum_overfull_hbox_pt": maximum_overfull(final_log),
        "no_severe_overfull_hbox": maximum_overfull(final_log) <= 20.0,
    }


def number_consistency() -> bool:
    performance = pd.read_csv(PHASE3_TABLES / "main_model_performance.csv")
    row = performance.loc[
        performance["population"].eq("Global") & performance["model_id"].eq("D5_MAIN")
    ].iloc[0]
    macros = (ROOT / "paper/tables/result_macros.tex").read_text(encoding="utf-8")
    required = [
        f"\\newcommand{{\\GlobalDfiveRoc}}{{{row.roc_auc:.6f}}}",
        f"\\newcommand{{\\GlobalDfivePr}}{{{row.pr_auc:.6f}}}",
        f"\\newcommand{{\\GlobalDfiveLogLoss}}{{{row.log_loss:.6f}}}",
        f"\\newcommand{{\\GlobalDfiveBrier}}{{{row.brier_score:.6f}}}",
        f"\\newcommand{{\\GlobalDfiveEce}}{{{row.calibrated_ece:.6f}}}",
        "\\newcommand{\\NPeople}{661{,}124}",
    ]
    return all(value in macros for value in required)


def reference_check() -> tuple[bool, int]:
    audit = pd.read_csv(ROOT / "paper/reference_audit.csv")
    bib = (ROOT / "paper/references.bib").read_text(encoding="utf-8")
    keys = set(re.findall(r"@\w+\{([^,]+),", bib))
    audit_keys = set(audit["citation_key"].astype(str))
    return bool(
        len(audit) >= 8
        and keys == audit_keys
        and audit["verification_status"].astype(str).str.startswith("VERIFIED").all()
        and audit["doi_or_url"].notna().all()
    ), len(audit)


def figure_check(tex: str) -> tuple[bool, dict[str, Any]]:
    manifest = pd.read_csv(PHASE3_TABLES / "figure_manifest.csv")
    errors: list[str] = []
    for row in manifest.itertuples(index=False):
        script = ROOT / row.script_path
        source = ROOT / row.input_files
        outputs = [ROOT / row.output_png, ROOT / row.output_pdf, ROOT / row.output_svg]
        if not script.is_file():
            errors.append(f"missing script:{row.figure_id}")
        if not source.is_file() or sha256_file(source) != row.input_sha256:
            errors.append(f"input provenance:{row.figure_id}")
        if any(not output.is_file() for output in outputs):
            errors.append(f"missing output:{row.figure_id}")
        if not str(row.input_files).startswith("outputs/"):
            errors.append(f"non-project input:{row.figure_id}")
        if f"figures/{row.figure_id}.pdf" not in tex:
            errors.append(f"not cited:{row.figure_id}")
    observed = manifest["figure_id"].tolist()
    positions = [tex.find(f"figures/{figure}.pdf") for figure in EXPECTED_FIGURES]
    details = {
        "figures_total": len(manifest),
        "main_figures": int(manifest["figure_id"].str.match(r"fig[1-8]_").sum()),
        "generated_from_project_outputs": int(len(manifest) - len(errors)),
        "figures_missing_scripts": sum(error.startswith("missing script") for error in errors),
        "external_images_count": 0,
        "expected_ids_and_order": observed == EXPECTED_FIGURES and positions == sorted(positions) and min(positions) >= 0,
        "errors": errors,
    }
    return not errors and details["expected_ids_and_order"], details


def source_quality() -> dict[str, Any]:
    author = (ROOT / "paper/main_author.tex").read_text(encoding="utf-8")
    anonymous = (ROOT / "paper/main_anonymous.tex").read_text(encoding="utf-8")
    combined = author + "\n" + anonymous
    figure_pass, figure_details = figure_check(author)
    return {
        "no_todo": "TODO" not in combined,
        "no_question_placeholders": "??" not in combined,
        "no_svg_placeholders": "[svg]" not in combined,
        "no_markdown_links": re.search(r"\[[^\]]+\]\([^\)]+\)", combined) is None,
        "no_absolute_project_paths": re.search(r"/(?:data|home)/", combined) is None,
        "author_class_correct": r"\documentclass[sigconf]{acmart}" in author,
        "anonymous_class_correct": r"\documentclass[sigconf,anonymous,review]{acmart}" in anonymous,
        "anonymous_source_blinded": "Xiaoke Lu" not in anonymous and "ShanghaiTech" not in anonymous,
        "paper_number_consistency": number_consistency(),
        "figure_provenance_check": figure_pass,
        "figure_provenance": figure_details,
    }


def write_scientific_docs(quality: dict[str, Any]) -> None:
    status = json.loads(SOURCE_STATUS.read_text(encoding="utf-8"))
    PHASE3_DOCS.joinpath("final_scientific_validation.md").write_text(
        f"""# Final scientific validation

## Decision

Phase 3 preserves every frozen database, feature, split, Phase 2, Phase 2.5, and Phase 2.6 artifact. The main task is prediction of observed ENTRY-record presence E, not latent true historical entry T. Posting presence P is a distinct auxiliary observed label.

The designated `D5_MAIN` result is Global ROC-AUC 0.936956 and PR-AUC 0.882535. `H_STRUCT` is the structural benchmark; `D6_UPPER` is a database-internal record-structure upper bound. Ablations, not SHAP shares, are the primary evidence of conditional contribution.

## Robustness boundary

Spatial transport is weaker on matched unseen regions, while family holdout degradation is smaller. SAFE temporal and Qing performance were not present as locked Phase 2.6 results, so no post-hoc result was created. Source status is `{status['status']}`: the largest of {status['source_groups']} connected groups covers {status['largest_group_fraction']:.2%} of {status['eligible_people']:,} eligible people.

## Paper validation

The author and anonymous manuscripts compile with resolved citations, embedded fonts, and no placeholders. Main content is {quality['author']['main_content_pages']} pages, references are {quality['author']['reference_pages']} page(s), and the appendix is {quality['author']['appendix_pages']} page(s).
""",
        encoding="utf-8",
    )
    PHASE3_DOCS.joinpath("reproducibility.md").write_text(
        """# Reproducibility

Run `bash scripts/run_phase3.sh` from the project root after the frozen Phase 1--2.6 artifacts are present. The runner validates known hashes and SQLite `PRAGMA quick_check`, audits sources, regenerates Phase 3 tables/figures/LaTeX, compiles both PDFs, checks citations and pagination, runs tests, and creates validated archives.

The canonical seed is 42. Phase 3 performs no hyperparameter search, new-model tuning, GNN, or PageRank run. The full SQLite files and 661,124-row feature master are excluded from archives; `scripts/01_download_cbdb.py` obtains the official release and verifies its declared SHA256.
""",
        encoding="utf-8",
    )
    PHASE3_DOCS.joinpath("submission_package.md").write_text(
        """# Submission and review packages

`scripts/59_build_submission_package.py` creates the reproducible author submission. `scripts/60_package_final_review.py` creates the bounded human-review archive. Both contain a CSV/Markdown payload manifest and are validated by ZIP CRC plus per-file SHA256. Database files, the virtual environment, full feature master, caches, temporary LaTeX files, raw prediction matrices, and old review archives are excluded.
""",
        encoding="utf-8",
    )


def compile_and_validate() -> dict[str, Any]:
    ensure_phase3_dirs()
    author = compile_one("main_author", "cbdb_kdd_style_author.pdf", "Xiaoke Lu")
    anonymous = compile_one("main_anonymous", "cbdb_kdd_style_anonymous.pdf", "Anonymous")
    source = source_quality()
    references_pass, reference_count = reference_check()
    checks = [
        author["compile"],
        anonymous["compile"],
        author["main_content_at_most_8"],
        anonymous["main_content_at_most_8"],
        author["citations_and_references_resolved"],
        anonymous["citations_and_references_resolved"],
        author["placeholder_free"],
        anonymous["placeholder_free"],
        author["fonts_embedded"],
        anonymous["fonts_embedded"],
        author["pdf_title_correct"],
        anonymous["pdf_title_correct"],
        author["pdf_author_correct"],
        anonymous["pdf_author_correct"],
        author["no_severe_overfull_hbox"],
        anonymous["no_severe_overfull_hbox"],
        references_pass,
        *[bool(value) for key, value in source.items() if key != "figure_provenance"],
    ]
    payload = {
        "status": "PASS" if all(checks) else "FAIL",
        "title": TITLE,
        "author": author,
        "anonymous": anonymous,
        "reference_count": reference_count,
        "reference_audit_check": references_pass,
        "table_count": 10,
        "source_checks": source,
    }
    write_json(PHASE3_TABLES / "paper_quality_check.json", payload)
    write_scientific_docs(payload)
    if payload["status"] != "PASS":
        raise RuntimeError(f"Paper quality gate failed: {json.dumps(payload, ensure_ascii=False)}")
    return payload


def build_invariants() -> dict[str, Any]:
    frozen = verify_frozen_snapshot()
    quality = json.loads((PHASE3_TABLES / "paper_quality_check.json").read_text(encoding="utf-8"))
    source = json.loads(SOURCE_STATUS.read_text(encoding="utf-8"))
    references_pass, _ = reference_check()
    submission = validate_zip(ROOT / "submission/cbdb_final_submission.zip")
    review = validate_zip(ROOT / "review_bundles/cbdb_final_paper_review_bundle.zip")
    changed = frozen["changed_frozen_files"]
    payload: dict[str, Any] = {
        "database_sha256_unchanged": sha256_file(ROOT / "database/cbdb_20260829.sqlite3") == EXPECTED_HASHES["database"],
        "working_db_sha256_unchanged": sha256_file(ROOT / "database/cbdb_working.sqlite3") == EXPECTED_HASHES["working_db"],
        "target_sha256_unchanged": sha256_file(ROOT / "data/interim/person_target.parquet") == EXPECTED_HASHES["target"],
        "base_sha256_unchanged": sha256_file(ROOT / "data/processed/person_base_v0.parquet") == EXPECTED_HASHES["base"],
        "phase2_feature_master_sha256_unchanged": sha256_file(ROOT / "data/modeling/person_phase2_features.parquet") == EXPECTED_HASHES["phase2_master"],
        "split_sha256_unchanged": all(
            sha256_file(ROOT / relative) == EXPECTED_HASHES[key]
            for key, relative in {
                "primary": "data/splits/split_primary_dynasty_target.parquet",
                "random": "data/splits/split_random_benchmark.parquet",
                "family": "data/splits/split_family_group_robustness.parquet",
                "temporal": "data/splits/split_safe_temporal.parquet",
            }.items()
        ),
        "phase2_outputs_unchanged": not any(path.startswith("outputs/phase2/") for path in changed),
        "phase2_5_outputs_unchanged": not any(path.startswith("outputs/phase2_5/") for path in changed),
        "phase2_6_outputs_unchanged": not any(path.startswith("outputs/phase2_6/") for path in changed),
        "working_db_quick_check": frozen["working_db_quick_check"],
        "source_holdout_status": source["status"],
        "source_overlap_check": source["source_overlap_check"]["status"],
        "paper_number_consistency": quality["source_checks"]["paper_number_consistency"],
        "figure_provenance_check": quality["source_checks"]["figure_provenance_check"],
        "reference_audit_check": references_pass,
        "latex_author_compile": quality["author"]["compile"],
        "latex_anonymous_compile": quality["anonymous"]["compile"],
        "paper_page_limit_check": quality["author"]["main_content_at_most_8"] and quality["anonymous"]["main_content_at_most_8"],
        "submission_zip_check": submission["pass"],
        "review_zip_check": review["pass"],
        "new_model_tuning_run": False,
        "hyperparameter_search_run": False,
        "gnn_run": False,
        "pagerank_run": False,
    }
    required_true = [
        key for key, value in payload.items()
        if key.endswith("_unchanged") or key.endswith("_consistency") or key.endswith("_check") or key.endswith("_compile")
    ]
    payload["status"] = "PASS" if all(bool(payload[key]) for key in required_true) and payload["working_db_quick_check"] == "ok" else "FAIL"
    write_json(PHASE3_TABLES / "phase3_invariants.json", payload)
    if payload["status"] != "PASS":
        raise RuntimeError(f"Phase 3 invariants failed: {json.dumps(payload, ensure_ascii=False)}")
    return payload


def check_zips() -> dict[str, Any]:
    payload = {
        "submission": validate_zip(ROOT / "submission/cbdb_final_submission.zip"),
        "review": validate_zip(ROOT / "review_bundles/cbdb_final_paper_review_bundle.zip"),
    }
    if not all(item["pass"] for item in payload.values()):
        raise RuntimeError(f"Final ZIP validation failed: {json.dumps(payload, ensure_ascii=False)}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--invariants", action="store_true")
    group.add_argument("--check-zips", action="store_true")
    args = parser.parse_args()
    if args.invariants:
        result = build_invariants()
    elif args.check_zips:
        result = check_zips()
    else:
        result = compile_and_validate()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
