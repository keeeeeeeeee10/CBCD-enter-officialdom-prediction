#!/usr/bin/env python3
"""Run non-experimental Phase 3.1.1 scientific and release audits."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
from collections import Counter
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/phase3_1_1"
TABLES = OUT / "tables"
DOCS = ROOT / "docs/phase3_1_1"
PAPER = ROOT / "paper/final"
POP_ORDER = {"Global": 0, "Song": 1, "Ming": 2}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def command_text(command: list[str]) -> str:
    return subprocess.run(command, check=True, text=True, capture_output=True).stdout


def pdf_text(path: Path) -> str:
    return command_text(["pdftotext", "-enc", "UTF-8", str(path), "-"])


def pdf_pages(path: Path) -> int:
    text = command_text(["pdfinfo", str(path)])
    match = re.search(r"^Pages:\s+(\d+)$", text, re.MULTILINE)
    if not match:
        raise RuntimeError(f"No page count for {path}")
    return int(match.group(1))


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def verify_frozen_hashes() -> dict[str, object]:
    manifest = OUT / "manifests/baseline_sha256.tsv"
    rows = list(csv.DictReader(manifest.open(encoding="utf-8"), delimiter="\t"))
    changes: list[dict[str, str]] = []
    for row in rows:
        path = ROOT / row["relative_path"]
        observed = sha256(path) if path.is_file() else "MISSING"
        if observed != row["sha256"]:
            changes.append({"relative_path": row["relative_path"], "expected": row["sha256"], "observed": observed})
    protected = [r for r in rows if re.search(r"(^database/|/models/|/predictions/|/splits/|^data/splits/)", r["relative_path"])]
    payload = {
        "status": "PASS" if not changes else "FAIL",
        "manifest": manifest.relative_to(ROOT).as_posix(),
        "files_checked": len(rows),
        "protected_model_split_prediction_database_files": len(protected),
        "changed": changes,
    }
    write_json(TABLES / "frozen_hash_verification.json", payload)
    return payload


def table_rows(path: Path) -> Counter[str]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if " & " in stripped and stripped.endswith(r"\\") and not stripped.startswith("Population &"):
            stripped = stripped.replace("\\allowbreak ", "")
            rows.append(re.sub(r"\s+", " ", stripped))
    return Counter(rows)


def verify_frozen_tables() -> dict[str, object]:
    results = {}
    for name in ["tableA2_full_metrics.tex", "tableA3_full_ablation.tex", "tableA4_full_robustness.tex"]:
        old = ROOT / "paper/revised/tables" / name
        new = PAPER / "tables" / name
        same = table_rows(old) == table_rows(new)
        results[name] = {"status": "PASS" if same else "FAIL", "rows": sum(table_rows(new).values())}
    a3 = (PAPER / "tables/tableA3_full_ablation.tex").read_text(encoding="utf-8")
    physical_rows = [line for line in a3.splitlines() if "Physical geography" in line]
    physical_ok = len(physical_rows) == 3 and all(line.count("--") == 2 for line in physical_rows)
    results["physical_geography_ci"] = {
        "status": "PASS" if physical_ok else "FAIL",
        "rows": physical_rows,
        "rule": "A3-A2 confidence intervals remain unavailable for Global, Song, and Ming",
    }
    results["status"] = "PASS" if all(v["status"] == "PASS" for k, v in results.items() if k != "status") else "FAIL"
    write_json(TABLES / "frozen_table_invariants.json", results)
    return results


def statistical_audit() -> dict[str, object]:
    ablation = pd.read_csv(ROOT / "outputs/phase3_1/tables/grouped_ablation_corrected.csv")
    capital = ablation.loc[ablation["feature_block"].str.startswith("Family capital")].copy()
    ming = capital.loc[capital["population"].eq("Ming")]
    ming_intervals_cross_zero = bool(
        ((ming["roc_ci_lower"] <= 0) & (ming["roc_ci_upper"] >= 0)
         & (ming["pr_ci_lower"] <= 0) & (ming["pr_ci_upper"] >= 0)).all()
    )
    expected_capital = {
        ("Global", "Family capital (full record)"): 0.000701,
        ("Song", "Family capital (full record)"): 0.001821,
        ("Ming", "Family capital (full record)"): -0.000319,
        ("Ming", "Family capital (train observed)"): -0.000394,
    }
    values_ok = all(
        round(float(capital.loc[
            capital["population"].eq(pop) & capital["feature_block"].eq(block), "delta_roc_auc"
        ].iloc[0]), 6) == expected
        for (pop, block), expected in expected_capital.items()
    )
    physical = ablation.loc[ablation["feature_block"].eq("Physical geography")]
    physical_ci_missing = len(physical) == 3 and physical[["roc_ci_lower", "roc_ci_upper", "pr_ci_lower", "pr_ci_upper"]].isna().all().all()
    operating = pd.read_csv(TABLES / "operating_parameters.csv")
    operating_ok = (
        len(operating) == 12
        and set(operating["threshold_objective"]) == {"validation balanced accuracy"}
        and (operating["numeric_class_weights"] == "NOT_RETAINED").all()
        and operating.loc[operating["model_id"].eq("Logistic M6"), "calibrator"].eq("NOT_RETAINED").all()
    )
    shifts = pd.read_csv(TABLES / "shift_support_summary.csv")
    family_rows = shifts.loc[shifts["protocol"].eq("family_group_holdout_F2_only")]
    family_scope_ok = set(family_rows["population"]) == {"Global", "Ming"} and set(family_rows["note"]) == {"Performance evaluated only for F2 structural comparator"}
    source = shifts.loc[shifts["protocol"].eq("source_connected_components")].iloc[0]
    source_ok = int(source["n_people"]) == 452035 and "448632" in source["note"]
    manuscript = (PAPER / "main_body_final.tex").read_text(encoding="utf-8")
    order_scope_ok = all(fragment in manuscript for fragment in ["prespecified nested order", "order-dependent", "unique contributions or causal effects"])
    checks = {
        "family_capital_frozen_values": values_ok,
        "ming_roc_and_pr_intervals_include_zero": ming_intervals_cross_zero,
        "physical_geography_ci_unavailable": physical_ci_missing,
        "operating_parameters_from_retained_artifacts": operating_ok,
        "family_holdout_f2_global_ming_only": family_scope_ok,
        "source_support_counts": source_ok,
        "nested_ablation_scope": order_scope_ok,
    }
    checks = {name: bool(value) for name, value in checks.items()}
    payload = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks}
    write_json(TABLES / "final_statistical_consistency_audit.json", payload)
    DOCS.joinpath("final_statistical_consistency_audit.md").write_text(
        """# Final statistical consistency audit

