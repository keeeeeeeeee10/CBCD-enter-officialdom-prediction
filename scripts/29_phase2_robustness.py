#!/usr/bin/env python3
"""Run frozen-split family, temporal, pre-birth, and Qing holdout checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import atomic_to_csv, atomic_to_parquet, load_yaml
from src.metrics import binary_metrics, optimal_balanced_accuracy_threshold
from src.modeling import (
    build_logistic_pipeline,
    predictor_frame,
    prepare_model_data,
    prepare_model_data_from_assignments,
)
from src.utils import atomic_write_text, setup_logging


PRIMARY_POPULATIONS = ["Global", "Song", "Ming"]
ALL_POPULATIONS = ["Global", "Song", "Ming", "Qing"]
FEATURE_SETS = ["M0", "M0b", "M1", "M2", "M3", "M4", "M5", "M6"]
PREBIRTH_FEATURE_SETS = ["PB0", "PB1"]


def _metric_rows(
    prepared,
    probability: np.ndarray,
    population: str,
    feature_set: str,
    split_protocol: str,
    analysis: str,
    threshold_source: str,
    threshold: float,
) -> dict[str, object]:
    y_test = prepared.test["target_entry_v1"].astype(int).to_numpy()
    return {
        "algorithm": "LogisticRegression",
        "model_variant": "balanced",
        "analysis": analysis,
        "population": population,
        "feature_set": feature_set,
        "split_protocol": split_protocol,
        "evaluation_split": "test",
        "threshold_source": threshold_source,
        "threshold": threshold,
        "n_train": len(prepared.train),
        "n_validation": len(prepared.validation),
        "n_test": len(prepared.test),
        "train_positive_rate": float(prepared.train["target_entry_v1"].mean()),
        "validation_positive_rate": float(prepared.validation["target_entry_v1"].mean()),
        "test_positive_rate": float(prepared.test["target_entry_v1"].mean()),
        "best_iteration": np.nan,
        **binary_metrics(y_test, probability, threshold),
    }


def _fit_logistic(
    prepared,
    config: dict[str, object],
    population: str,
    feature_set: str,
    split_protocol: str,
    analysis: str,
) -> tuple[list[dict[str, object]], pd.DataFrame]:
    train_x = predictor_frame(prepared.train, prepared)
    validation_x = predictor_frame(prepared.validation, prepared)
    test_x = predictor_frame(prepared.test, prepared)
    train_y = prepared.train["target_entry_v1"].astype(int).to_numpy()
    validation_y = prepared.validation["target_entry_v1"].astype(int).to_numpy()
    test_y = prepared.test["target_entry_v1"].astype(int).to_numpy()
    if len(np.unique(train_y)) < 2 or len(np.unique(validation_y)) < 2 or len(np.unique(test_y)) < 2:
        raise RuntimeError(f"Both target classes are required for {analysis}/{population}/{feature_set}")

    model = build_logistic_pipeline(
        prepared.categorical,
        prepared.numeric,
        config,
        class_weight=str(config["class_weight"]),
    )
    model.fit(train_x, train_y)
    validation_probability = model.predict_proba(validation_x)[:, 1]
    test_probability = model.predict_proba(test_x)[:, 1]
    threshold = optimal_balanced_accuracy_threshold(validation_y, validation_probability)
    rows = [
        _metric_rows(
            prepared, test_probability, population, feature_set, split_protocol,
            analysis, "fixed_0.5", 0.5,
        ),
        _metric_rows(
            prepared, test_probability, population, feature_set, split_protocol,
            analysis, "validation_balanced_accuracy", threshold,
        ),
    ]
    prediction = pd.DataFrame({
        "algorithm": "LogisticRegression",
        "model_variant": "balanced",
        "analysis": analysis,
        "population": population,
        "feature_set": feature_set,
        "split_protocol": split_protocol,
        "person_id": prepared.test["person_id"].to_numpy(),
        "y_true": test_y,
        "y_probability": test_probability,
    })
    return rows, prediction


def _run_standard_split(
    dataset: pd.DataFrame,
    model_config: dict[str, object],
    split_protocol: str,
    analysis: str,
    populations: list[str],
    feature_sets: list[str],
    safe_birth_subset: bool = False,
) -> tuple[list[dict[str, object]], list[pd.DataFrame], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    predictions: list[pd.DataFrame] = []
    failures: list[dict[str, object]] = []
    for population in populations:
        for feature_set in feature_sets:
            try:
                prepared = prepare_model_data(
                    dataset,
                    population,
                    feature_set,
                    split_protocol=split_protocol,
                    safe_birth_subset=safe_birth_subset,
                    seed=int(model_config["seed"]),
                )
                metric_rows, prediction = _fit_logistic(
                    prepared, model_config["logistic"], population, feature_set,
                    split_protocol, analysis,
                )
                rows.extend(metric_rows)
                predictions.append(prediction)
            except Exception as exc:  # pragma: no cover - reported and failed at the end
                failures.append({
                    "analysis": analysis,
                    "population": population,
                    "feature_set": feature_set,
                    "error": repr(exc),
                })
    return rows, predictions, failures


def qing_holdout_assignments(dataset: pd.DataFrame) -> pd.DataFrame:
    """Use the frozen Qing holdout and primary train/validation assignments."""
    frozen = pd.read_parquet(
        PROJECT_ROOT / "data/interim/person_split_assignments.parquet",
        columns=["person_id", "split_holdout_qing"],
    )
    frame = dataset[["person_id", "dynasty_name", "split_primary"]].merge(
        frozen, on="person_id", how="inner", validate="one_to_one"
    )
    qing_ids = set(frame.loc[frame["dynasty_name"].eq("Qing"), "person_id"])
    frozen_qing_ids = set(frame.loc[frame["split_holdout_qing"].eq("test"), "person_id"])
    if qing_ids != frozen_qing_ids:
        raise RuntimeError("Frozen Qing holdout does not match the Qing population")
    source = frame["dynasty_name"].isin(["Song", "Yuan", "Ming"])
    included = (source & frame["split_primary"].isin(["train", "validation"])) | frame["split_holdout_qing"].eq("test")
    output = frame.loc[included, ["person_id", "dynasty_name", "split_primary", "split_holdout_qing"]].copy()
    output["split"] = np.select(
        [
            output["split_holdout_qing"].eq("test"),
            output["split_primary"].eq("train"),
            output["split_primary"].eq("validation"),
        ],
        ["test", "train", "validation"],
        default="excluded",
    )
    output = output.loc[output["split"].isin(["train", "validation", "test"]), ["person_id", "split"]]
    if output["split"].value_counts().reindex(["train", "validation", "test"]).isna().any():
        raise RuntimeError("Qing holdout assignment is missing a partition")
    return output


def run_qing_holdout(
    dataset: pd.DataFrame,
    model_config: dict[str, object],
) -> tuple[list[dict[str, object]], list[pd.DataFrame], list[dict[str, object]]]:
    assignments = qing_holdout_assignments(dataset)
    rows: list[dict[str, object]] = []
    predictions: list[pd.DataFrame] = []
    failures: list[dict[str, object]] = []
    for feature_set in FEATURE_SETS:
        try:
            prepared = prepare_model_data_from_assignments(
                dataset,
                assignments,
                "Global",
                feature_set,
                split_protocol="qing_holdout",
                seed=int(model_config["seed"]),
            )
            metric_rows, prediction = _fit_logistic(
                prepared, model_config["logistic"], "Qing", feature_set,
                "qing_holdout", "qing_holdout",
            )
            rows.extend(metric_rows)
            prediction["population"] = "Qing"
            predictions.append(prediction)
        except Exception as exc:  # pragma: no cover - reported and failed at the end
            failures.append({
                "analysis": "qing_holdout",
                "population": "Qing",
                "feature_set": feature_set,
                "error": repr(exc),
            })
    return rows, predictions, failures


def save_metric_views(metrics: pd.DataFrame) -> None:
    tables = PROJECT_ROOT / "outputs/phase2/tables"
    for analysis, filename in {
        "family_group_robustness": "family_robustness_metrics.csv",
        "temporal_sensitivity": "temporal_sensitivity_metrics.csv",
        "qing_holdout": "qing_holdout_metrics.csv",
    }.items():
        subset = metrics.loc[metrics["analysis"].eq(analysis)].copy()
        atomic_to_csv(subset, tables / filename)


def save_temporal_support_audit(dataset: pd.DataFrame) -> pd.DataFrame:
    eligible = dataset.loc[dataset["split_temporal"].ne("not_eligible"), [
        "dynasty_name", "split_temporal", "target_entry_v1"
    ]].copy()
    rows = []
    for population in ["Global", "Song", "Ming", "Qing"]:
        subset = eligible if population == "Global" else eligible.loc[eligible["dynasty_name"].eq(population)]
        counts = subset["split_temporal"].value_counts()
        rows.append({
            "population": population,
            "safe_people": len(subset),
            "safe_positive": int(subset["target_entry_v1"].sum()),
            "train_n": int(counts.get("train", 0)),
            "validation_n": int(counts.get("validation", 0)),
            "test_n": int(counts.get("test", 0)),
            "supports_three_partitions": bool(all(counts.get(name, 0) > 0 for name in ["train", "validation", "test"])),
        })
    audit = pd.DataFrame(rows)
    atomic_to_csv(audit, PROJECT_ROOT / "outputs/phase2/tables/temporal_support_audit.csv")
    return audit


def main() -> int:
    logger = setup_logging("phase2_robustness", PROJECT_ROOT / "outputs/logs/phase2_robustness.log")
    dataset = pd.read_parquet(PROJECT_ROOT / "data/modeling/person_phase2_features.parquet")
    model_config = load_yaml("configs/phase2_models.yaml")
    all_rows: list[dict[str, object]] = []
    all_predictions: list[pd.DataFrame] = []
    failures: list[dict[str, object]] = []
    temporal_audit = save_temporal_support_audit(dataset)

    for kwargs in [
        {
            "split_protocol": "family",
            "analysis": "family_group_robustness",
            "populations": PRIMARY_POPULATIONS,
            "feature_sets": FEATURE_SETS,
        },
        {
            "split_protocol": "temporal",
            "analysis": "temporal_sensitivity",
            "populations": ["Global", "Qing"],
            "feature_sets": FEATURE_SETS,
        },
        {
            "split_protocol": "primary",
            "analysis": "prebirth_lineage",
            "populations": ALL_POPULATIONS,
            "feature_sets": PREBIRTH_FEATURE_SETS,
            "safe_birth_subset": True,
        },
    ]:
        rows, predictions, errors = _run_standard_split(dataset, model_config, **kwargs)
        all_rows.extend(rows)
        all_predictions.extend(predictions)
        failures.extend(errors)

    rows, predictions, errors = run_qing_holdout(dataset, model_config)
    all_rows.extend(rows)
    all_predictions.extend(predictions)
    failures.extend(errors)

    if failures:
        atomic_write_text(
            PROJECT_ROOT / "outputs/phase2/tables/robustness_failures.json",
            json.dumps(failures, ensure_ascii=False, indent=2) + "\n",
        )
        raise RuntimeError(f"Robustness analyses failed: {failures[:3]}")

    metrics = pd.DataFrame(all_rows).sort_values(
        ["analysis", "population", "feature_set", "threshold_source"]
    )
    predictions = pd.concat(all_predictions, ignore_index=True)
    atomic_to_csv(metrics, PROJECT_ROOT / "outputs/phase2/tables/robustness_metrics.csv")
    save_metric_views(metrics)
    atomic_to_parquet(predictions, PROJECT_ROOT / "data/modeling/phase2_predictions_robustness.parquet")
    failure_path = PROJECT_ROOT / "outputs/phase2/tables/robustness_failures.json"
    if failure_path.exists():
        failure_path.unlink()
    status = {
        "status": "PASS",
        "family_rows": int(metrics["analysis"].eq("family_group_robustness").sum()),
        "temporal_rows": int(metrics["analysis"].eq("temporal_sensitivity").sum()),
        "prebirth_rows": int(metrics["analysis"].eq("prebirth_lineage").sum()),
        "qing_holdout_rows": int(metrics["analysis"].eq("qing_holdout").sum()),
        "prediction_rows": int(len(predictions)),
        "failure_count": 0,
        "temporal_supported_populations": temporal_audit.loc[
            temporal_audit["supports_three_partitions"], "population"
        ].tolist(),
        "temporal_skipped_for_insufficient_partition_support": temporal_audit.loc[
            ~temporal_audit["supports_three_partitions"], "population"
        ].tolist(),
        "qing_holdout_definition": "Song/Yuan/Ming frozen primary train/validation; all Qing frozen test",
    }
    atomic_write_text(
        PROJECT_ROOT / "outputs/phase2/tables/robustness_status.json",
        json.dumps(status, ensure_ascii=False, indent=2) + "\n",
    )
    logger.info(
        "Robustness PASS: metrics=%d predictions=%d family=%d temporal=%d prebirth=%d qing=%d",
        len(metrics), len(predictions), status["family_rows"], status["temporal_rows"],
        status["prebirth_rows"], status["qing_holdout_rows"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
