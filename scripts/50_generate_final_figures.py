#!/usr/bin/env python3
"""Generate publication-style Phase 2.6 PNG/SVG figures from saved tables."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.feature_builders import atomic_to_csv, load_yaml
from src.utils import setup_logging


FIGURES = PROJECT_ROOT / "outputs/phase2_6/figures"
INPUTS = PROJECT_ROOT / "outputs/phase2_6/tables/figure_inputs"
POPULATIONS = ["Global", "Song", "Ming"]
COLOURS = ["#4c78a8", "#f58518", "#54a24b", "#e45756", "#72b7b2", "#b279a2", "#ff9da6"]


def save_both(figure: plt.Figure, name: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    for suffix in ["png", "svg"]:
        path = FIGURES / f"{name}.{suffix}"
        temporary = path.with_name(path.stem + ".tmp" + path.suffix)
        figure.savefig(temporary, dpi=300, bbox_inches="tight")
        os.replace(temporary, path)
    plt.close(figure)


def save_input(name: str, frame: pd.DataFrame) -> None:
    atomic_to_csv(frame, INPUTS / f"{name}.csv")


def grouped_lines(frame: pd.DataFrame, comparison_column: str, value: str, title: str, ylabel: str, name: str) -> None:
    save_input(name, frame)
    labels = list(dict.fromkeys(frame[comparison_column]))
    figure, axis = plt.subplots(figsize=(10, 5.5))
    for population, color in zip(POPULATIONS, COLOURS[:3], strict=True):
        block = frame.loc[frame["population"].eq(population)].set_index(comparison_column).reindex(labels)
        axis.plot(labels, block[value], marker="o", label=population, color=color, linewidth=2)
    axis.axhline(0, color="black", linewidth=0.8)
    axis.set_ylabel(ylabel)
    axis.set_xlabel("Staged comparison")
    axis.set_title(title)
    axis.tick_params(axis="x", rotation=30)
    axis.legend(frameon=False)
    axis.grid(axis="y", alpha=0.2)
    figure.tight_layout()
    save_both(figure, name)


def main() -> int:
    logger = setup_logging("phase2_6_figures", PROJECT_ROOT / "outputs/phase2_6/logs/final_figures.log")
    reporting = load_yaml("configs/phase2_6_reporting.yaml")
    major = [str(value) for value in reporting["major_dynasties"]]
    tables = PROJECT_ROOT / "outputs/phase2_6/tables"
    INPUTS.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 9, "axes.titlesize": 11, "axes.labelsize": 10})

    context = pd.read_csv(tables / "final_population_target_context.csv")
    context = context.loc[context["dynasty_name"].isin(major)].set_index("dynasty_name").reindex(major).reset_index()
    save_input("final_population_and_target_context", context)
    figure, axis = plt.subplots(figsize=(9, 5.4))
    axis.bar(context["dynasty_name"], context["n_people"], color="#9ecae9", label="CBDB-listed people")
    axis.set_ylabel("CBDB-listed people")
    axis.set_xlabel("Dynasty")
    rate_axis = axis.twinx()
    rate_axis.plot(context["dynasty_name"], context["entry_record_presence_rate"], color="#d62728", marker="o", linewidth=2, label="ENTRY record presence")
    rate_axis.set_ylabel("Share with an ENTRY_DATA record")
    axis.set_title("Population and target context in CBDB (not historical population rates)")
    figure.tight_layout()
    save_both(figure, "final_population_and_target_context")

    pathways = pd.read_csv(tables / "entry_category_by_dynasty_records.csv")
    save_input("final_entry_pathways_by_dynasty", pathways)
    pivot = pathways.pivot(index="dynasty", columns="semantic_category", values="record_category_share").reindex(major).fillna(0)
    figure, axis = plt.subplots(figsize=(11, 6))
    bottom = np.zeros(len(pivot))
    for index, column in enumerate(pivot.columns):
        axis.bar(pivot.index, pivot[column], bottom=bottom, label=column.replace("_", " "), color=plt.cm.tab20(index / max(len(pivot.columns) - 1, 1)))
        bottom += pivot[column].to_numpy()
    axis.set_ylim(0, 1)
    axis.set_ylabel("Share of ENTRY_DATA records")
    axis.set_xlabel("Dynasty")
    axis.set_title("Recorded ENTRY pathway composition by dynasty")
    axis.legend(bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False, fontsize=7)
    figure.tight_layout()
    save_both(figure, "final_entry_pathways_by_dynasty")
    for suffix in ["png", "svg"]:
        shutil.copy2(FIGURES / f"final_entry_pathways_by_dynasty.{suffix}", FIGURES / f"entry_pathway_composition_by_dynasty.{suffix}")

    gender = pd.read_csv(tables / "final_gender_entry_rates.csv")
    save_input("final_gender_entry_rate", gender)
    pivot = gender.pivot(index="population", columns="gender", values="entry_record_presence_rate").reindex(["Global", "Song", "Ming", "Qing"])
    figure, axis = plt.subplots(figsize=(9, 5.5))
    x = np.arange(len(pivot)); width = 0.24
    for index, column in enumerate([value for value in ["female", "male", "unknown"] if value in pivot]):
        axis.bar(x + (index - 1) * width, pivot[column], width, label=column.title(), color=COLOURS[index])
    axis.set_xticks(x, pivot.index)
    axis.set_ylabel("Share with an ENTRY_DATA record")
    axis.set_xlabel("Population")
    axis.set_title("Gender composition of ENTRY record presence among CBDB-listed people")
    axis.legend(frameon=False)
    axis.grid(axis="y", alpha=0.2)
    figure.tight_layout()
    save_both(figure, "final_gender_entry_rate")

    birth = pd.read_csv(tables / "birth_missingness_deltas.csv")
    grouped_lines(
        birth, "comparison", "delta_roc_auc", "SAFE-birth value and missingness decomposition",
        "Change in ROC-AUC", "final_birth_missingness_decomposition",
    )

    address = pd.read_csv(tables / "address_semantics_deltas.csv")
    address = address.loc[~address["comparison"].str.contains("A6")]
    grouped_lines(
        address, "comparison", "delta_roc_auc", "Address observability, location, and record semantics",
        "Change in ROC-AUC", "final_address_semantics_decomposition",
    )

    family = pd.read_csv(PROJECT_ROOT / "outputs/phase2_5/tables/family_decomposition_deltas.csv")
    family = family.loc[family["algorithm"].eq("CatBoost")][["population", "comparison", "delta_roc_auc", "delta_pr_auc"]]
    grouped_lines(
        family, "comparison", "delta_roc_auc", "Family observability, topology, and recorded capital",
        "Change in ROC-AUC", "final_family_signal_decomposition",
    )

    locked = pd.read_csv(tables / "final_model_metrics.csv")
    d0 = pd.read_csv(PROJECT_ROOT / "outputs/phase2_5/tables/documentation_controlled_ablation.csv")
    d0 = d0.loc[d0["algorithm"].eq("CatBoost") & d0["model_id"].eq("D0"), ["population", "model_id", "roc_auc", "pr_auc"]]
    doc_plot = pd.concat([d0, locked[["population", "model_id", "roc_auc", "pr_auc"]]], ignore_index=True)
    save_input("final_documentation_controlled_models", doc_plot)
    order = ["D0", "H_STRUCT", "D5_MAIN", "D6_UPPER"]
    figure, axes = plt.subplots(1, 3, figsize=(12, 4.6), sharey=True)
    for axis, population in zip(axes, POPULATIONS, strict=True):
        block = doc_plot.loc[doc_plot["population"].eq(population)].set_index("model_id").reindex(order)
        axis.bar(order, block["roc_auc"], color=COLOURS[:4])
        axis.set_title(population)
        axis.set_xlabel("Model meaning")
        axis.tick_params(axis="x", rotation=30)
        axis.set_ylim(max(0.5, float(block["roc_auc"].min()) - 0.05), 1)
        axis.grid(axis="y", alpha=0.2)
    axes[0].set_ylabel("ROC-AUC")
    figure.suptitle("Documentation-only, structural, main predictive, and upper-bound models")
    figure.tight_layout()
    save_both(figure, "final_documentation_controlled_models")

    multiseed = pd.read_csv(tables / "multiseed_model_metrics.csv")
    stability = multiseed.groupby(["population", "model_id"], as_index=False).agg(mean_roc_auc=("roc_auc", "mean"), std_roc_auc=("roc_auc", "std"))
    save_input("final_multiseed_stability", stability)
    model_order = ["F2", "F3", "F4", "D5", "D6", "D6i", "H_STRUCT"]
    figure, axes = plt.subplots(1, 3, figsize=(14, 4.8), sharey=False)
    for axis, population in zip(axes, POPULATIONS, strict=True):
        block = stability.loc[stability["population"].eq(population)].set_index("model_id").reindex(model_order)
        axis.errorbar(model_order, block["mean_roc_auc"], yerr=block["std_roc_auc"], marker="o", capsize=3, color="#4c78a8")
        axis.set_title(population)
        axis.set_xlabel("Fixed model")
        axis.tick_params(axis="x", rotation=35)
        axis.set_ylabel("Five-seed ROC-AUC mean ± SD")
        axis.grid(axis="y", alpha=0.2)
    figure.suptitle("Fixed-configuration multi-seed stability")
    figure.tight_layout()
    save_both(figure, "final_multiseed_stability")

    matched = pd.read_csv(tables / "matched_random_vs_spatial_results.csv")
    save_input("final_random_vs_spatial_matched_support", matched)
    figure, axes = plt.subplots(1, 3, figsize=(12, 4.7), sharey=False)
    for axis, population in zip(axes, POPULATIONS, strict=True):
        block = matched.loc[matched["population"].eq(population)].set_index("model_id").reindex(["H_STRUCT", "D5_MAIN"])
        x = np.arange(len(block)); width = 0.34
        axis.bar(x - width / 2, block["matched_random_roc_auc"], width, label="Matched random", color="#4c78a8")
        axis.bar(x + width / 2, block["matched_spatial_roc_auc"], width, label="Matched spatial", color="#f58518")
        axis.set_xticks(x, block.index, rotation=25)
        axis.set_title(population)
        axis.set_xlabel("Locked definition")
        axis.set_ylabel("ROC-AUC")
        axis.set_ylim(max(0.5, min(block["matched_spatial_roc_auc"].min(), block["matched_random_roc_auc"].min()) - 0.08), 1)
        axis.grid(axis="y", alpha=0.2)
    axes[0].legend(frameon=False)
    figure.suptitle("Matched-support spatial distribution-shift sensitivity")
    figure.tight_layout()
    save_both(figure, "final_random_vs_spatial_matched_support")

    save_input("final_locked_model_performance", locked)
    figure, axes = plt.subplots(1, 3, figsize=(12, 4.8), sharey=False)
    for axis, population in zip(axes, POPULATIONS, strict=True):
        block = locked.loc[locked["population"].eq(population)].set_index("model_id").reindex(["H_STRUCT", "D5_MAIN", "D6_UPPER"])
        x = np.arange(len(block)); width = 0.34
        axis.bar(x - width / 2, block["roc_auc"], width, label="ROC-AUC", color="#4c78a8")
        axis.bar(x + width / 2, block["pr_auc"], width, label="PR-AUC", color="#54a24b")
        axis.set_xticks(x, block.index, rotation=25)
        axis.set_title(population)
        axis.set_xlabel("Canonical seed-42 model")
        axis.set_ylabel("Test metric")
        axis.grid(axis="y", alpha=0.2)
    axes[0].legend(frameon=False)
    figure.suptitle("Locked model discrimination on the frozen primary test set")
    figure.tight_layout()
    save_both(figure, "final_locked_model_performance")

    shap = pd.read_csv(PROJECT_ROOT / "outputs/phase2_6/shap/shap_group_summary.csv")
    for population in POPULATIONS:
        block = shap.loc[shap["population"].eq(population)]
        name = f"final_shap_group_comparison_{population.lower()}"
        save_input(name, block)
        pivot = block.pivot(index="model_id", columns="feature_group", values="group_share_of_total_abs_shap").fillna(0).reindex(["H_STRUCT", "D5_MAIN", "D6_UPPER"])
        figure, axis = plt.subplots(figsize=(10.5, 5.4))
        bottom = np.zeros(len(pivot))
        for index, column in enumerate(pivot.columns):
            axis.bar(pivot.index, pivot[column], bottom=bottom, label=column.replace("_", " "), color=plt.cm.tab20(index / max(len(pivot.columns) - 1, 1)))
            bottom += pivot[column].to_numpy()
        axis.set_ylim(0, 1)
        axis.set_ylabel("Share of total mean absolute SHAP")
        axis.set_xlabel("Locked model")
        axis.set_title(f"{population}: grouped prediction attribution (not causal effects)")
        axis.legend(bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False, fontsize=7)
        figure.tight_layout()
        save_both(figure, name)

    calibration = pd.read_csv(tables / "final_model_calibration.csv")
    save_input("final_calibration_summary", calibration)
    figure, axes = plt.subplots(1, 3, figsize=(12, 4.7), sharey=True)
    for axis, population in zip(axes, POPULATIONS, strict=True):
        block = calibration.loc[calibration["population"].eq(population)].set_index("model_id").reindex(["H_STRUCT", "D5_MAIN", "D6_UPPER"])
        x = np.arange(len(block)); width = 0.34
        axis.bar(x - width / 2, block["raw_ece"], width, label="Raw", color="#e45756")
        axis.bar(x + width / 2, block["calibrated_ece"], width, label="Validation-fitted sigmoid", color="#72b7b2")
        axis.set_xticks(x, block.index, rotation=25)
        axis.set_title(population)
        axis.set_xlabel("Canonical model")
        axis.grid(axis="y", alpha=0.2)
    axes[0].set_ylabel("Expected calibration error")
    axes[0].legend(frameon=False, fontsize=8)
    figure.suptitle("Raw and validation-fitted diagnostic calibration")
    figure.tight_layout()
    save_both(figure, "final_calibration_summary")

    required = [
        "final_population_and_target_context", "final_entry_pathways_by_dynasty", "final_gender_entry_rate",
        "final_birth_missingness_decomposition", "final_address_semantics_decomposition",
        "final_family_signal_decomposition", "final_documentation_controlled_models",
        "final_multiseed_stability", "final_random_vs_spatial_matched_support",
        "final_locked_model_performance", "final_shap_group_comparison_global",
        "final_shap_group_comparison_song", "final_shap_group_comparison_ming", "final_calibration_summary",
    ]
    for name in required:
        for suffix in ["png", "svg"]:
            path = FIGURES / f"{name}.{suffix}"
            if not path.exists() or path.stat().st_size == 0:
                raise RuntimeError(f"Missing final figure: {path}")
        if not (INPUTS / f"{name}.csv").exists():
            raise RuntimeError(f"Missing final figure input: {name}")
    logger.info("Generated %d final figures in PNG and SVG with source CSVs", len(required))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
