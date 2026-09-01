from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_reports_and_model_cards_exist_without_svg_placeholders():
    paths = [
        ROOT / "docs/phase2_6/final_data_analysis.md",
        ROOT / "docs/phase2_6/final_model_report.md",
        ROOT / "docs/phase2_6/final_interpretation_and_limitations.md",
        ROOT / "docs/phase2_6/address_feature_policy.md",
        *(ROOT / f"docs/phase2_6/model_cards/{model}.md" for model in ["H_STRUCT", "D5_MAIN", "D6_UPPER"]),
    ]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert text.strip()
        assert "[svg]" not in text
    assert "explicit missing indicator" in paths[0].read_text(encoding="utf-8")
    assert "not causal effect" in paths[1].read_text(encoding="utf-8")


def test_all_final_figures_have_png_svg_and_input_csv():
    names = [
        "final_population_and_target_context", "final_entry_pathways_by_dynasty", "final_gender_entry_rate",
        "final_birth_missingness_decomposition", "final_address_semantics_decomposition",
        "final_family_signal_decomposition", "final_documentation_controlled_models", "final_multiseed_stability",
        "final_random_vs_spatial_matched_support", "final_locked_model_performance",
        "final_shap_group_comparison_global", "final_shap_group_comparison_song",
        "final_shap_group_comparison_ming", "final_calibration_summary",
    ]
    for name in names:
        assert (ROOT / f"outputs/phase2_6/figures/{name}.png").stat().st_size > 0
        assert (ROOT / f"outputs/phase2_6/figures/{name}.svg").stat().st_size > 0
        assert (ROOT / f"outputs/phase2_6/tables/figure_inputs/{name}.csv").stat().st_size > 0
