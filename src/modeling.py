"""Frozen-split Phase 2 modeling utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.family import smoothed_ratio, training_family_prior
from src.feature_builders import load_yaml, population_mask, resolve_feature_set
from src.feature_policy import validate_feature_set
from src.geography import FoldSafeLocalEntryEncoder
from src.metrics import binary_metrics


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPLIT_FILES = {
    "primary": PROJECT_ROOT / "data/splits/split_primary_dynasty_target.parquet",
    "family": PROJECT_ROOT / "data/splits/split_family_group_robustness.parquet",
    "random": PROJECT_ROOT / "data/splits/split_random_benchmark.parquet",
    "temporal": PROJECT_ROOT / "data/splits/split_safe_temporal.parquet",
}


@dataclass
class PreparedData:
    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame
    categorical: list[str]
    numeric: list[str]
    feature_names: list[str]


def model_track(feature_set: str) -> str:
    if feature_set == "M5":
        return "documentation_only"
    if feature_set == "M6":
        return "historical_plus_documentation"
    if feature_set == "M4":
        return "cross_sectional_family"
    if feature_set.startswith("PB"):
        return "pre_birth_lineage"
    return "historical_only"


def _derive_fold_features(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
    features: set[str],
    registry: dict[str, Any],
    seed: int,
) -> None:
    if "local_entry_prior" in features:
        encoder = FoldSafeLocalEntryEncoder(
            alpha=float(registry["local_entry_prior_alpha"]),
            n_folds=int(registry["target_encoding_oof_folds"]),
            seed=seed,
        )
        train["local_entry_prior"] = encoder.fit_transform_train(
            train["addr_id"], train["target_entry_v1"], train["person_id"]
        )
        validation["local_entry_prior"] = encoder.transform(validation["addr_id"])
        test["local_entry_prior"] = encoder.transform(test["addr_id"])

    alpha = float(registry["family_ratio_alpha"])
    if "older_kin_entry_ratio_smoothed" in features:
        prior = training_family_prior(train["n_older_kin_ever_entry"], train["n_eligible_older_kin"])
        for frame in (train, validation, test):
            frame["older_kin_entry_ratio_smoothed"] = smoothed_ratio(
                frame["n_older_kin_ever_entry"], frame["n_eligible_older_kin"], prior, alpha
            )
    if "older_kin_posting_ratio_smoothed" in features:
        prior = training_family_prior(train["n_older_kin_ever_posting"], train["n_eligible_older_kin"])
        for frame in (train, validation, test):
            frame["older_kin_posting_ratio_smoothed"] = smoothed_ratio(
                frame["n_older_kin_ever_posting"], frame["n_eligible_older_kin"], prior, alpha
            )


def prepare_model_data(
    dataset: pd.DataFrame,
    population: str,
    feature_set: str,
    split_protocol: str = "primary",
    safe_birth_subset: bool = False,
    feature_config_path: str | Path = "configs/phase2_features.yaml",
    seed: int = 42,
) -> PreparedData:
    registry = load_yaml(feature_config_path)
    categorical, numeric = resolve_feature_set(registry, feature_set)
    feature_names = categorical + numeric
    validate_feature_set(feature_names, model_track(feature_set))

    split = pd.read_parquet(SPLIT_FILES[split_protocol]).rename(columns={"split": "frozen_split"})
    frame = dataset.merge(split, on="person_id", how="inner", validate="one_to_one")
    frame = frame.loc[population_mask(frame, population)].copy()
    if safe_birth_subset:
        frame = frame.loc[frame["has_safe_birth_year"].eq(1)].copy()
    train = frame.loc[frame["frozen_split"].eq("train")].copy()
    validation = frame.loc[frame["frozen_split"].eq("validation")].copy()
    test = frame.loc[frame["frozen_split"].eq("test")].copy()
    if min(len(train), len(validation), len(test)) == 0:
        raise RuntimeError(f"Empty frozen partition for {population}/{feature_set}/{split_protocol}")
    _derive_fold_features(train, validation, test, set(feature_names), registry, seed)
    missing = [name for name in feature_names if name not in train.columns]
    if missing:
        raise RuntimeError(f"Missing Phase 2 model features for {feature_set}: {missing}")
    return PreparedData(train, validation, test, categorical, numeric, feature_names)


def predictor_frame(frame: pd.DataFrame, prepared: PreparedData) -> pd.DataFrame:
    output = frame[prepared.feature_names].copy()
    for column in prepared.categorical:
        output[column] = output[column].astype("string").fillna("__MISSING__").astype(str)
    for column in prepared.numeric:
        output[column] = pd.to_numeric(output[column], errors="coerce").replace([np.inf, -np.inf], np.nan).astype(float)
    return output


def build_logistic_pipeline(
    categorical: list[str],
    numeric: list[str],
    config: dict[str, Any],
    class_weight: str | None,
) -> Pipeline:
    transformers = []
    if numeric:
        transformers.append((
            "numeric",
            Pipeline([
                ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
                ("scale", StandardScaler()),
            ]),
            numeric,
        ))
    if categorical:
        transformers.append((
            "categorical",
            Pipeline([
                ("imputer", SimpleImputer(strategy="constant", fill_value="__MISSING__")),
                ("onehot", OneHotEncoder(
                    handle_unknown="ignore",
                    min_frequency=int(config["onehot_min_frequency"]),
                )),
            ]),
            categorical,
        ))
    preprocessing = ColumnTransformer(transformers, remainder="drop")
    model = LogisticRegression(
        max_iter=int(config["max_iter"]),
        solver=str(config["solver"]),
        class_weight=class_weight,
        random_state=42,
    )
    return Pipeline([("preprocess", preprocessing), ("model", model)])


def all_predictors_constant(frame: pd.DataFrame, columns: list[str]) -> bool:
    return all(frame[column].nunique(dropna=False) <= 1 for column in columns)


def fit_catboost_candidates(
    prepared: PreparedData,
    config: dict[str, Any],
    seed: int,
) -> tuple[CatBoostClassifier | None, str, dict[str, float], np.ndarray, np.ndarray, int | None]:
    train_x = predictor_frame(prepared.train, prepared)
    validation_x = predictor_frame(prepared.validation, prepared)
    test_x = predictor_frame(prepared.test, prepared)
    train_y = prepared.train["target_entry_v1"].astype(int).to_numpy()
    validation_y = prepared.validation["target_entry_v1"].astype(int).to_numpy()

    if all_predictors_constant(train_x, prepared.feature_names):
        probability = float(train_y.mean())
        validation_probability = np.full(len(validation_x), probability)
        test_probability = np.full(len(test_x), probability)
        return None, "constant_unweighted", binary_metrics(validation_y, validation_probability), validation_probability, test_probability, None

    best: tuple[float, float, CatBoostClassifier, str, np.ndarray, np.ndarray, int | None] | None = None
    categorical_indices = [train_x.columns.get_loc(column) for column in prepared.categorical]
    for candidate in config["class_weight_candidates"]:
        mode = "unweighted" if candidate in (None, "None") else "balanced"
        params = {
            "iterations": int(config["iterations"]),
            "learning_rate": float(config["learning_rate"]),
            "depth": int(config["depth"]),
            "loss_function": str(config["loss_function"]),
            "eval_metric": str(config["eval_metric"]),
            "random_seed": seed,
            "l2_leaf_reg": float(config["l2_leaf_reg"]),
            "thread_count": int(config["thread_count"]),
            "verbose": bool(config["verbose"]),
            "allow_writing_files": False,
        }
        if mode == "balanced":
            params["auto_class_weights"] = "Balanced"
        model = CatBoostClassifier(**params)
        model.fit(
            train_x,
            train_y,
            cat_features=categorical_indices,
            eval_set=(validation_x, validation_y),
            early_stopping_rounds=int(config["early_stopping_rounds"]),
            verbose=False,
        )
        validation_probability = model.predict_proba(validation_x)[:, 1]
        validation_metrics = binary_metrics(validation_y, validation_probability)
        test_probability = model.predict_proba(test_x)[:, 1]
        candidate_key = (validation_metrics["roc_auc"], -validation_metrics["log_loss"])
        if best is None or candidate_key > (best[0], best[1]):
            best = (
                candidate_key[0], candidate_key[1], model, mode,
                validation_probability, test_probability, model.get_best_iteration(),
            )
    assert best is not None
    metrics = binary_metrics(validation_y, best[4])
    return best[2], best[3], metrics, best[4], best[5], best[6]
