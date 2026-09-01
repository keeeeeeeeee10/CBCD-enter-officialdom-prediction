#!/usr/bin/env python3
"""Package and verify the self-contained Phase 2.6 final-lock review bundle."""

from __future__ import annotations

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

from src.utils import atomic_write_text, sha256_file, setup_logging


def copy_file(source: Path, stage: Path, relative: Path | None = None) -> None:
    if not source.exists():
        raise FileNotFoundError(source)
    target = stage / (relative or source.relative_to(PROJECT_ROOT))
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def copy_tree(source: Path, stage: Path) -> None:
    for path in sorted(source.rglob("*")):
        if path.is_file() and not any(part in {"__pycache__", ".pytest_cache"} for part in path.parts):
            copy_file(path, stage)


def review_index(stage: Path) -> None:
    metrics = pd.read_csv(PROJECT_ROOT / "outputs/phase2_6/tables/final_model_metrics.csv")
    global_metrics = metrics.loc[metrics["population"].eq("Global")]
    metric_lines = "\n".join(
        f"- {row.model_id}: ROC-AUC {row.roc_auc:.4f}, PR-AUC {row.pr_auc:.4f}, model SHA256 `{row.model_sha256}`"
        for row in global_metrics.itertuples()
    )
    text = f"""# CBDB Phase 2.6 Final Lock Review Index

## Version and status

- Database version: `cbdb_20260829.sqlite3` (binary intentionally excluded; hash is in invariants)
- Phase 1 through Phase 2.6: PASS
- Target V1: presence of at least one `ENTRY_DATA` record
- Formal grouped SHAP: completed for 3 models × 3 populations
- GNN / PageRank / hyperparameter search: not run

## Locked models

- **H_STRUCT:** historical structural prediction associations; preferred for relatively cleaner historical interpretation.
- **D5_MAIN:** main predictive model; includes documentation-linked information but no relatives’ outcome features.
- **D6_UPPER:** full-record database record-structure upper bound; not a strict pre-entry model.

Global frozen-test metrics:

{metric_lines}

## Recommended reading order

1. `docs/phase2_6/final_data_analysis.md`
2. `docs/phase2_6/final_model_report.md`
3. `docs/phase2_6/final_interpretation_and_limitations.md`
4. `docs/phase2_6/model_cards/H_STRUCT.md`
5. `outputs/phase2_6/tables/final_model_lock_manifest.json`
6. `outputs/phase2_6/tables/multiseed_delta_summary.csv`
7. `outputs/phase2_6/tables/matched_random_vs_spatial_results.csv`
8. `outputs/phase2_6/shap/shap_group_summary.csv`
9. `outputs/phase2_6/figures/`

## Interpretation boundary

Use H_STRUCT for structural predictive associations, D5_MAIN for prediction of CBDB ENTRY record presence, and D6_UPPER only as a database-internal upper bound. `addr_type_name` is address-record semantics, not pure geography. Full-record and train-observed family outcomes remain cross-sectional. SHAP explains model prediction attribution, not causal effect.

CBDB is a selected historical database and Global does not represent the total population of historical China. ENTRY presence is not actual office holding or actual government-entry probability.
"""
    (stage / "REVIEW_INDEX.md").write_text(text, encoding="utf-8")