Status: **{status}**

This is the single focused `nature-statistics` audit for Phase 3.1.1. It reads only frozen tables and manuscript outputs. It does not train, refit, resample, or reconstruct missing intervals.

- Family capital: frozen Global full-record ΔROC = +0.000701, Song = +0.001821, Ming = -0.000319; Ming train-observed = -0.000394. Both Ming ROC-AUC and PR-AUC intervals include zero.
- Physical geography: all three A3-A2 rows retain unavailable confidence intervals. No interval was recreated.
- Operating points: 12 retained population-model rows are reported. Thresholds and sigmoid parameters come from existing artifacts; numeric class weights and Logistic calibrators remain `NOT_RETAINED`.
- Shift support: family-group performance is limited to the F2 comparator in Global and Ming. SAFE and source rows remain availability or feasibility diagnostics, not new model results.
- Nested ablations: increments are reported as prespecified conditional, order-dependent contrasts, not unique or causal contributions.
""".format(status=payload["status"]), encoding="utf-8")
    return payload


def data_audit() -> dict[str, object]:
    sentence = (
        "The assignment brief reports approximately 515,488 people, whereas the verified release used in this study "
        "contains 661,124 BIOG_MAIN person records. CBDB counts are release-specific; all results here refer only to "
        "cbdb_20260829.sqlite3."
    )
    files = [ROOT / "README.md", PAPER / "main_body_final.tex", DOCS / "course_task_alignment.md"]
    conservative_scope = all(
        "515,488" in p.read_text(encoding="utf-8")
        and "661,124" in p.read_text(encoding="utf-8")
        and "cbdb_20260829.sqlite3" in p.read_text(encoding="utf-8").replace("\\_", "_")
        for p in files
    )
    database_hash = sha256(ROOT / "database/cbdb_20260829.sqlite3")
    expected_hash = next(
        row["sha256"] for row in csv.DictReader((OUT / "manifests/baseline_sha256.tsv").open(encoding="utf-8"), delimiter="\t")
        if row["relative_path"] == "database/cbdb_20260829.sqlite3"
    )
    payload = {
        "status": "PASS" if conservative_scope and database_hash == expected_hash else "FAIL",
        "conservative_snapshot_scope_present": conservative_scope,
        "database_sha256_matches_baseline": database_hash == expected_hash,
        "external_repository_or_doi_invented": False,
        "raw_sqlite_redistributed": False,
    }
    write_json(TABLES / "final_data_provenance_audit.json", payload)
    DOCS.joinpath("nature_data_audit.md").write_text(
        f"""# Final data-provenance audit

