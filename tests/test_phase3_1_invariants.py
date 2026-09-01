import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_every_phase3_1_invariant_passes():
    values = json.loads((ROOT / "outputs/phase3_1/tables/phase3_1_invariants.json").read_text())
    required_true = [
        "frozen_database_unchanged", "frozen_target_unchanged", "frozen_splits_unchanged",
        "phase2_outputs_unchanged", "phase2_5_outputs_unchanged", "phase2_6_outputs_unchanged",
        "phase3_outputs_unchanged", "nature_reviewer_round1_complete", "nature_statistics_complete",
        "nature_writing_complete", "nature_citation_complete", "nature_ref_verifier_complete",
        "nature_figure_complete", "nature_data_complete", "nature_polishing_complete",
        "nature_reviewer_round2_complete", "physical_geography_ci_valid",
        "all_table_numbers_consistent", "all_claims_supported", "all_references_verified",
        "all_figures_locally_generated", "external_image_count_zero", "fake_conference_metadata_removed",
        "shap_other_group_removed", "ep_t_semantics_correct", "raw_calibrated_metrics_labeled",
        "page_count_valid", "author_pdf_compiles", "anonymous_pdf_compiles",
        "submission_zip_valid", "review_zip_valid",
    ]
    for key in required_true:
        assert values[key] is True, key
    for key in ["new_model_training", "hyperparameter_search", "new_split_selection", "test_set_tuning"]:
        assert values[key] is False, key
    assert values["status"] == "PASS"
