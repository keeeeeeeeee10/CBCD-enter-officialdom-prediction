import hashlib
from pathlib import Path

import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "outputs/phase3_1/tables/figure_manifest_revised.csv"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_figure_manifest_and_provenance_are_complete():
    manifest = pd.read_csv(MANIFEST)
    assert list(manifest.columns) == [
        "figure_id", "paper_section", "caption", "source_tables", "source_sha256",
        "generation_script", "png_path", "pdf_path", "svg_path", "verification_status",
    ]
    assert len(manifest) == 11
    assert manifest["figure_id"].is_unique
    assert manifest["generation_script"].eq("scripts/63_phase3_1_figures.py").all()
    for row in manifest.itertuples(index=False):
        sources = row.source_tables.split(";")
        hashes = row.source_sha256.split(";")
        assert len(sources) == len(hashes)
        for source, expected in zip(sources, hashes):
            path = ROOT / source
            assert path.is_file() and digest(path) == expected
        for output in [row.png_path, row.pdf_path, row.svg_path]:
            assert (ROOT / output).is_file()
        snapshot = ROOT / "outputs/phase3_1/figure_data" / f"{row.figure_id}.csv"
        assert snapshot.is_file()
        assert "VERIFIED_FROM_FROZEN_INPUT" in row.verification_status


def test_pngs_are_submission_resolution_and_no_external_images_exist():
    manifest = pd.read_csv(MANIFEST)
    for relative in manifest["png_path"]:
        with Image.open(ROOT / relative) as image:
            dpi = image.info.get("dpi", (0, 0))
            assert min(dpi) >= 299
    assert all(str(path).startswith(str(ROOT)) for path in [ROOT / p for p in manifest["png_path"]])


def test_shap_registry_uses_historical_regime_not_other():
    for name in ["shap_group_summary_revised.csv", "shap_feature_summary_revised.csv", "shap_direction_summary_revised.csv"]:
        frame = pd.read_csv(ROOT / "outputs/phase3_1/tables" / name)
        object_values = " ".join(frame.select_dtypes(include="object").fillna("").astype(str).to_numpy().ravel()).lower().split()
        assert "other" not in object_values
        assert "historical_regime" in object_values


def test_eight_main_and_three_appendix_figures_are_cited():
    body = (ROOT / "paper/revised/main_body_revised.tex").read_text(encoding="utf-8")
    main_part, appendix = body.split(r"\appendix", maxsplit=1)
    manifest = pd.read_csv(MANIFEST)
    main_ids = manifest.loc[~manifest["figure_id"].str.startswith("figA"), "figure_id"]
    appendix_ids = manifest.loc[manifest["figure_id"].str.startswith("figA"), "figure_id"]
    assert len(main_ids) == 8 and len(appendix_ids) == 3
    for figure_id in main_ids:
        assert f"figures/{figure_id}.pdf" in main_part
    for figure_id in appendix_ids:
        assert f"figures/{figure_id}.pdf" in appendix
