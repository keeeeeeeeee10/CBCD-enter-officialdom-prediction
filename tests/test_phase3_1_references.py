import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper/revised"


def bib_keys(text: str) -> set[str]:
    return set(re.findall(r"@\w+\{([^,]+),", text))


def citation_keys(text: str) -> set[str]:
    keys: set[str] = set()
    for match in re.findall(r"\\cite\{([^}]+)\}", text):
        keys.update(key.strip() for key in match.split(","))
    return keys


def test_reference_audit_covers_every_bibliography_entry():
    audit = pd.read_csv(PAPER / "reference_audit_revised.csv")
    bib = (PAPER / "references_revised.bib").read_text(encoding="utf-8")
    required = [
        "citation_key", "title", "authors", "year", "venue", "doi_or_official_url",
        "verification_status", "claim_supported", "section_used", "notes",
    ]
    assert list(audit.columns) == required
    assert len(audit) == 20
    assert audit["citation_key"].is_unique
    assert audit["verification_status"].eq("VERIFIED").all()
    assert audit[["title", "authors", "year", "venue", "doi_or_official_url", "claim_supported"]].notna().all().all()
    assert bib_keys(bib) == set(audit["citation_key"])


def test_every_bibliography_entry_is_cited_and_defined():
    bib = (PAPER / "references_revised.bib").read_text(encoding="utf-8")
    body = (PAPER / "main_body_revised.tex").read_text(encoding="utf-8")
    assert citation_keys(body) == bib_keys(bib)


def test_compiled_logs_have_no_undefined_citations_or_references():
    for kind in ["author", "anonymous"]:
        log = (PAPER / f"cbdb_kdd_style_{kind}_revised.log").read_text(encoding="utf-8", errors="replace")
        lowered = log.lower()
        assert "citation" not in lowered or "undefined on input line" not in lowered
        assert "there were undefined references" not in lowered
        assert "rerun to get cross-references right" not in lowered
