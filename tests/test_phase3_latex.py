import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_both_latex_versions_pass_quality_gate():
    quality = json.loads((ROOT / "outputs/phase3/tables/paper_quality_check.json").read_text())
    assert quality["status"] == "PASS"
    for version in ["author", "anonymous"]:
        item = quality[version]
        assert item["compile"]
        assert item["citations_and_references_resolved"]
        assert item["main_content_pages"] <= 8
        assert item["fonts_embedded"]
        assert item["placeholder_free"]
        assert item["no_severe_overfull_hbox"]
        assert (ROOT / item["pdf"]).stat().st_size > 100_000


def test_latex_sources_have_required_classes_and_no_placeholders():
    author = (ROOT / "paper/main_author.tex").read_text()
    anonymous = (ROOT / "paper/main_anonymous.tex").read_text()
    assert r"\documentclass[sigconf]{acmart}" in author
    assert r"\documentclass[sigconf,anonymous,review]{acmart}" in anonymous
    assert "Xiaoke Lu" not in anonymous
    assert not any(token in author + anonymous for token in ["TODO", "??", "[svg]", "/data/", "/home/"])
