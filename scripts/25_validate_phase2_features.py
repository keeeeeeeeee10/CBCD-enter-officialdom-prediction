#!/usr/bin/env python3
"""Validate Phase 2 feature ranges, missingness, registry boundaries, and leakage risk."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import atomic_to_csv, load_yaml, resolve_feature_set
from src.feature_policy import validate_feature_set
from src.modeling import model_track
from src.utils import atomic_write_text, setup_logging


def feature_summary(frame: pd.DataFrame, feature_groups: dict[str, list[str]]) -> pd.DataFrame:
    reverse: dict[str, list[str]] = {}
    for group, columns in feature_groups.items():
        for column in columns:
            reverse.setdefault(column, []).append(group)
    rows = []
    for column in sorted(reverse):
        if column not in frame.columns:
            rows.append({"feature": column, "feature_sets": ";".join(reverse[column]), "storage": "fold_derived"})
            continue
        numeric = pd.to_numeric(frame[column], errors="coerce")
        rows.append({
            "feature": column,
            "feature_sets": ";".join(reverse[column]),
            "storage": "master_table",
            "dtype": str(frame[column].dtype),
            "n_non_missing": int(frame[column].notna().sum()),
            "coverage": float(frame[column].notna().mean()),
            "n_unique": int(frame[column].nunique(dropna=True)),
            "min": float(numeric.min()) if numeric.notna().any() else None,
            "max": float(numeric.max()) if numeric.notna().any() else None,
            "mean": float(numeric.mean()) if numeric.notna().any() else None,
        })
    return pd.DataFrame(rows)


def single_feature_association(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    feature: str,
    categorical: bool,
) -> dict[str, object]:
    y_train = train["target_entry_v1"].astype(int)
    y_validation = validation["target_entry_v1"].astype(int)
    global_prior = float(y_train.mean())
    if categorical:
        train_value = train[feature].astype("string").fillna("__MISSING__")
        validation_value = validation[feature].astype("string").fillna("__MISSING__")
        mapping = pd.DataFrame({"value": train_value, "target": y_train}).groupby("value")["target"].mean()
        score = validation_value.map(mapping).fillna(global_prior).astype(float)
        method = "train-category-rate to frozen validation"
    else:
        train_value = pd.to_numeric(train[feature], errors="coerce")
        validation_value = pd.to_numeric(validation[feature], errors="coerce")
        median = float(train_value.median()) if train_value.notna().any() else 0.0
        score = validation_value.fillna(median)
        method = "raw numeric with train median to frozen validation"
    if score.nunique(dropna=False) <= 1:
        auc = 0.5
    else:
        raw_auc = float(roc_auc_score(y_validation, score))
        auc = max(raw_auc, 1.0 - raw_auc)
    return {"feature": feature, "method": method, "validation_single_feature_auc": auc}


def main() -> int:
    logger = setup_logging("phase2_feature_validation", PROJECT_ROOT / "outputs/logs/phase2_feature_validation.log")
    frame = pd.read_parquet(PROJECT_ROOT / "data/modeling/person_phase2_features.parquet")
    registry = load_yaml("configs/phase2_features.yaml")
    if len(frame) != 661_124 or frame["person_id"].duplicated().any():
        raise RuntimeError("Phase 2 person-level uniqueness/count invariant failed")
    if int(frame["target_entry_v1"].sum()) != 220_627:
        raise RuntimeError("Phase 2 target invariant failed")

    groups: dict[str, list[str]] = {}
    categorical_union: set[str] = set()
    numeric_union: set[str] = set()
    for feature_set in ["M0", "M0b", "M1", "M2", "M3", "M4", "M5", "M6", "PB0", "PB1"]:
        categorical, numeric = resolve_feature_set(registry, feature_set)
        groups[feature_set] = categorical + numeric
        categorical_union.update(categorical)
        numeric_union.update(numeric)
        validate_feature_set(groups[feature_set], model_track(feature_set))
    all_predictors = set().union(*map(set, groups.values()))
    forbidden = set(registry["never_predict"])
    overlap = sorted(all_predictors & forbidden)
    if overlap:
        raise RuntimeError(f"Registry includes forbidden predictors: {overlap}")
    if "family_group_id" in all_predictors:
        raise RuntimeError("family_group_id cannot be a predictor")

    derived = set(registry["derived_fold_features"])
    missing_columns = sorted(all_predictors - set(frame.columns) - derived)
    if missing_columns:
        raise RuntimeError(f"Registered feature columns missing: {missing_columns}")
    range_checks = {
        "latitude": frame["latitude"].dropna().between(-90, 90).all(),
        "longitude": frame["longitude"].dropna().between(-180, 180).all(),
        "distance": frame["distance_to_dynasty_capital_km"].dropna().between(0, 20_050).all(),
        "counts_nonnegative": all(
            pd.to_numeric(frame[column], errors="coerce").dropna().ge(0).all()
            for column in all_predictors if column.startswith("n_") or column.endswith("_count") or column == "family_group_size"
        ),
        "ratios_bounded": all(
            pd.to_numeric(frame[column], errors="coerce").dropna().between(0, 1).all()
            for column in all_predictors
            if (column.endswith("_ratio") or "_ratio_" in column) and column in frame.columns
        ),
    }
    if not all(range_checks.values()):
        raise RuntimeError(f"Feature range validation failed: {range_checks}")

    summary = feature_summary(frame, groups)
    atomic_to_csv(summary, PROJECT_ROOT / "outputs/phase2/tables/feature_summary.csv")
    missingness = pd.DataFrame({
        "feature": [column for column in frame.columns if column not in {"person_id", "target_entry_v1"}],
        "n_missing": [int(frame[column].isna().sum()) for column in frame.columns if column not in {"person_id", "target_entry_v1"}],
        "missing_rate": [float(frame[column].isna().mean()) for column in frame.columns if column not in {"person_id", "target_entry_v1"}],
    }).sort_values(["missing_rate", "feature"], ascending=[False, True])
    atomic_to_csv(missingness, PROJECT_ROOT / "outputs/phase2/tables/feature_missingness.csv")

    train = frame.loc[frame["split_primary"].eq("train")]
    validation = frame.loc[frame["split_primary"].eq("validation")]
    association_rows = []
    for feature in sorted(all_predictors - derived):
        association_rows.append(single_feature_association(train, validation, feature, feature in categorical_union))
    association = pd.DataFrame(association_rows).sort_values("validation_single_feature_auc", ascending=False)
    atomic_to_csv(association, PROJECT_ROOT / "outputs/phase2/tables/feature_target_association.csv")
    warnings = association.loc[association["validation_single_feature_auc"].gt(0.95), "feature"].tolist()

    validation_document = {
        "status": "PASS",
        "n_people": len(frame),
        "v1_positive": int(frame["target_entry_v1"].sum()),
        "person_id_unique": True,
        "registered_feature_sets": list(groups),
        "fold_derived_features": sorted(derived),
        "forbidden_predictor_overlap": overlap,
        "range_checks": {key: bool(value) for key, value in range_checks.items()},
        "single_feature_auc_gt_0_95_warnings": warnings,
        "target_encoding_policy": "local_entry_prior is train-only/OOF and absent from the master table",
    }
    atomic_write_text(
        PROJECT_ROOT / "outputs/phase2/tables/feature_validation.json",
        json.dumps(validation_document, ensure_ascii=False, indent=2) + "\n",
    )
    document = [
        "# Phase 2 feature engineering",
        "",
        "The master table retains 661,124 unique CBDB people and the unchanged V1 label. Model matrices are selected from `configs/phase2_features.yaml`; no script automatically treats every master-table column as a predictor.",
        "",
        "## Personal",
        "",
        "`safe_birth_year` is copied only from valid SAFE provenance `01 — Based on Birth Year`; `safe_birth_decade` is its floor-to-decade representation. Raw birth and raw/safe index year are not simultaneously modeled. Missing SAFE birth years are not globally imputed.",
        "",
        "## Geography",
        "",
        "Primary background address selection, historical hierarchy matching, coordinates, canonical-capital approximation, and non-target local density are documented in `docs/audit/geography_feature_definition.md`. `local_entry_prior` is created only after loading a frozen split: training rows receive OOF encodings and validation/test receive a train-fitted mapping.",
        "",
        "## Family",
        "",
        "Family Structural features contain relationship/coverage counts only. Cross-sectional `ever_*` variables use relatives' lifetime CBDB ENTRY/posting records and carry temporal ambiguity. Pre-birth variables require both a SAFE focal birth year and a valid relative event year earlier than birth; missing relative event years stay missing.",
        "",
        "## Documentation",
        "",
        "M5 contains only the six domain flags and documentation intensity. These variables are excluded from M0–M4 and enter historical models only in M6.",
        "",
        f"Automated validation status: **PASS**. Single-feature AUC >0.95 warnings: {warnings or 'none'}.",
        "",
    ]
    atomic_write_text(PROJECT_ROOT / "docs/phase2/feature_engineering.md", "\n".join(document))
    logger.info("Feature validation PASS: %d registered predictors; warnings=%s", len(all_predictors), warnings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
