#!/usr/bin/env python3
"""Run family-aware, largest-component, and pre-birth lineage robustness analyses."""

from __future__ import annotations

import gc
import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import atomic_to_csv, atomic_to_parquet, load_yaml
from src.metrics import binary_metrics, optimal_balanced_accuracy_threshold
from src.modeling import (
    build_logistic_pipeline,
    fit_catboost_candidates,
    predictor_frame,
    prepare_model_data,
)
from src.utils import setup_logging


def metric_row(
    algorithm: str,
    variant: str,
    population: str,
    feature_set: str,
    split_protocol: str,
    prepared,
    probability: np.ndarray,
    threshold_source: str,
    threshold: float,
    best_iteration: int | None = None,
) -> dict[str, object]:
    y_test = prepared.test["target_entry_v1"].astype(int).to_numpy()
    return {
        "algorithm": algorithm,
        "model_variant": variant,
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
        "best_iteration": best_iteration,
        **binary_metrics(y_test, probability, threshold),
    }


def fit_logistic(prepared, config: dict) -> tuple[object, np.ndarray, np.ndarray, float]:
    train_x = predictor_frame(prepared.train, prepared)
    validation_x = predictor_frame(prepared.validation, prepared)
    test_x = predictor_frame(prepared.test, prepared)
    model = build_logistic_pipeline(prepared.categorical, prepared.numeric, config, class_weight="balanced")
    model.fit(train_x, prepared.train["target_entry_v1"].astype(int).to_numpy())
    validation_probability = model.predict_proba(validation_x)[:, 1]
    test_probability = model.predict_proba(test_x)[:, 1]
    threshold = optimal_balanced_accuracy_threshold(
        prepared.validation["target_entry_v1"].astype(int).to_numpy(), validation_probability
    )
    return model, validation_probability, test_probability, threshold


