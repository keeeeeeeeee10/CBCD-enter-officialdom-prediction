from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
BODY = (ROOT / "paper/final/main_body_final.tex").read_text(encoding="utf-8")


def test_required_scientific_boundaries_are_present():
    required = [
        "Full-coverage source-group confirmation was infeasible under the prespecified connected-component protocol because 448,632 of 452,035 eligible people belonged to a single connected component.",
        "\\subsection{Locked models establish strong within-database discrimination}",
        "E, P, and T are distinct constructs and are not semantically equivalent.",
        "Family-group robustness of D5\\_MAIN was not directly evaluated.",
        "order-dependent",
        "661,124 \\texttt{BIOG\\_MAIN} person records",
        "This study combines open-ended exploratory analysis of dynastic, gender, ENTRY-pathway, geographic, and kin-observability patterns with predictive modeling of ENTRY-record presence.",
    ]
    assert all(text in BODY for text in required)


def test_banned_final_wording_is_absent():
    banned = [
        "Full-coverage source grouping was not completed",
        "Historical entry / credential events",
        "predictive ceiling",
        "Continuous geography",
        "family-capital increments are stable across all populations",
        "source validation is impossible",
    ]
    assert not any(text in BODY for text in banned)


def test_phase311_claim_map_has_exactly_seven_additions():
    text = (ROOT / "docs/phase3_1_1/final_claim_evidence_map.md").read_text(encoding="utf-8")
    assert len(re.findall(r"^\| P311-0[1-7] ", text, re.MULTILINE)) == 7
    assert not re.search(r"^\| P311-(?:0[89]|[1-9]\d)", text, re.MULTILINE)


def test_family_scope_is_consistent_across_interpretive_sections():
    assert "whole-family evidence supports only F2 in Global and Ming, not D5\\_MAIN" in BODY
    assert "Whole-family performance applies only to F2 in Global and Ming, not D5\\_MAIN" in BODY
    assert "Whole-family evidence is F2-only" in BODY