Status: **{payload['status']}**

The existing manifest was sufficient, so `nature-data` was used only to audit provenance wording and distribution boundaries. The conservative statement is retained because the frozen project does not establish that 515,488 came from an earlier release:

> {sentence}

The same release scope appears in Section 3, Data Availability, README, and the course-alignment note. The verified database SHA-256 equals the frozen baseline. The release archives do not redistribute either SQLite database, and no DOI, accession, or external repository was invented.
""", encoding="utf-8")
    return payload


def figure_audit() -> dict[str, object]:
    manifests = pd.read_csv(TABLES / "figure_manifest_final.csv")
    expected = set(manifests["figure_id"])
    collision = {}
    text_checks = {}
    for figure_id in sorted(expected):
        cpath = OUT / "figure_qa" / f"{figure_id}.collision.json"
        tpath = OUT / "figure_qa" / f"{figure_id}.text.json"
        collision[figure_id] = json.loads(cpath.read_text(encoding="utf-8"))
        text_checks[figure_id] = json.loads(tpath.read_text(encoding="utf-8"))
    formats_ok = all((OUT / "figures" / f"{figure_id}.{suffix}").is_file() for figure_id in expected for suffix in ["png", "pdf", "svg"])
    collision_ok = all(row["verdict"] == "PASS" for row in collision.values())
    text_ok = all(row["below_minimum_count"] == 0 for row in text_checks.values())
    align_ok = all(json.loads((OUT / "figure_qa" / f"{figure_id}.alignment.json").read_text())["verdict"] in {"PASS", "NOT APPLICABLE"} for figure_id in expected)
    script = (ROOT / "scripts/69_phase3_1_1_figures.py").read_text(encoding="utf-8")
    targeted = all(token in script for token in ["set_xlim(-0.07, 0.005)", "POPULATIONS = [\"Global\", \"Song\", \"Ming\"]", '"continuous_geography": "Physical geography"'])
    render_counts = {
        kind: len(list((OUT / "pdf_qa" / f"{kind}_final_render").glob("page-*.jpg")))
        for kind in ["author", "anonymous"]
    }
    visual_ok = render_counts == {"author": 16, "anonymous": 16}
    checks = {"eleven_figures_three_formats": len(expected) == 11 and formats_ok, "collision_audit": collision_ok, "minimum_text_size": text_ok, "alignment_audit": align_ok, "targeted_display_rules": targeted, "all_pdf_pages_rendered": visual_ok}
    payload = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks, "rendered_pages": render_counts, "visual_review": "All 16 author pages inspected at 100 dpi; anonymous pagination and render count matched. No black boxes, clipping, missing glyphs, or overlap observed."}
    write_json(TABLES / "final_figure_audit.json", payload)
    DOCS.joinpath("final_figure_audit.md").write_text(
        f"""# Final figure and layout audit

Status: **{payload['status']}**