def prediction_frame(algorithm: str, variant: str, population: str, feature_set: str, split_protocol: str, prepared, probability: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame({
        "algorithm": algorithm,
        "model_variant": variant,
        "population": population,
        "feature_set": feature_set,
        "split_protocol": split_protocol,
        "person_id": prepared.test["person_id"].to_numpy(),
        "y_true": prepared.test["target_entry_v1"].astype(np.int8).to_numpy(),
        "y_probability": probability,
    })


def primary_main_metrics(metrics: pd.DataFrame) -> pd.DataFrame:
    keep = metrics["split_protocol"].eq("primary") & metrics["threshold_source"].eq("fixed_0.5")
    keep &= ~(
        metrics["algorithm"].eq("LogisticRegression")
        & ~metrics["model_variant"].eq("balanced")
    )
    return metrics.loc[keep].copy()


def family_split_robustness(dataset: pd.DataFrame, config: dict, logger) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    predictions = []
    seed = int(config["seed"])
    for population in ["Global", "Ming"]:
        for feature_set in ["M0", "M4"]:
            prepared = prepare_model_data(
                dataset, population, feature_set, split_protocol="family", seed=seed
            )
            logistic, _, probability, threshold = fit_logistic(prepared, config["logistic"])
            rows.extend([
                metric_row("LogisticRegression", "balanced", population, feature_set, "family", prepared, probability, "fixed_0.5", 0.5),
                metric_row("LogisticRegression", "balanced", population, feature_set, "family", prepared, probability, "validation_balanced_accuracy", threshold),
            ])
            predictions.append(prediction_frame(
                "LogisticRegression", "balanced", population, feature_set, "family", prepared, probability
            ))
            del logistic

            model, mode, validation_metrics, validation_probability, probability, best_iteration = fit_catboost_candidates(
                prepared, config["catboost"], seed
            )
            threshold = optimal_balanced_accuracy_threshold(
                prepared.validation["target_entry_v1"].astype(int).to_numpy(), validation_probability
            )
            rows.extend([
                metric_row("CatBoost", mode, population, feature_set, "family", prepared, probability, "fixed_0.5", 0.5, best_iteration),
                metric_row("CatBoost", mode, population, feature_set, "family", prepared, probability, "validation_balanced_accuracy", threshold, best_iteration),
            ])
            predictions.append(prediction_frame(
                "CatBoost", mode, population, feature_set, "family", prepared, probability
            ))
            logger.info(
                "Family split %s/%s complete: Logistic AUC=%.4f; CatBoost(%s) AUC=%.4f",
                population, feature_set, rows[-4]["roc_auc"], mode, rows[-2]["roc_auc"],
            )
            del prepared, model, validation_probability, probability
            gc.collect()
    return pd.DataFrame(rows), pd.concat(predictions, ignore_index=True)


def compare_family_splits(primary: pd.DataFrame, family: pd.DataFrame) -> pd.DataFrame:
    family_main = family.loc[family["threshold_source"].eq("fixed_0.5")]
    rows = []
    for _, family_row in family_main.iterrows():
        matched = primary.loc[
            primary["algorithm"].eq(family_row["algorithm"])
            & primary["population"].eq(family_row["population"])
            & primary["feature_set"].eq(family_row["feature_set"])
        ]
        if len(matched) != 1:
            raise RuntimeError("Primary/family robustness match is not unique")
        primary_row = matched.iloc[0]
        rows.append({
            "analysis": "primary_vs_family_group_split",
            "algorithm": family_row["algorithm"],
            "population": family_row["population"],
            "feature_set": family_row["feature_set"],
            "reference": "primary",
            "comparison": "family",
            "reference_n_test": int(primary_row["n_test"]),
            "comparison_n_test": int(family_row["n_test"]),
            "reference_roc_auc": primary_row["roc_auc"],
            "comparison_roc_auc": family_row["roc_auc"],
            "delta_roc_auc": family_row["roc_auc"] - primary_row["roc_auc"],
            "reference_pr_auc": primary_row["pr_auc"],
            "comparison_pr_auc": family_row["pr_auc"],
            "delta_pr_auc": family_row["pr_auc"] - primary_row["pr_auc"],
            "reference_log_loss": primary_row["log_loss"],
            "comparison_log_loss": family_row["log_loss"],
            "delta_log_loss": family_row["log_loss"] - primary_row["log_loss"],
        })
    return pd.DataFrame(rows)


def largest_component_sensitivity(dataset: pd.DataFrame) -> pd.DataFrame:
    counts = dataset["family_group_id"].value_counts()
    largest_group = int(counts.index[0])
    largest_size = int(counts.iloc[0])
    predictions = pd.concat([
        pd.read_parquet(PROJECT_ROOT / "data/modeling/phase2_predictions_logistic.parquet"),
        pd.read_parquet(PROJECT_ROOT / "data/modeling/phase2_predictions_catboost.parquet"),
    ], ignore_index=True)
    predictions = predictions.loc[
        predictions["population"].eq("Global") & predictions["feature_set"].eq("M4")
    ].merge(dataset[["person_id", "family_group_id"]], on="person_id", validate="many_to_one")
    rows = []
    for (algorithm, variant), group in predictions.groupby(["algorithm", "model_variant"], sort=True):
        without = group.loc[~group["family_group_id"].eq(largest_group)]
        with_metrics = binary_metrics(group["y_true"].to_numpy(), group["y_probability"].to_numpy())
        without_metrics = binary_metrics(without["y_true"].to_numpy(), without["y_probability"].to_numpy())
        rows.append({
            "analysis": "largest_component_exclusion",
            "algorithm": algorithm,
            "population": "Global",
            "feature_set": "M4",
            "reference": "with_largest_component",
            "comparison": "without_largest_component",
            "largest_family_group_id": largest_group,
            "largest_component_global_size": largest_size,
            "largest_component_test_rows": int(group["family_group_id"].eq(largest_group).sum()),
            "reference_n_test": len(group),
            "comparison_n_test": len(without),
            "reference_roc_auc": with_metrics["roc_auc"],
            "comparison_roc_auc": without_metrics["roc_auc"],
            "delta_roc_auc": without_metrics["roc_auc"] - with_metrics["roc_auc"],
            "reference_pr_auc": with_metrics["pr_auc"],
            "comparison_pr_auc": without_metrics["pr_auc"],
            "delta_pr_auc": without_metrics["pr_auc"] - with_metrics["pr_auc"],
            "reference_log_loss": with_metrics["log_loss"],
            "comparison_log_loss": without_metrics["log_loss"],
            "delta_log_loss": without_metrics["log_loss"] - with_metrics["log_loss"],
        })
    return pd.DataFrame(rows)


def prebirth_robustness(dataset: pd.DataFrame, config: dict, logger) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows = []
    metric_rows = []
    predictions = []
    seed = int(config["seed"])
    for feature_set in ["PB0", "PB1"]:
        prepared = prepare_model_data(
            dataset, "Global", feature_set, split_protocol="primary",
            safe_birth_subset=True, seed=seed,
        )
        logistic, _, probability, threshold = fit_logistic(prepared, config["logistic"])
        logistic_row = metric_row(
            "LogisticRegression", "balanced", "Global", feature_set, "primary",
            prepared, probability, "fixed_0.5", 0.5,
        )
        metric_rows.extend([
            logistic_row,
            metric_row(
                "LogisticRegression", "balanced", "Global", feature_set, "primary",
                prepared, probability, "validation_balanced_accuracy", threshold,
            ),
        ])
        predictions.append(prediction_frame(
            "LogisticRegression", "balanced", "Global", feature_set, "primary", prepared, probability
        ))
        rows.append(logistic_row.copy())
        del logistic

        model, mode, validation_metrics, validation_probability, probability, best_iteration = fit_catboost_candidates(
            prepared, config["catboost"], seed
        )
        threshold = optimal_balanced_accuracy_threshold(
            prepared.validation["target_entry_v1"].astype(int).to_numpy(), validation_probability
        )
        catboost_row = metric_row(
            "CatBoost", mode, "Global", feature_set, "primary", prepared,
            probability, "fixed_0.5", 0.5, best_iteration,
        )
        metric_rows.extend([
            catboost_row,
            metric_row(
                "CatBoost", mode, "Global", feature_set, "primary", prepared,
                probability, "validation_balanced_accuracy", threshold, best_iteration,
            ),
        ])
        predictions.append(prediction_frame(
            "CatBoost", mode, "Global", feature_set, "primary", prepared, probability
        ))
        rows.append(catboost_row.copy())
        logger.info(
            "Pre-birth %s complete: N(test)=%d; Logistic AUC=%.4f; CatBoost AUC=%.4f",
            feature_set, len(prepared.test), logistic_row["roc_auc"], catboost_row["roc_auc"],
        )
        del prepared, model, validation_probability, probability
        gc.collect()

    results = pd.DataFrame(rows)
    for algorithm, index in results.groupby("algorithm").groups.items():
        ordered = results.loc[index].set_index("feature_set")
        results.loc[index, "delta_roc_auc_vs_pb0"] = results.loc[index, "roc_auc"] - ordered.loc["PB0", "roc_auc"]
        results.loc[index, "delta_pr_auc_vs_pb0"] = results.loc[index, "pr_auc"] - ordered.loc["PB0", "pr_auc"]
        results.loc[index, "delta_log_loss_vs_pb0"] = results.loc[index, "log_loss"] - ordered.loc["PB0", "log_loss"]
    return results, pd.DataFrame(metric_rows), pd.concat(predictions, ignore_index=True)


def atomic_savefig(figure: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.stem + ".tmp" + path.suffix)
    figure.savefig(temporary, dpi=300, bbox_inches="tight")
    os.replace(temporary, path)
    plt.close(figure)


def robustness_figure(primary: pd.DataFrame, family: pd.DataFrame, path: Path) -> None:
    family = family.loc[family["threshold_source"].eq("fixed_0.5")]
    figure, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
    width = 0.18
    labels = ["Logistic\nM0", "Logistic\nM4", "CatBoost\nM0", "CatBoost\nM4"]
    for axis, population in zip(axes, ["Global", "Ming"], strict=True):
        values_primary = []
        values_family = []
        for algorithm in ["LogisticRegression", "CatBoost"]:
            for feature_set in ["M0", "M4"]:
                values_primary.append(float(primary.loc[
                    primary["algorithm"].eq(algorithm)
                    & primary["population"].eq(population)
                    & primary["feature_set"].eq(feature_set), "roc_auc"
                ].iloc[0]))
                values_family.append(float(family.loc[
                    family["algorithm"].eq(algorithm)
                    & family["population"].eq(population)
                    & family["feature_set"].eq(feature_set), "roc_auc"
                ].iloc[0]))
        x = np.arange(4)
        axis.bar(x - width / 2, values_primary, width, label="Primary", color="#4c78a8")
        axis.bar(x + width / 2, values_family, width, label="Family-aware", color="#f58518")
        axis.set_xticks(x, labels)
        axis.set_title(population)
        axis.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("ROC-AUC")
    axes[-1].legend(frameon=False)
    figure.suptitle("Frozen primary versus family-group test split")
    figure.tight_layout()
    atomic_savefig(figure, path)


def family_descriptive(dataset: pd.DataFrame, path: Path) -> pd.DataFrame:
    rows = []
    for population in ["Song", "Ming", "Qing"]:
        subset = dataset.loc[dataset["dynasty_name"].eq(population) & dataset["father_ever_entry"].notna()]
        for status, group in subset.groupby("father_ever_entry"):
            rows.append({
                "population": population,
                "father_ever_entry": int(status),
                "n_people": len(group),
                "v1_positive": int(group["target_entry_v1"].sum()),
                "v1_positive_rate": float(group["target_entry_v1"].mean()),
            })
    descriptive = pd.DataFrame(rows)
    figure, axis = plt.subplots(figsize=(7, 4.2))
    populations = ["Song", "Ming", "Qing"]
    x = np.arange(3)
    width = 0.34
    for offset, status, color in [(-width / 2, 0, "#9ecae9"), (width / 2, 1, "#de6b48")]:
        values = [float(descriptive.loc[
            descriptive["population"].eq(population)
            & descriptive["father_ever_entry"].eq(status), "v1_positive_rate"
        ].iloc[0]) for population in populations]
        axis.bar(x + offset, values, width, label=f"father_ever_entry = {status}", color=color)
    axis.set_xticks(x, populations)
    axis.set_ylabel("Focal V1 positive rate in CBDB")
    axis.set_title("Descriptive association with father's recorded ENTRY history")
    axis.legend(frameon=False)
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    atomic_savefig(figure, path)
    return descriptive


def main() -> int:
    logger = setup_logging("phase2_robustness", PROJECT_ROOT / "outputs/logs/phase2_robustness.log")
    dataset = pd.read_parquet(PROJECT_ROOT / "data/modeling/person_phase2_features.parquet")
    config = load_yaml("configs/phase2_models.yaml")
    metrics_path = PROJECT_ROOT / "outputs/phase2/tables/model_metrics.csv"
    existing = pd.read_csv(metrics_path)
    primary = primary_main_metrics(existing)

    family_metrics, family_predictions = family_split_robustness(dataset, config, logger)
    split_results = compare_family_splits(primary, family_metrics)
    largest_results = largest_component_sensitivity(dataset)
    robustness = pd.concat([split_results, largest_results], ignore_index=True, sort=False)
    atomic_to_csv(robustness, PROJECT_ROOT / "outputs/phase2/tables/robustness_results.csv")

    prebirth, prebirth_metrics, prebirth_predictions = prebirth_robustness(dataset, config, logger)
    atomic_to_csv(prebirth, PROJECT_ROOT / "outputs/phase2/tables/prebirth_lineage_results.csv")
    atomic_to_parquet(
        pd.concat([family_predictions, prebirth_predictions], ignore_index=True),
        PROJECT_ROOT / "data/modeling/phase2_predictions_robustness.parquet",
    )
    retained = existing.loc[
        ~existing["split_protocol"].eq("family")
        & ~existing["feature_set"].isin(["PB0", "PB1"])
    ]
    atomic_to_csv(
        pd.concat([retained, family_metrics, prebirth_metrics], ignore_index=True, sort=False),
        metrics_path,
    )

    figures = PROJECT_ROOT / "outputs/phase2/figures"
    robustness_figure(primary, family_metrics, figures / "figure4_primary_vs_family_split.png")
    descriptive = family_descriptive(dataset, figures / "figure5_family_descriptive.png")
    atomic_to_csv(descriptive, PROJECT_ROOT / "outputs/phase2/tables/family_descriptive_rates.csv")
    logger.info("Phase 2 robustness complete: %d comparison rows", len(robustness))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