def environment_assets(stage: Path) -> None:
    run_info = stage / "run_info"
    run_info.mkdir(parents=True, exist_ok=True)
    packages = ["pandas", "numpy", "scikit-learn", "catboost", "pyarrow", "matplotlib"]
    lines = [f"python={sys.version.replace(chr(10), ' ')}"]
    for package in packages:
        try:
            lines.append(f"{package}={importlib.metadata.version(package)}")
        except importlib.metadata.PackageNotFoundError:
            lines.append(f"{package}=NOT_INSTALLED")
    (run_info / "environment_versions.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    excluded = {".venv", "__pycache__", ".pytest_cache", ".git", "review_bundles"}
    tree = []
    for path in sorted(PROJECT_ROOT.rglob("*")):
        relative = path.relative_to(PROJECT_ROOT)
        if any(part in excluded for part in relative.parts):
            continue
        if len(relative.parts) <= 4:
            tree.append(str(relative) + ("/" if path.is_dir() else ""))
    (run_info / "project_tree.txt").write_text("\n".join(tree) + "\n", encoding="utf-8")
    for name in ["run_phase2_6.log", "pytest_phase2_6.log"]:
        copy_file(PROJECT_ROOT / "outputs/phase2_6/logs" / name, stage, Path("run_info") / name)
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


def category(relative: str) -> str:
    if relative.startswith("docs/"):
        return "documentation"
    if relative.startswith("outputs/phase2_6/figures"):
        return "figure"
    if relative.startswith("outputs/phase2_6/shap") or relative.startswith("data/phase2_6/shap_samples"):
        return "shap"
    if relative.startswith("data/phase2_6/predictions"):
        return "prediction"
    if relative.startswith("outputs/phase2_6/models"):
        return "canonical_model"
    if relative.startswith("outputs/"):
        return "result_or_invariant"
    if relative.startswith("configs/"):
        return "configuration"
    if relative.startswith("scripts/") or relative.startswith("src/"):
        return "source"
    if relative.startswith("tests/"):
        return "test"
    if relative.startswith("run_info/"):
        return "environment_and_run"
    return "index_or_manifest"


def manifests(stage: Path) -> int:
    files = sorted(
        path for path in stage.rglob("*")
        if path.is_file() and path.name not in {"ZIP_MANIFEST.csv", "ZIP_MANIFEST.md"}
    )
    rows = [{
        "relative_path": str(path.relative_to(stage)),
        "file_size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "category": category(str(path.relative_to(stage))),
        "description": "Phase 2.6 final-lock human-review artifact",
    } for path in files]
    frame = pd.DataFrame(rows)
    frame.to_csv(stage / "ZIP_MANIFEST.csv", index=False)
    summary = frame.groupby("category").agg(files=("relative_path", "size"), bytes=("file_size_bytes", "sum")).reset_index()
    lines = ["# ZIP Manifest Summary", "", f"Manifested files: {len(frame)}", "", "| Category | Files | Bytes |", "| --- | ---: | ---: |"]
    lines.extend(f"| {row.category} | {row.files} | {row.bytes} |" for row in summary.itertuples())
    lines.extend(["", "Per-file SHA256 values are in `ZIP_MANIFEST.csv`. Manifest files do not self-manifest.", ""])
    (stage / "ZIP_MANIFEST.md").write_text("\n".join(lines), encoding="utf-8")
    return len(list(path for path in stage.rglob("*") if path.is_file()))


def main() -> int:
    logger = setup_logging("phase2_6_package", PROJECT_ROOT / "outputs/phase2_6/logs/package_review.log")
    invariant = json.loads((PROJECT_ROOT / "outputs/phase2_6/tables/phase2_6_invariants.json").read_text())
    if invariant.get("status") != "PASS" or invariant.get("formal_shap_run") is not True:
        raise RuntimeError("Cannot package before Phase 2.6 invariants and formal SHAP PASS")
    temporary_root = Path(tempfile.mkdtemp(prefix="cbdb_phase2_6_review_"))
    stage = temporary_root / "cbdb_phase2_6_final_lock_review_bundle"
    stage.mkdir()
    try:
        copy_file(PROJECT_ROOT / "docs/phase2_5/phase2_5_results.md", stage)
        copy_tree(PROJECT_ROOT / "docs/phase2_6", stage)
        for directory in ["tables", "figures", "shap", "logs"]:
            copy_tree(PROJECT_ROOT / "outputs/phase2_6" / directory, stage)
        phase25_names = [
            "geography_decomposition_results.csv", "family_decomposition_results.csv",
            "documentation_controlled_ablation.csv", "spatial_robustness_results.csv",
            "target_sensitivity_results.csv", "paired_bootstrap_results.csv", "calibration_audit.csv",
            "model_candidate_manifest.json", "phase2_5_invariants.json",
        ]
        for name in phase25_names:
            copy_file(PROJECT_ROOT / "outputs/phase2_5/tables" / name, stage)
        copy_file(
            PROJECT_ROOT / "outputs/phase2_5/tables/calibration_audit.csv", stage,
            Path("outputs/phase2_5/tables/calibration_results.csv"),
        )
        for name in ["feature_policy.yaml", "feature_registry.yaml"]:
            copy_file(PROJECT_ROOT / "configs" / name, stage)
        for path in sorted((PROJECT_ROOT / "configs").glob("phase2_6_*.yaml")):
            copy_file(path, stage)
        for number in range(42, 53):
            matches = sorted((PROJECT_ROOT / "scripts").glob(f"{number}_*.py"))
            if len(matches) != 1:
                raise RuntimeError(f"Expected one Phase 2.6 script for prefix {number}: {matches}")
            copy_file(matches[0], stage)
        copy_file(PROJECT_ROOT / "scripts/run_phase2_6.sh", stage)
        for name in [
            "phase26.py", "phase25.py", "modeling.py", "metrics.py", "geography.py", "family.py",
            "feature_builders.py", "feature_policy.py", "utils.py", "cleaning.py",
        ]:
            copy_file(PROJECT_ROOT / "src" / name, stage)
        for path in sorted((PROJECT_ROOT / "tests").glob("test_phase2_6_*.py")):
            copy_file(path, stage)
        copy_file(PROJECT_ROOT / "data/phase2_6/predictions/final_model_predictions.parquet", stage)
        copy_file(PROJECT_ROOT / "data/phase2_6/shap_samples/shap_sample_ids.parquet", stage)
        copy_file(PROJECT_ROOT / "data/phase2_6/shap_samples/shap_values_sample.parquet", stage)
        metadata = PROJECT_ROOT / "outputs/phase2_6/models/canonical_model_metadata.json"
        copy_file(metadata, stage)
        model_files = [PROJECT_ROOT / f"outputs/phase2_6/models/{model}.cbm" for model in ["H_STRUCT", "D5_MAIN", "D6_UPPER"]]
        total_model_bytes = sum(path.stat().st_size for path in model_files)
        if total_model_bytes <= 100 * 1024 * 1024:
            for path in model_files:
                copy_file(path, stage)
        environment_assets(stage)
        review_index(stage)
        file_count = manifests(stage)
        bundle_dir = PROJECT_ROOT / "review_bundles"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        zip_path = bundle_dir / "cbdb_phase2_6_final_lock_review_bundle.zip"
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
        atomic_write_text(bundle_dir / "cbdb_phase2_6_final_lock_review_bundle.sha256", f"{digest}  {zip_path.name}\n")
        verification = {
            "status": "PASS", "zip_path": str(zip_path.relative_to(PROJECT_ROOT)),
            "zip_size_bytes": zip_path.stat().st_size, "zip_sha256": digest,
            "unzip_test": "PASS", "file_count": file_count,
            "canonical_models_included": total_model_bytes <= 100 * 1024 * 1024,
            "canonical_model_bytes": total_model_bytes,
        }
        atomic_write_text(
            bundle_dir / "cbdb_phase2_6_final_lock_review_bundle_verification.json",
            json.dumps(verification, indent=2) + "\n",
        )
        if zip_path.stat().st_size > 150 * 1024 * 1024:
            raise RuntimeError(f"Review ZIP exceeds 150 MiB: {zip_path.stat().st_size}")
        logger.info("Review ZIP PASS: files=%d size=%d sha256=%s", file_count, zip_path.stat().st_size, digest)
    finally:
        shutil.rmtree(temporary_root, ignore_errors=True)
    print("================================================")
    print("PHASE 2.6 FINAL MODEL LOCK & INTERPRETATION PASS")
    print("================================================")
    print("Review bundle:")
    print("review_bundles/cbdb_phase2_6_final_lock_review_bundle.zip")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
