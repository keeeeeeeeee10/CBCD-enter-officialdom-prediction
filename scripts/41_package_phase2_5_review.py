#!/usr/bin/env python3
"""Build and verify the self-contained Phase 2.5 human-review ZIP."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import load_yaml, resolve_feature_set
from src.utils import atomic_write_text, sha256_file, setup_logging


def copy_file(source: Path, stage: Path, relative: Path | None = None) -> None:
    target = stage / (relative or source.relative_to(PROJECT_ROOT))
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def copy_tree_files(source: Path, stage: Path) -> None:
    for path in sorted(source.rglob("*")):
        if path.is_file() and not any(part in {"__pycache__", ".pytest_cache"} for part in path.parts):
            copy_file(path, stage)


def feature_review_assets(stage: Path) -> None:
    master_path = PROJECT_ROOT / "data/modeling/person_phase2_features.parquet"
    master = pd.read_parquet(master_path)
    targets = pd.read_parquet(PROJECT_ROOT / "data/interim/person_targets_v1_v2.parquet")
    sample_source = master.merge(
        targets[["person_id", "target_entry_v2a", "target_entry_v2b", "target_posting"]],
        on="person_id", how="left", validate="one_to_one",
    )
    sample_source["population_bucket"] = sample_source["dynasty_name"].where(
        sample_source["dynasty_name"].isin(["Song", "Ming", "Qing"]), "Other"
    )
    fraction = 15_000 / len(sample_source)
    sample = (
        sample_source.groupby(["population_bucket", "target_entry_v1", "split_primary"], dropna=False, group_keys=False)
        .sample(frac=fraction, random_state=42)
        .sort_values("person_id")
        .reset_index(drop=True)
    )
    if not 10_000 <= len(sample) <= 20_000:
        raise RuntimeError(f"Review sample size outside protocol: {len(sample)}")
    review = stage / "feature_review"
    review.mkdir(parents=True, exist_ok=True)
    schema = pd.DataFrame({
        "feature": master.columns,
        "dtype": [str(master[column].dtype) for column in master.columns],
        "n_missing": [int(master[column].isna().sum()) for column in master.columns],
        "missing_rate": [float(master[column].isna().mean()) for column in master.columns],
        "n_unique": [int(master[column].nunique(dropna=True)) for column in master.columns],
    })
    schema.to_csv(review / "feature_schema.csv", index=False)
    registry = load_yaml("configs/phase2_5_features.yaml")
    rows = []
    for model_id in registry["feature_sets"]:
        categorical, numeric = resolve_feature_set(registry, model_id)
        rows.extend({"model_id": model_id, "feature": feature, "role": "categorical"} for feature in categorical)
        rows.extend({"model_id": model_id, "feature": feature, "role": "numeric"} for feature in numeric)
    pd.DataFrame(rows).to_csv(review / "feature_registry_resolved.csv", index=False)
    (review / "feature_table_hash_and_shape.json").write_text(json.dumps({
        "path": "data/modeling/person_phase2_features.parquet",
        "sha256": sha256_file(master_path),
        "rows": len(master),
        "columns": len(master.columns),
        "sample_rows": len(sample),
        "note": "The full frozen table is intentionally excluded from the ZIP.",
    }, indent=2) + "\n", encoding="utf-8")
    sample.to_parquet(review / "person_phase2_5_features_sample.parquet", index=False, compression="zstd")


def environment_assets(stage: Path) -> None:
    run_info = stage / "run_info"
    run_info.mkdir(parents=True, exist_ok=True)
    packages = ["python", "pandas", "numpy", "scikit-learn", "catboost", "pyarrow", "matplotlib"]
    lines = [f"python={sys.version.replace(chr(10), ' ')}"]
    for package in packages[1:]:
        try:
            lines.append(f"{package}={importlib.metadata.version(package)}")
        except importlib.metadata.PackageNotFoundError:
            lines.append(f"{package}=NOT_INSTALLED")
    (run_info / "environment_versions.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    excluded = {".venv", "__pycache__", ".pytest_cache", ".git"}
    tree = []
    for path in sorted(PROJECT_ROOT.rglob("*")):
        relative = path.relative_to(PROJECT_ROOT)
        if any(part in excluded for part in relative.parts):
            continue
        if len(relative.parts) <= 4:
            tree.append(str(relative) + ("/" if path.is_dir() else ""))
    (run_info / "project_tree.txt").write_text("\n".join(tree) + "\n", encoding="utf-8")
    phase2_logs = sorted((PROJECT_ROOT / "outputs/logs").glob("phase2*.log"))
    text = "Phase 2 preserved run evidence\n\n" + "\n".join(
        f"## {path.name}\n{path.read_text(encoding='utf-8', errors='replace')}" for path in phase2_logs
    )
    (run_info / "run_phase2.log").write_text(text, encoding="utf-8")
    for name in ["run_phase2_5.log", "pytest_phase2_5.log"]:
        source = PROJECT_ROOT / "outputs/phase2_5/logs" / name
        if source.exists():
            shutil.copy2(source, run_info / name)
        else:
            (run_info / name).write_text("Not available at packaging time.\n", encoding="utf-8")
    git = subprocess.run(["git", "-C", str(PROJECT_ROOT), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if git.returncode == 0:
        commands = {
            "git_status.txt": ["git", "-C", str(PROJECT_ROOT), "status", "--short"],
            "git_diff_stat.txt": ["git", "-C", str(PROJECT_ROOT), "diff", "--stat"],
            "git_commit.txt": ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"],
        }
        for name, command in commands.items():
            result = subprocess.run(command, capture_output=True, text=True)
            (run_info / name).write_text(result.stdout + result.stderr, encoding="utf-8")


def review_index(stage: Path) -> None:
    text = """# CBDB Phase 2.5 Review Index

