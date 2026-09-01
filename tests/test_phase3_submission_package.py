from pathlib import Path

from src.phase3_packaging import validate_zip


ROOT = Path(__file__).resolve().parents[1]


def test_submission_zip_and_manifest():
    result = validate_zip(ROOT / "submission/cbdb_final_submission.zip")
    assert result["pass"], result
    assert result["manifest_entries"] >= 80


def test_review_zip_and_manifest():
    result = validate_zip(ROOT / "review_bundles/cbdb_final_paper_review_bundle.zip")
    assert result["pass"], result
    assert result["manifest_entries"] >= 80
