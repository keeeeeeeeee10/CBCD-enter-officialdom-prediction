from pathlib import Path
import csv
import hashlib
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SUBMISSION = ROOT / "submission/cbdb_final_submission_phase3_1_1.zip"
LATEST = ROOT / "exports/cbdb_phase3_1_1_latest_results.zip"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate(path: Path):
    assert path.is_file() and path.stat().st_size > 0
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert len(names) == len(set(names))
        assert "manifest/MANIFEST.tsv" in names
        assert "manifest/SHA256SUMS" in names
        rows = list(csv.DictReader(archive.read("manifest/MANIFEST.tsv").decode().splitlines(), delimiter="\t"))
        sums = {}
        for line in archive.read("manifest/SHA256SUMS").decode().splitlines():
            digest, name = line.split("  ", 1)
            sums[name] = digest
        assert set(sums) == {row["relative_path"] for row in rows}
        for row in rows:
            payload = archive.read(row["relative_path"])
            assert len(payload) == int(row["size_bytes"])
            assert sha256(payload) == row["sha256"] == sums[row["relative_path"]]
    sidecar = path.with_suffix(path.suffix + ".sha256")
    assert sidecar.is_file()
    assert sidecar.read_text().split()[0] == sha256(path.read_bytes())


def test_both_archives_and_internal_manifests_validate():
    validate(SUBMISSION)
    validate(LATEST)


def test_zip_pdf_hashes_equal_canonical_final_pdfs():
    for archive_path in [SUBMISSION, LATEST]:
        with zipfile.ZipFile(archive_path) as archive:
            for kind in ["author", "anonymous"]:
                name = f"paper/cbdb_kdd_style_{kind}_final.pdf"
                canonical = ROOT / "paper/final" / f"cbdb_kdd_style_{kind}_final.pdf"
                assert sha256(archive.read(name)) == sha256(canonical.read_bytes())


def test_no_prohibited_data_cache_or_latex_intermediate_is_packaged():
    prohibited = [".sqlite", ".sqlite3", ".cbm", "__pycache__", ".pytest_cache", ".aux", ".fls", ".fdb_latexmk", ".build.log", ".blg", ".out"]
    for archive_path in [SUBMISSION, LATEST]:
        with zipfile.ZipFile(archive_path) as archive:
            assert not any(any(token in name.lower() for token in prohibited) for name in archive.namelist())


def test_latest_archive_has_exact_review_structure_and_size_limit():
    assert LATEST.stat().st_size < 20 * 1024 * 1024
    required = {
        "README_ZH.md", "README_EN.md",
        "paper/cbdb_kdd_style_author_final.pdf", "paper/cbdb_kdd_style_anonymous_final.pdf",
        "results/latest_results_summary.md", "results/latest_results_summary.json", "results/course_task_alignment.md",
        "results/tables/primary_test_metrics.csv", "results/tables/grouped_ablation_results.csv",
        "results/tables/distribution_shift_results.csv", "results/tables/split_support_summary.csv",
        "results/tables/shift_support_summary.csv", "results/tables/selected_operating_parameters.csv",
        "results/tables/frozen_feature_registry.csv", "results/figures/figure_input_hashes.csv",
        "results/methods/local_target_prior_spec.md", "results/methods/local_target_prior_spec.json",
        "audits/final_claim_evidence_map.md", "audits/final_statistical_consistency_audit.md",
        "audits/final_figure_audit.md", "audits/final_anonymity_audit.md",
        "audits/final_reproducibility_audit.md", "audits/final_nature_review.md",
        "audits/release_validation_report.md", "audits/changelog_phase3_1_1.md",
        "manifest/MANIFEST.tsv", "manifest/SHA256SUMS",
    }
    with zipfile.ZipFile(LATEST) as archive:
        names = set(archive.namelist())
        assert required.issubset(names)
        for suffix in ["png", "pdf", "svg"]:
            figures = [name for name in names if name.startswith("results/figures/") and name.endswith("." + suffix)]
            assert len(figures) == 11


def test_submission_archive_has_complete_source_payload():
    with zipfile.ZipFile(SUBMISSION) as archive:
        names = set(archive.namelist())
    required = {
        "README.md", "LICENSE", "paper/main_author_final.tex", "paper/main_anonymous_final.tex",
        "paper/main_body_final.tex", "paper/references_final.bib",
        "scripts/run_phase3_1_1_final_polish.sh", "scripts/72_package_phase3_1_1.py",
        "tests/test_phase3_1_1_invariants.py", "configs/phase2_6_features.yaml",
        "manifest/MANIFEST.tsv", "manifest/SHA256SUMS",
    }
    assert required.issubset(names)