## Version and status

- Database: `cbdb_20260829.sqlite3` (database binary excluded; SHA256 is in invariants)
- Phase 2: PASS and preserved
- Phase 2.5: PASS pending human scientific review
- Formal SHAP run: false

## Core questions

This bundle separates gender/cohort, address observability, raw historical geography, train-only density, supervised local target prior, family observability, family topology, full-record cross-sectional family capital, train-observed inductive family capital, and documentation structure. It also evaluates unseen spatial groups and V1/V2a/V2b/posting targets.

## Recommended review order

1. `docs/phase2_5/phase2_5_results.md`
2. `outputs/phase2_5/tables/paired_bootstrap_results.csv`
3. `outputs/phase2_5/tables/spatial_robustness_results.csv`
4. `outputs/phase2_5/tables/documentation_controlled_ablation.csv`
5. `outputs/phase2_5/tables/model_candidate_manifest.json`
6. `outputs/phase2_5/figures/`
7. Prediction Parquet files for independent metric reproduction

## Model ID guide

- P0–P3: dynasty, gender, SAFE cohort, SAFE-year observability
- G0–G5: personal → observability → administrative geography → continuous space → train-only density → supervised local prior
- F1–F4: family observability → topology → full-record cross-sectional capital / train-observed inductive capital
- D0–D6/D6i: documentation baseline with staged historical signals
- S0–S2/S2i/SD: target-sensitivity stages; S2p is posting-relative sensitivity only
- M3/M4/M5/M6: preserved original Phase 2 models

## Known limitations

CBDB is a selected historical database, not a population sample. V1 is ENTRY record presence. Full-record family features are temporally ambiguous/transductive. The local target prior is supervised. SAFE birth and dated-relative coverage are sparse. Balanced class weights may impair raw probability calibration. A statistically stable ∼0.001 AUC delta remains practically small.

