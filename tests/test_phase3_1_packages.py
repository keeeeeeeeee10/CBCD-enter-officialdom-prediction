import csv
import hashlib
import io
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def validate(path: Path) -> set[str]:
    assert path.is_file() and path.stat().st_size < 120 * 1024 * 1024
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        names = set(archive.namelist())
        assert {"ZIP_MANIFEST.csv", "ZIP_MANIFEST.md"}.issubset(names)
        rows = list(csv.DictReader(io.TextIOWrapper(archive.open("ZIP_MANIFEST.csv"), encoding="utf-8")))
        assert len(rows) == len(names) - 2
        for row in rows:
            data = archive.read(row["relative_path"])
            assert len(data) == int(row["file_size_bytes"])
            assert hashlib.sha256(data).hexdigest() == row["sha256"]
        assert path.with_suffix(".sha256").is_file()
        expected = path.with_suffix(".sha256").read_text().split()[0]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
        assert path.name not in names and path.with_suffix(".sha256").name not in names
        return names


def test_submission_package_is_valid_and_bounded():
    names = validate(ROOT / "submission/cbdb_final_submission_nature_revised.zip")
    required = {
        "paper/revised/cbdb_kdd_style_author_revised.pdf",
        "paper/revised/main_author_revised.tex",
        "paper/revised/main_body_revised.tex",
        "paper/revised/references_revised.bib",
        "outputs/phase3_1/tables/figure_manifest_revised.csv",
        "README.md", "DATA_USAGE.md", "requirements.txt", "environment.yml",
        "scripts/run_phase3_1_nature_revision.sh",
    }
    assert required.issubset(names)
    forbidden = [".sqlite3", ".venv/", "person_phase2_features.parquet", "cbdb_final_submission.zip", "cbdb_final_paper_review_bundle.zip"]
    assert not any(any(token in name for token in forbidden) for name in names)


def test_review_package_contains_all_requested_review_categories():
    names = validate(ROOT / "review_bundles/cbdb_final_paper_review_bundle_nature_revised.zip")
    required = {
        "REVIEW_INDEX.md",
        "paper/revised/cbdb_kdd_style_author_revised.pdf",
        "paper/revised/cbdb_kdd_style_anonymous_revised.pdf",
        "docs/phase3_1/nature_review_round1.md",
        "docs/phase3_1/nature_statistics_audit.md",
        "docs/phase3_1/nature_figure_audit.md",
        "docs/phase3_1/nature_data_audit.md",
        "docs/phase3_1/nature_review_round2.md",
        "docs/phase3_1/nature_skill_revision_log.md",
        "docs/phase3_1/revision_summary.md",
        "docs/phase3_1/revision_diff.md",
        "docs/phase3_1/final_claim_evidence_map.md",
        "outputs/phase3_1/tables/statistical_correction_manifest.csv",
        "data/phase3_1/final_model_test_predictions.parquet",
        "outputs/phase3_1/tables/page_count_audit.json",
        "outputs/phase3_1/tables/phase3_1_invariants.json",
        "outputs/phase3_1/tables/environment_versions.json",
        "outputs/phase3_1/tables/project_tree.txt",
        "outputs/phase3_1/logs/run_phase3_1_nature_revision.log",
        "outputs/phase3_1/logs/pytest_phase3_1.log",
    }
    assert required.issubset(names)
    assert any(name.startswith("outputs/phase3_1/figure_data/") for name in names)
    assert any(name.startswith("paper/revised/figures/") for name in names)
    assert any(name.startswith("paper/revised/tables/") for name in names)
    assert any(name.startswith("tests/test_phase3_1_") for name in names)
    assert not any(name.endswith(".sqlite3") or name.endswith(".zip") for name in names)
