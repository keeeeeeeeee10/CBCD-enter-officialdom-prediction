"""Shared Phase 2.5 split-safe feature derivation and fixed-model execution."""

from __future__ import annotations

import gc
import hashlib
import pickle
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from src.cleaning import clean_person_identifier
from src.family import INDUCTIVE_FEATURES, build_inductive_family_features
from src.feature_builders import atomic_to_csv, atomic_to_parquet, load_yaml, population_mask, resolve_feature_set
from src.feature_policy import validate_feature_set
from src.geography import FoldSafeLocalEntryEncoder, TrainOnlyRegionalDensity
from src.metrics import binary_metrics, optimal_balanced_accuracy_threshold
from src.modeling import PreparedData, build_logistic_pipeline, fit_catboost_candidates, predictor_frame


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TARGETS = ["target_entry_v1", "target_entry_v2a", "target_entry_v2b", "target_posting"]
SPLITS = {
    "primary": PROJECT_ROOT / "data/splits/split_primary_dynasty_target.parquet",
    "family": PROJECT_ROOT / "data/splits/split_family_group_robustness.parquet",
}
DOCUMENTATION = {
    "has_address", "has_kin", "has_assoc", "has_status", "has_text",
    "has_institution", "documentation_intensity",
}


@dataclass
class Phase25Run:
    metric: dict[str, object]
    test_predictions: pd.DataFrame
    validation_predictions: pd.DataFrame
    feature_metadata: pd.DataFrame


def load_phase25_dataset() -> pd.DataFrame:
    master = pd.read_parquet(PROJECT_ROOT / "data/modeling/person_phase2_features.parquet")
    targets = pd.read_parquet(PROJECT_ROOT / "data/interim/person_targets_v1_v2.parquet")
    if not master[["person_id"]].merge(targets[["person_id"]], on="person_id", how="outer", indicator=True)["_merge"].eq("both").all():
        raise RuntimeError("Target sensitivity IDs differ from frozen Phase 2 master IDs")
    if not master.set_index("person_id")["target_entry_v1"].sort_index().equals(
        targets.set_index("person_id")["target_entry_v1"].sort_index()
    ):
        raise RuntimeError("V1 differs between Phase 2 master and sensitivity target table")
    frame = master.merge(
        targets[["person_id", "target_entry_v2a", "target_entry_v2b", "target_posting"]],
        on="person_id", how="left", validate="one_to_one",
    )
    frame["has_valid_coordinates"] = (
        frame["latitude"].notna() & frame["longitude"].notna()
    ).astype("int8")
    frame["any_grandfather_identified"] = frame[[
        "paternal_grandfather_identified", "maternal_grandfather_identified"
    ]].max(axis=1).astype("int8")
    frame["spatial_group_id"] = make_spatial_group(frame)
    if len(frame) != 661_124 or frame["person_id"].duplicated().any():
        raise RuntimeError("Phase 2.5 master view violates frozen person invariant")
    return frame


def make_spatial_group(frame: pd.DataFrame) -> pd.Series:
    dynasty = frame["dynasty_code"].astype("string")
    prefecture = frame["prefecture_id"].astype("string")
    valid = dynasty.notna() & prefecture.notna()
    output = pd.Series(pd.NA, index=frame.index, dtype="string")
    output.loc[valid] = dynasty.loc[valid] + "::" + prefecture.loc[valid]
    return output