No candidate is automatically locked for SHAP. Human review is required.
"""
    (stage / "REVIEW_INDEX.md").write_text(text, encoding="utf-8")


def category(relative: str) -> str:
    if relative.startswith("docs/"):
        return "documentation"
    if relative.startswith("outputs/phase2_5/figures") or relative.startswith("outputs/phase2/figures"):
        return "figure"
    if relative.startswith("outputs/"):
        return "result_or_invariant"
    if relative.startswith("data/phase2_5/predictions"):
        return "prediction"
    if relative.startswith("configs/"):
        return "configuration"
    if relative.startswith("scripts/") or relative.startswith("src/"):
        return "source"
    if relative.startswith("tests/"):
        return "test"
    if relative.startswith("feature_review/"):
        return "feature_review"
    if relative.startswith("run_info/"):
        return "environment_and_run"
    return "index_or_manifest"


def manifests(stage: Path) -> int:
    files = sorted(path for path in stage.rglob("*") if path.is_file() and path.name not in {"ZIP_MANIFEST.csv", "ZIP_MANIFEST.md"})
    rows = []
    for path in files:
        relative = str(path.relative_to(stage))
        rows.append({
            "relative_path": relative,
            "file_size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "category": category(relative),
            "description": "Phase 2/2.5 review artifact",
        })
    frame = pd.DataFrame(rows)
    frame.to_csv(stage / "ZIP_MANIFEST.csv", index=False)
    summary = frame.groupby("category").agg(files=("relative_path", "size"), bytes=("file_size_bytes", "sum")).reset_index()
    lines = ["# ZIP Manifest Summary", "", f"Manifested files: {len(frame)}", "", "| Category | Files | Bytes |", "| --- | ---: | ---: |"]
    lines.extend(f"| {row.category} | {row.files} | {row.bytes} |" for row in summary.itertuples())
    lines.extend(["", "`ZIP_MANIFEST.csv` contains per-file SHA256 values. The two manifest files do not self-manifest to avoid recursive hashes.", ""])
    (stage / "ZIP_MANIFEST.md").write_text("\n".join(lines), encoding="utf-8")
    return len(list(path for path in stage.rglob("*") if path.is_file()))


def main() -> int:
    logger = setup_logging("phase2_5_package", PROJECT_ROOT / "outputs/phase2_5/logs/package_review.log")
    invariant = json.loads((PROJECT_ROOT / "outputs/phase2_5/tables/phase2_5_invariants.json").read_text())
    if invariant.get("status") != "PASS" or invariant.get("formal_shap_run") is not False:
        raise RuntimeError("Cannot package before Phase 2.5 invariants PASS")
    temporary_root = Path(tempfile.mkdtemp(prefix="cbdb_phase2_5_review_"))
    stage = temporary_root / "cbdb_phase2_5_review_bundle"
    stage.mkdir()
    try:
        copy_file(PROJECT_ROOT / "docs/phase2/phase2_results.md", stage)
        for name in [
            "model_metrics.csv", "ablation_results.csv", "robustness_results.csv", "prebirth_lineage_results.csv",
            "logistic_coefficients.csv", "catboost_feature_importance.csv", "phase2_invariants.json",
        ]:
            copy_file(PROJECT_ROOT / "outputs/phase2/tables" / name, stage)
        copy_tree_files(PROJECT_ROOT / "outputs/phase2/figures", stage)
        copy_tree_files(PROJECT_ROOT / "docs/phase2_5", stage)
        for directory in ["tables", "figures", "logs"]:
            copy_tree_files(PROJECT_ROOT / "outputs/phase2_5" / directory, stage)
        for name in [
            "feature_policy.yaml", "feature_registry.yaml", "phase2_features.yaml", "phase2_models.yaml",
            "phase2_5_features.yaml", "phase2_5_models.yaml", "phase2_5_protocol.yaml",
        ]:
            copy_file(PROJECT_ROOT / "configs" / name, stage)
        for path in sorted((PROJECT_ROOT / "scripts").glob("*.py")):
            if re_match_phase_script(path.name):
                copy_file(path, stage)
        for name in ["run_phase2.sh", "run_phase2_5.sh"]:
            copy_file(PROJECT_ROOT / "scripts" / name, stage)
        for name in ["feature_policy.py", "modeling.py", "metrics.py", "geography.py", "family.py", "feature_builders.py", "phase25.py"]:
            copy_file(PROJECT_ROOT / "src" / name, stage)
        for path in sorted((PROJECT_ROOT / "tests").glob("test_phase2*.py")) + [PROJECT_ROOT / "tests/test_feature_policy.py"]:
            if path.exists():
                copy_file(path, stage)
        for path in [
            PROJECT_ROOT / "outputs/tables/data_foundation_freeze_manifest.json",
            PROJECT_ROOT / "data/splits/split_manifest.json",
        ]:
            copy_file(path, stage)
        for name in [
            "predictions_primary_core.parquet", "predictions_family_robustness.parquet",
            "predictions_spatial_robustness.parquet", "predictions_target_sensitivity.parquet",
        ]:
            copy_file(PROJECT_ROOT / "data/phase2_5/predictions" / name, stage)
        feature_review_assets(stage)
        environment_assets(stage)
        review_index(stage)
        file_count = manifests(stage)

        bundle_dir = PROJECT_ROOT / "review_bundles"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        zip_path = bundle_dir / "cbdb_phase2_5_review_bundle.zip"
        if zip_path.exists():
            zip_path.unlink()
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path in sorted(stage.rglob("*")):
                if path.is_file():
                    archive.write(path, arcname=str(path.relative_to(stage)))
        check = subprocess.run(["unzip", "-t", str(zip_path)], capture_output=True, text=True)
        if check.returncode != 0 or "No errors detected" not in check.stdout:
            raise RuntimeError(f"unzip -t failed: {check.stdout}\n{check.stderr}")
        digest = sha256_file(zip_path)
        atomic_write_text(bundle_dir / "cbdb_phase2_5_review_bundle.sha256", f"{digest}  {zip_path.name}\n")
        verification = {
            "status": "PASS", "zip_path": str(zip_path.relative_to(PROJECT_ROOT)),
            "zip_size_bytes": zip_path.stat().st_size, "zip_sha256": digest,
            "unzip_test": "PASS", "file_count": file_count,
        }
        atomic_write_text(bundle_dir / "cbdb_phase2_5_review_bundle_verification.json", json.dumps(verification, indent=2) + "\n")
        logger.info("Review ZIP PASS: files=%d size=%d sha256=%s", file_count, zip_path.stat().st_size, digest)
    finally:
        shutil.rmtree(temporary_root, ignore_errors=True)
    print("================================================")
    print("PHASE 2.5 DOCUMENTATION-CONTROLLED VALIDATION PASS")
    print("================================================")
    print("Review bundle:")
    print("review_bundles/cbdb_phase2_5_review_bundle.zip")
    return 0


def re_match_phase_script(name: str) -> bool:
    try:
        prefix = int(name.split("_", 1)[0])
    except (ValueError, IndexError):
        return False
    return 20 <= prefix <= 41


if __name__ == "__main__":
    raise SystemExit(main())
