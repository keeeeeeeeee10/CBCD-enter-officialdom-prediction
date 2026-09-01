import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_all_phase3_invariants_pass():
    values = json.loads((ROOT / "outputs/phase3/tables/phase3_invariants.json").read_text())
    assert values["status"] == "PASS"
    for key in [
        "database_sha256_unchanged",
        "working_db_sha256_unchanged",
        "target_sha256_unchanged",
        "base_sha256_unchanged",
        "phase2_feature_master_sha256_unchanged",
        "split_sha256_unchanged",
        "phase2_outputs_unchanged",
        "phase2_5_outputs_unchanged",
        "phase2_6_outputs_unchanged",
        "paper_number_consistency",
        "figure_provenance_check",
        "reference_audit_check",
        "latex_author_compile",
        "latex_anonymous_compile",
        "paper_page_limit_check",
        "submission_zip_check",
        "review_zip_check",
    ]:
        assert values[key] is True, key
    assert values["working_db_quick_check"] == "ok"
    assert values["new_model_tuning_run"] is False
    assert values["hyperparameter_search_run"] is False
    assert values["gnn_run"] is False
    assert values["pagerank_run"] is False
