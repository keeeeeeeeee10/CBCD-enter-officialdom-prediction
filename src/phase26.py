"""Shared Phase 2.6 final-lock, split-safe modeling, and audit utilities."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.linear_model import LogisticRegression

from src.family import INDUCTIVE_FEATURES, build_inductive_family_features
from src.feature_builders import load_yaml, population_mask, resolve_feature_set
from src.feature_policy import validate_feature_set
from src.geography import FoldSafeLocalEntryEncoder, TrainOnlyRegionalDensity
from src.metrics import binary_metrics, optimal_balanced_accuracy_threshold
from src.modeling import PreparedData, fit_catboost_candidates, predictor_frame
from src.phase25 import build_relation_edge_cache, load_phase25_dataset
from src.utils import sha256_file


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FEATURE_CONFIG = PROJECT_ROOT / "configs/phase2_6_features.yaml"
MODEL_CONFIG = PROJECT_ROOT / "configs/phase2_6_models.yaml"
PRIMARY_SPLIT = PROJECT_ROOT / "data/splits/split_primary_dynasty_target.parquet"

GENERAL_DOCUMENTATION = {
    "has_address", "has_assoc", "has_status", "has_text", "has_institution",
    "documentation_intensity",
}
FAMILY_OBSERVABILITY = {
    "has_kin", "has_core_family", "father_identified", "mother_identified",
    "any_grandfather_identified",
}
FULL_RECORD_FAMILY = {
    "father_ever_entry", "father_ever_posting",
    "paternal_grandfather_ever_entry", "paternal_grandfather_ever_posting",
    "maternal_grandfather_ever_entry", "maternal_grandfather_ever_posting",
    "n_older_kin_ever_entry", "n_older_kin_ever_posting",
    "older_kin_entry_ratio", "older_kin_posting_ratio",
}
FORBIDDEN_STRUCTURAL = (
    GENERAL_DOCUMENTATION
    | {"addr_type_name", "local_target_prior"}
    | FULL_RECORD_FAMILY
    | set(INDUCTIVE_FEATURES)
)


@dataclass
class Phase26Run:
    model: CatBoostClassifier
    prepared: PreparedData
    metric: dict[str, object]
    test_predictions: pd.DataFrame
    validation_predictions: pd.DataFrame
    calibration: dict[str, float]


def load_phase26_dataset() -> pd.DataFrame:
    """Return the immutable Phase 2 feature view plus split-safe derived keys."""
    return load_phase25_dataset()


def model_features(model_id: str) -> tuple[list[str], list[str], list[str]]:
    registry = load_yaml(FEATURE_CONFIG)
    categorical, numeric = resolve_feature_set(registry, model_id)
    return categorical, numeric, categorical + numeric


def _model_track(features: Iterable[str]) -> str:
    names = set(features)
    if names & (GENERAL_DOCUMENTATION | {"has_kin"}):
        return "historical_plus_documentation"
    if names & FULL_RECORD_FAMILY:
        return "cross_sectional_family"
    return "historical_only"


def validate_locked_feature_sets() -> dict[str, dict[str, object]]:
    """Fail closed on the three final feature definitions."""
    registry = load_yaml(FEATURE_CONFIG)
    never = set(registry["never_predict"])
    resolved: dict[str, dict[str, object]] = {}
    for model_id in ["H_STRUCT", "D5_MAIN", "D6_UPPER"]:
        categorical, numeric = resolve_feature_set(registry, model_id)
        features = categorical + numeric
        validate_feature_set(features, _model_track(features))
        overlap = sorted(set(features) & never)
        if overlap:
            raise RuntimeError(f"{model_id} contains globally forbidden features: {overlap}")
        resolved[model_id] = {
            "categorical": categorical,
            "numeric": numeric,
            "features": features,
        }

    h_features = set(resolved["H_STRUCT"]["features"])
    forbidden_h = sorted(h_features & FORBIDDEN_STRUCTURAL)
    if forbidden_h:
        raise RuntimeError(f"H_STRUCT contains forbidden/documentation/outcome features: {forbidden_h}")
    if not FAMILY_OBSERVABILITY.issubset(h_features):
        raise RuntimeError("H_STRUCT is missing registered family-observability features")

    d5 = set(resolved["D5_MAIN"]["features"])
    forbidden_d5 = sorted(d5 & (FULL_RECORD_FAMILY | set(INDUCTIVE_FEATURES)))
    if forbidden_d5:
        raise RuntimeError(f"D5_MAIN contains family outcome features: {forbidden_d5}")
    d6 = set(resolved["D6_UPPER"]["features"])
    extra = d6 - d5
    if extra != FULL_RECORD_FAMILY:
        raise RuntimeError(
            "D6_UPPER additions differ from the explicit full-record allowlist: "
            f"missing={sorted(FULL_RECORD_FAMILY-extra)}, unexpected={sorted(extra-FULL_RECORD_FAMILY)}"
        )
    return resolved


def _normalise_split(split_path: Path) -> pd.DataFrame:
    split = pd.read_parquet(split_path)
    if "split" not in split.columns:
        raise RuntimeError(f"Split lacks split column: {split_path}")
    columns = [column for column in ["person_id", "split", "spatial_group_id"] if column in split]
    split = split[columns].rename(columns={"split": "frozen_split"}).copy()
    if split["person_id"].duplicated().any() or split["frozen_split"].isna().any():
        raise RuntimeError(f"Invalid split keys: {split_path}")
    unexpected = sorted(set(split["frozen_split"]) - {"train", "validation", "test"})
    if unexpected:
        raise RuntimeError(f"Unexpected split labels in {split_path}: {unexpected}")
    return split


def _subset(frame: pd.DataFrame, subset: str) -> pd.DataFrame:
    if subset == "all":
        return frame
    if subset == "birth_observed":
        return frame.loc[frame["has_safe_birth_year"].eq(1)]
    if subset == "address_observed":
        return frame.loc[frame["has_geography"].eq(1)]
    raise KeyError(f"Unknown Phase 2.6 subset: {subset}")


def prepare_phase26_data(
    dataset: pd.DataFrame,
    population: str,
    model_id: str,
    *,
    split_path: str | Path = PRIMARY_SPLIT,
    subset: str = "all",
    seed: int = 42,
) -> PreparedData:
    registry = load_yaml(FEATURE_CONFIG)
    categorical, numeric = resolve_feature_set(registry, model_id)
    features = categorical + numeric
    forbidden = sorted(set(features) & set(registry["never_predict"]))
    if forbidden:
        raise RuntimeError(f"Forbidden Phase 2.6 predictors in {model_id}: {forbidden}")
    validate_feature_set(features, _model_track(features))

    split = _normalise_split(Path(split_path))
    frame = dataset.merge(split, on="person_id", how="inner", validate="one_to_one", suffixes=("", "_split"))
    if "spatial_group_id_split" in frame:
        frame["spatial_group_id"] = frame["spatial_group_id_split"].astype("string")
        frame = frame.drop(columns="spatial_group_id_split")
    frame = _subset(frame.loc[population_mask(frame, population)].copy(), subset).copy()
    train = frame.loc[frame["frozen_split"].eq("train")].copy()
    validation = frame.loc[frame["frozen_split"].eq("validation")].copy()
    test = frame.loc[frame["frozen_split"].eq("test")].copy()
    if min(len(train), len(validation), len(test)) == 0:
        raise RuntimeError(f"Empty partition for {population}/{model_id}/{subset}/{split_path}")

    if {"safe_birth_year_neutral", "safe_birth_decade_neutral"} & set(features):
        medians = {
            source: float(pd.to_numeric(train[source], errors="coerce").median())
            for source in ["safe_birth_year", "safe_birth_decade"]
        }
        for part in (train, validation, test):
            part["safe_birth_year_neutral"] = pd.to_numeric(
                part["safe_birth_year"], errors="coerce"
            ).fillna(medians["safe_birth_year"])
            part["safe_birth_decade_neutral"] = pd.to_numeric(
                part["safe_birth_decade"], errors="coerce"
            ).fillna(medians["safe_birth_decade"])

    feature_set = set(features)
    region_key = str(registry["region_key"])
    if {"train_region_person_count", "train_region_log_density"} & feature_set:
        density = TrainOnlyRegionalDensity().fit(train[region_key])
        for part in (train, validation, test):
            derived = density.transform(part[region_key])
            part[derived.columns] = derived
    if "local_target_prior" in feature_set:
        encoder = FoldSafeLocalEntryEncoder(
            alpha=float(registry["local_prior_alpha"]),
            n_folds=int(registry["local_prior_oof_folds"]),
            seed=seed,
        )
        train["local_target_prior"] = encoder.fit_transform_train(
            train[region_key], train["target_entry_v1"], train["person_id"]
        )
        validation["local_target_prior"] = encoder.transform(validation[region_key])
        test["local_target_prior"] = encoder.transform(test[region_key])
    if feature_set & set(INDUCTIVE_FEATURES):
        relations = build_relation_edge_cache()
        outcomes = dataset[["person_id", "target_entry_v1"]].rename(
            columns={"target_entry_v1": "relative_outcome"}
        )
        training_ids = set(train["person_id"].astype(int))
        for part in (train, validation, test):
            derived = build_inductive_family_features(
                part["person_id"], relations, training_ids, outcomes
            ).set_index("person_id")
            for column in INDUCTIVE_FEATURES:
                part[column] = part["person_id"].map(derived[column])

    missing = sorted(set(features) - set(train.columns))
    if missing:
        raise RuntimeError(f"Missing Phase 2.6 features for {model_id}: {missing}")
    return PreparedData(train, validation, test, categorical, numeric, features)


def expected_calibration_error(y: np.ndarray, probability: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0.0, 1.0, bins + 1)
    bucket = np.clip(np.digitize(probability, edges[1:-1], right=True), 0, bins - 1)
    total = 0.0
    for index in range(bins):
        mask = bucket == index
        if mask.any():
            total += float(mask.mean()) * abs(float(y[mask].mean()) - float(probability[mask].mean()))
    return float(total)


def _calibrate(
    validation_y: np.ndarray,
    validation_probability: np.ndarray,
    test_y: np.ndarray,
    test_probability: np.ndarray,
) -> tuple[np.ndarray, dict[str, float]]:
    val = np.clip(validation_probability, 1e-6, 1 - 1e-6)
    tst = np.clip(test_probability, 1e-6, 1 - 1e-6)
    calibrator = LogisticRegression(solver="lbfgs", random_state=42)
    calibrator.fit(np.log(val / (1 - val)).reshape(-1, 1), validation_y)
    calibrated = calibrator.predict_proba(np.log(tst / (1 - tst)).reshape(-1, 1))[:, 1]
    raw = binary_metrics(test_y, tst)
    calibrated_metrics = binary_metrics(test_y, calibrated)
    return calibrated, {
        "raw_ece": expected_calibration_error(test_y, tst),
        "calibrated_ece": expected_calibration_error(test_y, calibrated),
        "raw_probability_bias": float(tst.mean() - test_y.mean()),
        "calibrated_probability_bias": float(calibrated.mean() - test_y.mean()),
        "raw_brier": float(raw["brier_score"]),
        "calibrated_brier": float(calibrated_metrics["brier_score"]),
        "raw_log_loss": float(raw["log_loss"]),
        "calibrated_log_loss": float(calibrated_metrics["log_loss"]),
        "sigmoid_coefficient": float(calibrator.coef_[0, 0]),
        "sigmoid_intercept": float(calibrator.intercept_[0]),
    }


def prediction_hash(frame: pd.DataFrame) -> str:
    ordered = frame.sort_values("person_id")[["person_id", "y_true", "y_probability_raw"]]
    payload = ordered.to_csv(index=False, float_format="%.17g").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def fit_phase26_model(
    dataset: pd.DataFrame,
    population: str,
    model_id: str,
    *,
    seed: int,
    split_path: str | Path = PRIMARY_SPLIT,
    split_protocol: str = "primary",
    subset: str = "all",
) -> Phase26Run:
    config = load_yaml(MODEL_CONFIG)
    prepared = prepare_phase26_data(
        dataset, population, model_id, split_path=split_path, subset=subset, seed=seed
    )
    model, variant, _, validation_probability, test_probability, best_iteration = fit_catboost_candidates(
        prepared, config["catboost"], seed
    )
    if model is None:
        raise RuntimeError(f"Final Phase 2.6 CatBoost model unexpectedly constant: {population}/{model_id}")
    validation_y = prepared.validation["target_entry_v1"].astype(int).to_numpy()
    test_y = prepared.test["target_entry_v1"].astype(int).to_numpy()
    threshold = optimal_balanced_accuracy_threshold(validation_y, validation_probability)
    fixed = binary_metrics(test_y, test_probability, 0.5)
    threshold_metrics = binary_metrics(test_y, test_probability, threshold)
    validation_metrics = binary_metrics(validation_y, validation_probability, threshold)
    calibrated, calibration = _calibrate(
        validation_y, validation_probability, test_y, test_probability
    )

    def predictions(part: pd.DataFrame, y: np.ndarray, raw: np.ndarray, calibrated_values: np.ndarray | None, evaluation: str) -> pd.DataFrame:
        values = {
            "person_id": part["person_id"].astype("int64").to_numpy(),
            "population": population,
            "model_id": model_id,
            "target": "target_entry_v1",
            "split_protocol": split_protocol,
            "split": evaluation,
            "seed": seed,
            "y_true": y.astype("int8"),
            "y_probability_raw": raw,
            "y_probability_calibrated_if_available": calibrated_values if calibrated_values is not None else np.nan,
            "frozen_threshold": threshold,
            "y_pred": (raw >= threshold).astype("int8"),
            "model_variant": variant,
        }
        return pd.DataFrame(values)

    test_predictions = predictions(prepared.test, test_y, test_probability, calibrated, "test")
    validation_predictions = predictions(
        prepared.validation, validation_y, validation_probability, None, "validation"
    )
    metric = {
        "algorithm": "CatBoost",
        "population": population,
        "model_id": model_id,
        "target": "target_entry_v1",
        "split_protocol": split_protocol,
        "subset": subset,
        "seed": seed,
        "model_variant": variant,
        "n_train": len(prepared.train),
        "n_validation": len(prepared.validation),
        "n_test": len(prepared.test),
        "test_positive_rate": float(test_y.mean()),
        "frozen_threshold": threshold,
        "best_iteration": int(best_iteration) if best_iteration is not None else None,
        **fixed,
        "balanced_accuracy_validation_threshold": threshold_metrics["balanced_accuracy"],
        "f1_validation_threshold": threshold_metrics["f1"],
        "validation_roc_auc": validation_metrics["roc_auc"],
        "validation_pr_auc": validation_metrics["pr_auc"],
        "validation_log_loss": validation_metrics["log_loss"],
        "raw_ece": calibration["raw_ece"],
        "calibrated_ece": calibration["calibrated_ece"],
        "calibration_status": "validation_fitted_sigmoid_diagnostic",
        "prediction_sha256": prediction_hash(test_predictions),
    }
    return Phase26Run(model, prepared, metric, test_predictions, validation_predictions, calibration)


def save_catboost_atomic(model: CatBoostClassifier, path: str | Path) -> str:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    model.save_model(str(temporary), format="cbm")
    os.replace(temporary, destination)
    return sha256_file(destination)


def load_locked_model(population: str, model_id: str) -> CatBoostClassifier:
    path = PROJECT_ROOT / f"outputs/phase2_6/models/{population.lower()}/{model_id}.cbm"
    if not path.exists():
        raise FileNotFoundError(path)
    model = CatBoostClassifier()
    model.load_model(str(path), format="cbm")
    return model


def feature_group_lookup(features: Iterable[str]) -> dict[str, str]:
    registry = load_yaml(FEATURE_CONFIG)
    lookup: dict[str, str] = {}
    for group, names in registry["shap_feature_groups"].items():
        for name in names:
            if name in lookup:
                raise RuntimeError(f"SHAP feature belongs to multiple groups: {name}")
            lookup[str(name)] = str(group)
    return {str(feature): lookup.get(str(feature), "other") for feature in features}


def locked_manifest_payload(metrics: pd.DataFrame) -> dict[str, Any]:
    resolved = validate_locked_feature_sets()
    rows = []
    for row in metrics.itertuples(index=False):
        rows.append({
            "population": row.population,
            "model_id": row.model_id,
            "seed": int(row.seed),
            "model_sha256": row.model_sha256,
            "prediction_sha256": row.prediction_sha256,
            "validation_roc_auc": float(row.validation_roc_auc),
            "test_roc_auc": float(row.roc_auc),
        })
    return {
        "status": "FINAL_MODELS_LOCKED",
        "canonical_seed": 42,
        "best_seed_selection_performed": False,
        "test_set_used_for_model_selection": False,
        "target": "target_entry_v1",
        "split": "frozen_primary",
        "models": {
            "H_STRUCT": {
                "meaning": "Historical structural prediction association",
                "feature_count": len(resolved["H_STRUCT"]["features"]),
                "forbidden_feature_check": "PASS",
            },
            "D5_MAIN": {
                "meaning": "Main documentation-linked predictive model without relatives outcomes",
                "feature_count": len(resolved["D5_MAIN"]["features"]),
                "family_outcome_check": "PASS",
            },
            "D6_UPPER": {
                "meaning": "Full-record database record-structure upper bound",
                "feature_count": len(resolved["D6_UPPER"]["features"]),
                "increment_allowlist_check": "PASS",
            },
        },
        "canonical_runs": rows,
    }


def json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"
