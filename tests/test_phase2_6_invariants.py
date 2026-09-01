import hashlib
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def test_phase26_frozen_artifacts_still_match_precheck():
    semantic = json.loads((ROOT / "outputs/phase2_6/tables/semantic_patch.json").read_text())
    paths = {
        "database": "database/cbdb_20260829.sqlite3", "working_database": "database/cbdb_working.sqlite3",
        "target": "data/interim/person_target.parquet", "base": "data/processed/person_base_v0.parquet",
        "phase2_master": "data/modeling/person_phase2_features.parquet",
        "primary": "data/splits/split_primary_dynasty_target.parquet", "random": "data/splits/split_random_benchmark.parquet",
        "family": "data/splits/split_family_group_robustness.parquet", "temporal": "data/splits/split_safe_temporal.parquet",
    }
    assert all(digest(ROOT / path) == semantic["frozen_hashes"][key] for key, path in paths.items())
    with sqlite3.connect(f"file:{(ROOT / paths['working_database']).resolve().as_posix()}?mode=ro", uri=True) as connection:
        assert connection.execute("PRAGMA quick_check").fetchone()[0] == "ok"


def test_prohibited_methods_remain_off():
    shap = json.loads((ROOT / "outputs/phase2_6/shap/shap_additivity_check.json").read_text())
    assert shap["formal_shap_run"] is True
    config_text = (ROOT / "configs/phase2_6_models.yaml").read_text().lower()
    assert "optuna" not in config_text and "pagerank" not in config_text and "gnn" not in config_text