def build_relation_edge_cache() -> pd.DataFrame:
    output = PROJECT_ROOT / "data/phase2_5/older_kin_edges.parquet"
    if output.exists():
        return pd.read_parquet(output)
    people = set(pd.read_parquet(
        PROJECT_ROOT / "data/modeling/person_phase2_features.parquet", columns=["person_id"]
    )["person_id"].astype(int))
    taxonomy = pd.read_csv(PROJECT_ROOT / "outputs/tables/kinship_generation_taxonomy.csv")[[
        "kin_code", "generation_class", "specific_relation", "is_affinal"
    ]]
    database = PROJECT_ROOT / "database/cbdb_working.sqlite3"
    with sqlite3.connect(f"file:{database.resolve().as_posix()}?mode=ro", uri=True) as connection:
        relations = pd.read_sql_query(
            "SELECT c_personid AS person_id, c_kin_id AS kin_id, c_kin_code AS kin_code FROM KIN_DATA",
            connection,
        )
    relations["person_id"] = clean_person_identifier(relations["person_id"])
    relations["kin_id"] = clean_person_identifier(relations["kin_id"])
    relations = relations.dropna(subset=["person_id", "kin_id"]).copy()
    relations[["person_id", "kin_id"]] = relations[["person_id", "kin_id"]].astype("int64")
    relations = relations.loc[
        relations["person_id"].isin(people)
        & relations["kin_id"].isin(people)
        & relations["person_id"].ne(relations["kin_id"])
    ].merge(taxonomy, on="kin_code", how="left", validate="many_to_one")
    relations["is_affinal"] = relations["is_affinal"].fillna(True).astype(bool)
    relations = relations.loc[
        ~relations["is_affinal"]
        & (
            relations["generation_class"].isin(["ancestor", "parent_generation"])
            | relations["specific_relation"].isin(["father", "paternal_grandfather", "maternal_grandfather"])
        )
    ].sort_values(["person_id", "kin_id", "kin_code"], kind="mergesort")
    relations = relations.drop_duplicates(["person_id", "kin_id"], keep="first")[[
        "person_id", "kin_id", "generation_class", "specific_relation"
    ]]
    atomic_to_parquet(relations, output)
    return relations


def _subset_mask(frame: pd.DataFrame, subset: str) -> pd.Series:
    if subset == "all":
        return pd.Series(True, index=frame.index)
    if subset == "geography_covered":
        return frame["has_geography"].eq(1)
    if subset == "family_observed":
        return frame["has_kin"].eq(1)
    if subset == "eligible_older_kin":
        return frame["n_eligible_older_kin"].gt(0)
    if subset == "verified_male":
        return frame["gender"].eq("male")
    raise KeyError(f"Unknown Phase 2.5 subset: {subset}")


def _split_path(split_protocol: str, population: str) -> Path:
    if split_protocol in SPLITS:
        return SPLITS[split_protocol]
    if split_protocol == "spatial":
        return PROJECT_ROOT / f"data/phase2_5/splits/split_spatial_group_{population.lower()}.parquet"
    raise KeyError(f"Unknown split protocol: {split_protocol}")


def _model_track(feature_names: Iterable[str]) -> str:
    return "historical_plus_documentation" if set(feature_names) & DOCUMENTATION else "historical_only"


def prepare_phase25_data(
    dataset: pd.DataFrame,
    population: str,
    model_id: str,
    target_name: str = "target_entry_v1",
    split_protocol: str = "primary",
    subset: str = "all",
    seed: int = 42,
    feature_config_path: str | Path = "configs/phase2_5_features.yaml",
) -> PreparedData:
    if target_name not in TARGETS:
        raise KeyError(f"Unknown sensitivity target: {target_name}")
    registry = load_yaml(feature_config_path)
    categorical, numeric = resolve_feature_set(registry, model_id)
    feature_names = categorical + numeric
    forbidden = set(registry["never_predict"])
    if forbidden & set(feature_names):
        raise RuntimeError(f"Forbidden Phase 2.5 predictors: {sorted(forbidden & set(feature_names))}")
    validate_feature_set(feature_names, _model_track(feature_names))

    split = pd.read_parquet(_split_path(split_protocol, population)).rename(columns={"split": "frozen_split"})
    frame = dataset.merge(split, on="person_id", how="inner", validate="one_to_one")
    frame = frame.loc[population_mask(frame, population) & _subset_mask(frame, subset)].copy()
    if split_protocol == "spatial":
        if "spatial_group_id_y" in frame.columns:
            frame["spatial_group_id"] = frame["spatial_group_id_y"].astype("string")
            frame = frame.drop(columns=[column for column in ["spatial_group_id_x", "spatial_group_id_y"] if column in frame])
    train = frame.loc[frame["frozen_split"].eq("train")].copy()
    validation = frame.loc[frame["frozen_split"].eq("validation")].copy()
    test = frame.loc[frame["frozen_split"].eq("test")].copy()
    if min(len(train), len(validation), len(test)) == 0:
        raise RuntimeError(f"Empty partition for {population}/{model_id}/{target_name}/{split_protocol}/{subset}")
    for part in (train, validation, test):
        part["target_entry_v1"] = part[target_name].astype("int8")

    features = set(feature_names)
    region_key = registry["region_key"]
    if {"train_region_person_count", "train_region_log_density"} & features:
        density = TrainOnlyRegionalDensity().fit(train[region_key])
        for part in (train, validation, test):
            derived = density.transform(part[region_key])
            part[derived.columns] = derived
    if "local_target_prior" in features:
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
    if set(INDUCTIVE_FEATURES) & features:
        relations = build_relation_edge_cache()
        source_target = "target_entry_v1" if target_name == "target_posting" else target_name
        outcome = dataset[["person_id", source_target]].rename(columns={source_target: "relative_outcome"})
        training_ids = set(train["person_id"].astype(int))
        for part in (train, validation, test):
            derived = build_inductive_family_features(
                part["person_id"], relations, training_ids, outcome
            ).set_index("person_id")
            for column in INDUCTIVE_FEATURES:
                part[column] = part["person_id"].map(derived[column])

    missing = sorted(set(feature_names) - set(train.columns))
    if missing:
        raise RuntimeError(f"Missing Phase 2.5 features for {model_id}: {missing}")
    return PreparedData(train, validation, test, categorical, numeric, feature_names)


