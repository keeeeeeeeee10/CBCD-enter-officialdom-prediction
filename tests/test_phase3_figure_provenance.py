from pathlib import Path

import pandas as pd

from src.utils import sha256_file


ROOT = Path(__file__).resolve().parents[1]


def test_every_figure_has_local_script_input_and_three_formats():
    manifest = pd.read_csv(ROOT / "outputs/phase3/tables/figure_manifest.csv")
    assert len(manifest) == 11
    assert manifest["figure_id"].str.match(r"fig(?:[1-8]|A[1-3])_").all()
    for row in manifest.itertuples(index=False):
        assert (ROOT / row.script_path).is_file()
        source = ROOT / row.input_files
        assert source.is_file()
        assert sha256_file(source) == row.input_sha256
        assert str(row.input_files).startswith("outputs/phase3/figure_data/")
        assert (ROOT / row.output_png).is_file()
        assert (ROOT / row.output_pdf).is_file()
        assert (ROOT / row.output_svg).is_file()
        assert int(row.dpi) == 300


def test_no_external_images_are_referenced():
    manifest = pd.read_csv(ROOT / "outputs/phase3/tables/figure_manifest.csv")
    tex = (ROOT / "paper/main_author.tex").read_text()
    assert len(set(manifest["figure_id"])) == 11
    for figure in manifest["figure_id"]:
        assert f"figures/{figure}.pdf" in tex
    assert "http://" not in tex and "https://" not in tex
