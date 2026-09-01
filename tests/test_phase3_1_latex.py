import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/revised"
BODY = (PAPER / "main_body_revised.tex").read_text(encoding="utf-8")


def pdf_text(path: Path) -> str:
    return subprocess.run(["pdftotext", str(path), "-"], check=True, text=True, capture_output=True).stdout


def test_neutral_metadata_and_shared_source_structure():
    assert r"\documentclass[sigconf]{acmart}" in BODY
    assert "Data Mining Course Research Report" in BODY
    assert "KDD-style 2026" not in BODY
    assert "Submitted to KDD 2026" not in BODY
    author = (PAPER / "main_author_revised.tex").read_text(encoding="utf-8")
    anonymous = (PAPER / "main_anonymous_revised.tex").read_text(encoding="utf-8")
    assert "Xiaoke Lu" in author and "ShanghaiTech University" in author
    assert "Xiaoke Lu" not in anonymous and "ShanghaiTech" not in anonymous
    assert "Xiaoke Lu" not in BODY and "ShanghaiTech" not in BODY
    assert r"\input{main_body_revised}" in author and r"\input{main_body_revised}" in anonymous


def test_page_boundary_and_counting_are_valid():
    assert r"\FloatBarrier" + "\n" + r"\clearpage" + "\n" + r"\label{mainend}" in BODY
    audit = json.loads((ROOT / "outputs/phase3_1/tables/page_count_audit.json").read_text())
    assert audit["status"] == "PASS"
    for version in audit["versions"].values():
        assert version["main_content_pages"] == 8
        assert version["references_pages"] >= 1
        assert version["appendix_pages"] >= 1
        assert version["references_after_main"] and version["appendix_after_references"]


def test_both_pdfs_compile_and_anonymous_pdf_is_blinded():
    author = PAPER / "cbdb_kdd_style_author_revised.pdf"
    anonymous = PAPER / "cbdb_kdd_style_anonymous_revised.pdf"
    assert author.is_file() and anonymous.is_file()
    author_text, anonymous_text = pdf_text(author), pdf_text(anonymous)
    assert "Xiaoke Lu" in author_text and "ShanghaiTech University" in author_text
    assert "Anonymous Author(s)" in anonymous_text
    assert "Xiaoke Lu" not in anonymous_text and "ShanghaiTech" not in anonymous_text
    metadata = subprocess.run(["pdfinfo", "-meta", str(anonymous)], check=True, text=True, capture_output=True).stdout
    assert "Xiaoke Lu" not in metadata and "ShanghaiTech" not in metadata


def test_source_and_pdfs_have_no_placeholders_or_local_paths():
    combined = "\n".join((PAPER / name).read_text(encoding="utf-8") for name in ["main_author_revised.tex", "main_anonymous_revised.tex", "main_body_revised.tex"])
    for token in ["TODO", "??", "[svg]", "/data/", "/home/"]:
        assert token not in combined
    for kind in ["author", "anonymous"]:
        text = pdf_text(PAPER / f"cbdb_kdd_style_{kind}_revised.pdf")
        assert "??" not in text and "TODO" not in text and "[svg]" not in text
        log = (PAPER / f"cbdb_kdd_style_{kind}_revised.log").read_text(encoding="utf-8", errors="replace")
        assert "Fatal error" not in log and "Emergency stop" not in log