def _prediction_frame(
    prepared: PreparedData,
    probabilities: np.ndarray,
    evaluation_split: str,
    algorithm: str,
    variant: str,
    population: str,
    target_name: str,
    split_protocol: str,
    model_id: str,
    subset: str,
    threshold: float,
) -> pd.DataFrame:
    part = prepared.validation if evaluation_split == "validation" else prepared.test
    result = pd.DataFrame({
        "person_id": part["person_id"].astype("int64").to_numpy(),
        "population": population,
        "split_protocol": split_protocol,
        "target_name": target_name,
        "algorithm": algorithm,
        "model_id": model_id,
        "subset": subset,
        "model_variant": variant,
        "evaluation_split": evaluation_split,
        "y_true": part["target_entry_v1"].astype("int8").to_numpy(),
        "y_probability": probabilities,
        "validation_frozen_threshold": threshold,
        "y_pred": (probabilities >= threshold).astype("int8"),
        "family_group_id": part["family_group_id"].astype("int64").to_numpy(),
        "spatial_group_id": part["spatial_group_id"].astype("string").to_numpy(),
    })
    return result


def run_fixed_model(
    dataset: pd.DataFrame,
    population: str,
    model_id: str,
    algorithm: str,
    target_name: str = "target_entry_v1",
    split_protocol: str = "primary",
    subset: str = "all",
    model_config_path: str | Path = "configs/phase2_5_models.yaml",
) -> Phase25Run:
    config = load_yaml(model_config_path)
    seed = int(config["seed"])
    prepared = prepare_phase25_data(
        dataset, population, model_id, target_name, split_protocol, subset, seed
    )
    validation_y = prepared.validation["target_entry_v1"].astype(int).to_numpy()
    test_y = prepared.test["target_entry_v1"].astype(int).to_numpy()
    metadata_rows: list[dict[str, object]] = []
    if algorithm == "LogisticRegression":
        train_x = predictor_frame(prepared.train, prepared)
        validation_x = predictor_frame(prepared.validation, prepared)
        test_x = predictor_frame(prepared.test, prepared)
        model = build_logistic_pipeline(
            prepared.categorical, prepared.numeric, config["logistic"], class_weight="balanced"
        )
        model.fit(train_x, prepared.train["target_entry_v1"].astype(int).to_numpy())
        validation_probability = model.predict_proba(validation_x)[:, 1]
        test_probability = model.predict_proba(test_x)[:, 1]
        variant = "balanced"
        best_iteration = None
        names = model.named_steps["preprocess"].get_feature_names_out()
        values = model.named_steps["model"].coef_[0]
        for index in np.argsort(np.abs(values))[::-1][:30]:
            metadata_rows.append({"feature": str(names[index]), "value": float(values[index]), "rank": len(metadata_rows) + 1})
        model_sha256 = hashlib.sha256(pickle.dumps(model, protocol=5)).hexdigest()
    elif algorithm == "CatBoost":
        model, variant, validation_metrics, validation_probability, test_probability, best_iteration = fit_catboost_candidates(
            prepared, config["catboost"], seed
        )
        if model is None:
            importances = np.zeros(len(prepared.feature_names))
        else:
            importances = model.get_feature_importance()
        for index in np.argsort(importances)[::-1]:
            metadata_rows.append({"feature": prepared.feature_names[index], "value": float(importances[index]), "rank": len(metadata_rows) + 1})
        if model is None:
            payload = f"constant|{population}|{model_id}|{target_name}|{prepared.train['target_entry_v1'].mean()}".encode()
        else:
            payload = bytes(model._serialize_model())
        model_sha256 = hashlib.sha256(payload).hexdigest()
    else:
        raise KeyError(f"Unknown algorithm: {algorithm}")

    threshold = optimal_balanced_accuracy_threshold(validation_y, validation_probability)
    fixed = binary_metrics(test_y, test_probability, 0.5)
    threshold_metrics = binary_metrics(test_y, test_probability, threshold)
    validation_metrics = binary_metrics(validation_y, validation_probability, threshold)
    metric = {
        "algorithm": algorithm,
        "model_variant": variant,
        "population": population,
        "model_id": model_id,
        "target_name": target_name,
        "split_protocol": split_protocol,
        "subset": subset,
        "n_train": len(prepared.train),
        "n_validation": len(prepared.validation),
        "n_test": len(prepared.test),
        "test_positive_rate": float(test_y.mean()),
        "validation_frozen_threshold": threshold,
        "best_iteration": best_iteration,
        "model_sha256": model_sha256,
        **fixed,
        "balanced_accuracy_validation_threshold": threshold_metrics["balanced_accuracy"],
        "f1_validation_threshold": threshold_metrics["f1"],
        "validation_roc_auc": validation_metrics["roc_auc"],
        "validation_pr_auc": validation_metrics["pr_auc"],
        "validation_log_loss": validation_metrics["log_loss"],
    }
    test_predictions = _prediction_frame(
        prepared, test_probability, "test", algorithm, variant, population,
        target_name, split_protocol, model_id, subset, threshold,
    )
    validation_predictions = _prediction_frame(
        prepared, validation_probability, "validation", algorithm, variant, population,
        target_name, split_protocol, model_id, subset, threshold,
    )
    metadata = pd.DataFrame(metadata_rows)
    for key, value in {
        "algorithm": algorithm, "population": population, "model_id": model_id,
        "target_name": target_name, "split_protocol": split_protocol, "subset": subset,
    }.items():
        metadata[key] = value
    del prepared, model
    gc.collect()
    return Phase25Run(metric, test_predictions, validation_predictions, metadata)


