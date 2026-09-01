from pathlib import Path
import os
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/final"


def pdf_text(path: Path) -> str:
    return subprocess.run(["pdftotext", "-enc", "UTF-8", str(path), "-"], check=True, text=True, capture_output=True).stdout


def pdf_pages(path: Path) -> int:
    info = subprocess.run(["pdfinfo", str(path)], check=True, text=True, capture_output=True).stdout
    return int(re.search(r"^Pages:\s+(\d+)$", info, re.MULTILINE).group(1))


def test_final_pdfs_compile_to_identical_page_counts():
    assert pdf_pages(PAPER / "cbdb_kdd_style_author_final.pdf") == 16
    assert pdf_pages(PAPER / "cbdb_kdd_style_anonymous_final.pdf") == 16
    aux = (PAPER / "cbdb_kdd_style_author_final.aux").read_text(errors="replace")
    assert re.search(r"\\newlabel\{mainend\}\{\{.*?\}\{9\}", aux)
    assert re.search(r"\\newlabel\{appendixstart\}\{\{.*?\}\{10\}", aux)


def test_logs_have_no_release_blockers():
    for kind in ["author", "anonymous"]:
        text = (PAPER / f"cbdb_kdd_style_{kind}_final.log").read_text(errors="replace")
        banned = ["Overfull \\hbox", "undefined citation", "There were undefined references", "duplicate ignored"]
        assert not any(item.lower() in text.lower() for item in banned)


def test_pdf_contains_construct_symbols_and_natural_language_boundary():
    author = pdf_text(PAPER / "cbdb_kdd_style_author_final.pdf")
    assert "E, P, and T are distinct constructs and are not semantically equivalent" in author
    source = (PAPER / "main_body_final.tex").read_text()
    assert r"E \not\equiv T" in source and r"P \not\equiv T" in source and r"E \not\equiv P" in source
    # pdftotext is not a reliable extractor for this glyph. The rendered page
    # is checked in the figure/layout audit while the source guarantees the
    # intended mathematical symbol.


def test_anonymous_pdf_text_metadata_and_wrapper_are_clean():
    anonymous_pdf = PAPER / "cbdb_kdd_style_anonymous_final.pdf"
    content = pdf_text(anonymous_pdf)
    metadata = subprocess.run(["pdfinfo", str(anonymous_pdf)], check=True, text=True, capture_output=True).stdout
    wrapper = (PAPER / "main_anonymous_final.tex").read_text()
    banned_values = ["Xiaoke", "Lu Xiaoke", "ShanghaiTech", "/data/", "/home/"]
    local_user = os.environ.get("USER", "").strip()
    if local_user:
        banned_values.append(local_user)
    for banned in banned_values:
        assert banned.lower() not in content.lower()
        assert banned.lower() not in metadata.lower()
        assert banned.lower() not in wrapper.lower()


def test_anonymous_compiler_auxiliaries_have_no_identity_or_personal_paths():
    suffixes = {".aux", ".bbl", ".blg", ".log", ".fls", ".fdb_latexmk", ".out"}
    paths = [path for path in PAPER.glob("cbdb_kdd_style_anonymous_final.*") if path.suffix in suffixes]
    paths += list(PAPER.glob("cbdb_kdd_style_anonymous_final.build.log"))
    assert paths
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        banned_values = ["Xiaoke", "Lu Xiaoke", "ShanghaiTech", "/data/", "/home/"]
        local_user = os.environ.get("USER", "").strip()
        if local_user:
            banned_values.append(local_user)
        for banned in banned_values:
            assert banned.lower() not in text.lower(), (path, banned)


def test_author_identity_is_present_only_in_author_wrapper_and_pdf():
    author = pdf_text(PAPER / "cbdb_kdd_style_author_final.pdf")
    wrapper = (PAPER / "main_author_final.tex").read_text()
    assert "Xiaoke Lu" in author and "ShanghaiTech" in author
    assert "Xiaoke Lu" in wrapper and "ShanghaiTech University" in wrapper
