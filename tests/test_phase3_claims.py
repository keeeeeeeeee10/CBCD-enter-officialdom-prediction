from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_e_p_t_and_model_roles_are_explicit():
    text = (ROOT / "paper/main_author.tex").read_text()
    assert "latent historical state of true entry into government" in text
    assert "observed database label" in text
    assert r"E_i&=\mathbb{1}" in text
    assert r"P_i&=\mathbb{1}" in text
    assert r"\Pr(E=1\mid X)" in text
    assert "rather than reconstructing historical truth" in text
    assert "historical structural benchmark" in text.lower()
    assert "database-internal upper bound" in text


def test_forbidden_scientific_claims_are_absent():
    text = (ROOT / "paper/main_author.tex").read_text().lower()
    forbidden = [
        "accurately predicts true entry into government",
        "predicts actual office holding with 93.7% accuracy",
        "geography causes entry into government",
        "father's entry causes the child's entry",
        "proves class rigidity",
        "proves the imperial examination was fair",
        "e=0 means the person never entered government",
        "auc accuracy",
    ]
    assert not [claim for claim in forbidden if claim in text]
    assert "shap attribution is neither independent ablation gain nor a causal effect" in text
    assert "not the historical entry rate" in text