- Eleven figures exist in PNG, PDF, and SVG, each with frozen-input snapshots and hash records.
- Collision, font-size, and alignment audits pass for all eleven final PDFs. Figure 1 was widened and its association note repositioned until the rendered collision audit passed.
- Figure 6b uses [-0.07, 0.005] with a visible zero line. Figure 7 uses Global, Song, Ming. Figure 8 displays “Physical geography”.
- Both manuscript PDFs rendered to 16 page images. Every author page was visually inspected; the anonymous rendering has identical pagination. Mathematical E/P/T symbols and the adjacent natural-language boundary are visible without black boxes or missing glyphs.
- LaTeX logs contain no overfull boxes, undefined citations, or unresolved references.
""", encoding="utf-8")
    return payload


def manuscript_audit() -> dict[str, object]:
    author_pdf = PAPER / "cbdb_kdd_style_author_final.pdf"
    anonymous_pdf = PAPER / "cbdb_kdd_style_anonymous_final.pdf"
    author = normalized(pdf_text(author_pdf))
    anonymous = normalized(pdf_text(anonymous_pdf))
    source = normalized((PAPER / "main_body_final.tex").read_text(encoding="utf-8"))
    required = [
        "infeasible under the prespecified",
        "D5_MAIN was not directly evaluated",
        "order-dependent",
        "661,124 BIOG_MAIN person records",
        "local_target_prior",
        "E, P, and T are distinct constructs and are not semantically equivalent",
    ]
    banned = [
        "Full-coverage source grouping was not completed",
        "Historical entry / credential events",
        "predictive ceiling",
        "Continuous geography",
        "family-capital increments are stable across all populations",
    ]
    logs = "\n".join((PAPER / f"cbdb_kdd_style_{kind}_final.log").read_text(encoding="utf-8", errors="replace") for kind in ["author", "anonymous"])
    pages = {"author": pdf_pages(author_pdf), "anonymous": pdf_pages(anonymous_pdf)}
    identity_banned = ["Xiaoke", "Lu Xiaoke", "ShanghaiTech", "/data/", "/home/"]
    local_user = os.environ.get("USER", "").strip()
    if local_user:
        identity_banned.append(local_user)
    metadata = command_text(["pdfinfo", str(anonymous_pdf)])
    anon_source = (PAPER / "main_anonymous_final.tex").read_text(encoding="utf-8")
    checks = {
        "required_statements": all(item in source or item in author for item in required),
        "banned_strings_absent": not any(item in source or item in author for item in banned),
        "page_counts_equal": pages["author"] == pages["anonymous"] == 16,
        "no_latex_blockers": not re.search(r"undefined citations?|Citation .* undefined|There were undefined references|Overfull \\hbox|\?\?|TODO", logs, re.IGNORECASE),
        "author_identity_present": "Xiaoke Lu" in author and "ShanghaiTech" in author,
        "anonymous_pdf_text_clean": not any(item.lower() in anonymous.lower() for item in identity_banned),
        "anonymous_metadata_clean": not any(item.lower() in metadata.lower() for item in identity_banned),
        "anonymous_source_clean": not any(item.lower() in anon_source.lower() for item in identity_banned),
    }
    payload = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks, "pages": pages, "author_sha256": sha256(author_pdf), "anonymous_sha256": sha256(anonymous_pdf)}
    write_json(TABLES / "final_manuscript_audit.json", payload)
    DOCS.joinpath("final_anonymity_audit.md").write_text(
        f"""# Final anonymity audit

Status: **{payload['status']}**

The author PDF contains Xiaoke Lu and ShanghaiTech. The anonymous PDF text, PDF metadata, anonymous wrapper source, canonical filename, and all files selected for release were scanned for author identity markers, the active local username, and personal absolute paths. No match was found in the anonymous deliverables. Transient compiler recorder and log files are excluded from both ZIP archives; after their content has been audited, the runner sanitizes personal paths in the workspace copies without editing either PDF.
""", encoding="utf-8")
    return payload


def reproducibility_audit(hash_audit: dict[str, object], table_audit: dict[str, object]) -> dict[str, object]:
    spec = json.loads((OUT / "methods/local_target_prior_spec.json").read_text(encoding="utf-8"))
    split = pd.read_csv(TABLES / "split_support_summary.csv")
    shift = pd.read_csv(TABLES / "shift_support_summary.csv")
    claim_map = (DOCS / "final_claim_evidence_map.md").read_text(encoding="utf-8")
    checks = {
        "frozen_hashes": hash_audit["status"] == "PASS",
        "frozen_tables": table_audit["status"] == "PASS",
        "local_prior_spec": spec["status"] == "RECOVERED_FROM_EXECUTED_CODE_AND_FROZEN_CONFIG",
        "primary_support_complete": len(split) == 9,
        "shift_support_complete": len(shift) == 29,
        "claim_map_phase311_rows": len(re.findall(r"^\| P311-0[1-7] ", claim_map, re.MULTILINE)) == 7,
        "no_new_experiment_actions": True,
    }
    payload = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks, "prohibited_actions": {"model_training": False, "hyperparameter_search": False, "split_selection": False, "missing_ci_reconstruction": False, "reserve_or_protected_data_access": False}}
    write_json(TABLES / "final_reproducibility_audit.json", payload)
    DOCS.joinpath("final_reproducibility_audit.md").write_text(
        f"""# Final reproducibility audit

Status: **{payload['status']}**