def save_analysis_outputs(
    analysis: str,
    metrics: list[dict[str, object]],
    tests: list[pd.DataFrame],
    validations: list[pd.DataFrame],
    metadata: list[pd.DataFrame] | None = None,
) -> None:
    tables = PROJECT_ROOT / "outputs/phase2_5/tables"
    predictions = PROJECT_ROOT / "data/phase2_5/predictions/parts"
    atomic_to_csv(pd.DataFrame(metrics), tables / f"{analysis}.csv")
    atomic_to_parquet(pd.concat(tests, ignore_index=True), predictions / f"{analysis}_test.parquet")
    atomic_to_parquet(pd.concat(validations, ignore_index=True), predictions / f"{analysis}_validation.parquet")
    if metadata:
        atomic_to_csv(pd.concat(metadata, ignore_index=True), tables / f"{analysis}_feature_metadata.csv")


def metric_deltas(
    metrics: pd.DataFrame,
    ordered_models: list[str],
    group_columns: list[str],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for keys, group in metrics.groupby(group_columns, dropna=False, sort=True):
        if not isinstance(keys, tuple):
            keys = (keys,)
        indexed = group.set_index("model_id")
        for previous, current in zip(ordered_models[:-1], ordered_models[1:], strict=True):
            if previous not in indexed.index or current not in indexed.index:
                continue
            row = dict(zip(group_columns, keys, strict=True))
            row.update({
                "model_a": previous,
                "model_b": current,
                "comparison": f"{current} - {previous}",
                "delta_roc_auc": float(indexed.loc[current, "roc_auc"] - indexed.loc[previous, "roc_auc"]),
                "delta_pr_auc": float(indexed.loc[current, "pr_auc"] - indexed.loc[previous, "pr_auc"]),
                "delta_log_loss": float(indexed.loc[current, "log_loss"] - indexed.loc[previous, "log_loss"]),
            })
            rows.append(row)
    return pd.DataFrame(rows)
