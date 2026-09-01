from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def test_generated_macros_match_result_csv():
    metrics = pd.read_csv(ROOT / "outputs/phase3/tables/main_model_performance.csv")
    d5 = metrics.loc[metrics["population"].eq("Global") & metrics["model_id"].eq("D5_MAIN")].iloc[0]
    macros = (ROOT / "paper/tables/result_macros.tex").read_text()
    for macro, value in [
        ("GlobalDfiveRoc", d5.roc_auc),
        ("GlobalDfivePr", d5.pr_auc),
        ("GlobalDfiveLogLoss", d5.log_loss),
        ("GlobalDfiveBrier", d5.brier_score),
        ("GlobalDfiveEce", d5.calibrated_ece),
    ]:
        assert f"\\newcommand{{\\{macro}}}{{{value:.6f}}}" in macros


def test_d5_is_the_reported_main_model():
    text = (ROOT / "paper/main_author.tex").read_text()
    assert "D5\\_MAIN is the designated main result" in (ROOT / "paper/tables/table3_performance.tex").read_text()
    assert "D5\\_MAIN is the main model" in text
    assert "D6\\_UPPER is an upper bound" in text