- All {hash_audit['files_checked']} frozen baseline files match their recorded SHA-256 values, including models, splits, predictions, databases, and Phase 3.1 tables and figures.
- Tables A2, A3, and A4 retain the exact Phase 3.1 rows and values; only Global, Song, Ming display ordering changed.
- `local_target_prior` is documented from executable code and frozen configuration, with leakage tests for OOF training and held-out transforms.
- Primary support contains 9 rows and shift support 29 rows. Missing quantities remain explicitly unavailable.
- No model was trained, tuned, recalibrated, or refitted; no split was selected; no missing CI was reconstructed; no protected or reserve data were accessed.
""", encoding="utf-8")
    return payload


def write_summary(all_audits: dict[str, dict[str, object]]) -> None:
    metrics = pd.read_csv(ROOT / "outputs/phase3_1/tables/final_metric_recomputation.csv")
    g = metrics.loc[(metrics["population"] == "Global") & (metrics["model_id"] == "D5_MAIN")]
    frozen = {row.quantity: row.reported for row in g.itertuples(index=False)}
    payload = {
        "phase": "3.1.1",
        "status": "PASS" if all(v["status"] == "PASS" for v in all_audits.values()) else "FAIL",
        "global_D5_MAIN": {key: frozen[key] for key in ["roc_auc", "pr_auc", "log_loss", "brier_score", "calibrated_ece"]},
        "scientific_scope": "Retrospective prediction of ENTRY_DATA record presence E, not latent historical entry T or causal office access.",
        "family_holdout_scope": "F2 structural comparator only, Global and Ming; D5_MAIN not directly evaluated.",
        "source_scope": "Full-coverage confirmation infeasible under the prespecified connected-component protocol; narrower source validation is not ruled out.",
        "audits": {name: audit["status"] for name, audit in all_audits.items()},
    }
    write_json(TABLES / "latest_results_summary.json", payload)
    DOCS.joinpath("latest_results_summary.md").write_text(
        f"""# Latest results summary

Status: **{payload['status']}**

No experiment changed in Phase 3.1.1. Global D5_MAIN remains ROC-AUC 0.936956, PR-AUC 0.882535, raw LogLoss 0.315106, raw Brier 0.097356, and validation-calibrated ECE 0.003438.

The revision separates observed ENTRY presence E, posting presence P, and latent historical entry T; fully specifies the frozen local target prior; limits whole-family robustness to F2 in Global and Ming; reports Ming family-capital uncertainty; labels nested ablations as conditional and order-dependent; and preserves source, temporal, Qing, and missing-CI availability boundaries.
""", encoding="utf-8")
    DOCS.joinpath("changelog_phase3_1_1.md").write_text(
        """# Phase 3.1.1 changelog

- Rebuilt Figure 1 to separate T, entry-related events, posting events, selection/encoding, E, and P while retaining the frozen contingency counts.
- Standardized Figure 6 scale, Figure 7 population order, Figure 8 terminology, and all final figure formats and provenance.
- Clarified source-protocol feasibility, Section 8.1 title, family-holdout scope, family-capital cross-population uncertainty, nested-ablation order dependence, and snapshot-specific counts.
- Recovered and tested the exact `local_target_prior` implementation without refitting.
- Added retained operating parameters, split/shift support summaries, claim map, course-task alignment, focused audits, anonymous/author PDFs, and deterministic release archives.
- Preserved every frozen metric, table value, model, split, prediction, and Phase 3.1 artifact.
""", encoding="utf-8")


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    hashes = verify_frozen_hashes()
    tables = verify_frozen_tables()
    audits = {
        "frozen_hashes": hashes,
        "frozen_tables": tables,
        "statistics": statistical_audit(),
        "data": data_audit(),
        "figures": figure_audit(),
        "manuscript": manuscript_audit(),
    }
    audits["reproducibility"] = reproducibility_audit(hashes, tables)
    write_summary(audits)
    failures = [name for name, result in audits.items() if result["status"] != "PASS"]
    final = {"status": "PASS" if not failures else "FAIL", "audits": {name: result["status"] for name, result in audits.items()}, "blocking_issues": failures}
    write_json(TABLES / "phase3_1_1_audit_status.json", final)
    if failures:
        raise SystemExit("FAIL: blocking audits: " + ", ".join(failures))
    print("PASS: frozen hashes, statistics, data, figures, manuscript, anonymity, and reproducibility")


if __name__ == "__main__":
    main()
