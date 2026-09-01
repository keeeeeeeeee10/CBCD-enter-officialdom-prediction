from pathlib import Path
import json
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/phase3_1_1"


def test_all_eleven_final_figures_have_three_formats_and_snapshots():
    manifest = pd.read_csv(OUT / "tables/figure_manifest_final.csv")
    assert len(manifest) == 11
    assert manifest["figure_id"].nunique() == 11
    for row in manifest.itertuples(index=False):
        for path in [row.png_path, row.pdf_path, row.svg_path, row.snapshot_path]:
            assert (ROOT / path).is_file() and (ROOT / path).stat().st_size > 0


def test_figure_geometry_and_text_audits_pass():
    for pdf in sorted((OUT / "figures").glob("*.pdf")):
        figure_id = pdf.stem
        collision = json.loads((OUT / "figure_qa" / f"{figure_id}.collision.json").read_text())
        text = json.loads((OUT / "figure_qa" / f"{figure_id}.text.json").read_text())
        alignment = json.loads((OUT / "figure_qa" / f"{figure_id}.alignment.json").read_text())
        assert collision["verdict"] == "PASS"
        assert text["below_minimum_count"] == 0
        assert alignment["verdict"] in {"PASS", "NOT APPLICABLE"}


def test_targeted_figure_rules_are_encoded_and_manifested():
    script = (ROOT / "scripts/69_phase3_1_1_figures.py").read_text()
    assert 'POPULATIONS = ["Global", "Song", "Ming"]' in script
    assert "set_xlim(-0.07, 0.005)" in script
    assert '"continuous_geography": "Physical geography"' in script
    caption = pd.read_csv(OUT / "tables/figure_manifest_final.csv").set_index("figure_id")["caption"]
    assert "negative" in caption["fig6_spatial_transport"].lower()
    assert "Global, Song, and Ming" in caption["fig7_family_decomposition"]
    assert "Physical geography" in caption["fig8_grouped_shap"]
    assert "E, P, and T are distinct constructs and are not interchangeable" in caption["final_task_definition_ep_t"]


def test_all_pdf_pages_have_rendered_images():
    for kind in ["author", "anonymous"]:
        pages = sorted((OUT / "pdf_qa" / f"{kind}_final_render").glob("page-*.jpg"))
        assert len(pages) == 16
        assert all(page.stat().st_size > 10_000 for page in pages)
