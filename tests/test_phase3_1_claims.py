from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BODY = (ROOT / "paper/revised/main_body_revised.tex").read_text(encoding="utf-8")


def test_ep_t_construct_semantics_are_explicit():
    assert r"E \not\equiv T" in BODY
    assert r"P \not\equiv T" in BODY
    assert r"E \not\equiv P" in BODY
    assert "E, P, and T are not semantically equivalent." in BODY
    assert r"\Pr(E_i=1\mid X_i)" in BODY
    assert "retrospective ENTRY-record presence" in BODY


def test_model_roles_and_source_scope_are_correct():
    assert "D5\\_MAIN is the designated predictive model" in BODY
    assert "D6\\_UPPER is a database-internal record-structure upper bound" in BODY
    assert "H\\_STRUCT contains regime, gender" in BODY
    assert "It is therefore not an unbiased historical model." in BODY
    assert "Full-coverage source-group confirmation was infeasible under the prespecified connected-component protocol." in BODY
    assert "A selective single-primary-source subset could support a narrower source-holdout sensitivity" in BODY
    assert "Source-level validation is impossible" not in BODY


def test_no_prohibited_scientific_overclaim():
    lowered = BODY.lower()
    for phrase in [
        "true entry prediction", "actual entry probability", "accurately predicts historical truth",
        "submitted to kdd 2026", "proved that", "proves that", "determined by the model",
    ]:
        assert phrase not in lowered
    assert "causal effects" in lowered and ("not conditional gains or causal effects" in lowered or "not a causal effect" in lowered)
    assert "cannot identify which historical institutions or source practices caused these patterns" in lowered


def test_required_limitations_are_argumentative_and_complete():
    for heading in [
        "Measurement and label validity", "Selection and documentation bias",
        "Temporal and transductive information", "Generalization and adaptive test use",
    ]:
        assert rf"\paragraph{{{heading}.}}" in BODY
    for phrase in [
        "9.05\\%", "transductive", "lifetime outcomes", "multiple project phases",
        "calibration need not remain stable", "SHAP remains non-causal",
        "omit uncertainty in its definition and historical validity", "Matched-support spatial performance declined",
    ]:
        assert phrase in BODY


def test_claim_evidence_map_has_only_supported_claims():
    claim_map = (ROOT / "docs/phase3_1/final_claim_evidence_map.md").read_text(encoding="utf-8")
    assert all(field in claim_map for field in [
        "claim_id", "paper_section", "claim_text", "evidence_type",
        "source_table_or_reference", "supported", "caveat",
    ])
    assert claim_map.count("| C") >= 15
    assert "| NO |" not in claim_map
