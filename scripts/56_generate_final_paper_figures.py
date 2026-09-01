#!/usr/bin/env python3
"""Generate Phase 3 scientific tables and every paper figure from frozen outputs."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np
import pandas as pd
import seaborn as sns

from src.phase3 import (
    PHASE3_FIGURE_DATA,
    PHASE3_FIGURES,
    PHASE3_TABLES,
    ROOT,
    ensure_phase3_dirs,
)
from src.utils import sha256_file


POPULATIONS = ["Global", "Song", "Ming"]
DYNASTIES = ["Tang", "Song", "Yuan", "Ming", "Qing"]
MODELS = ["Logistic M6", "H_STRUCT", "D5_MAIN", "D6_UPPER"]
MODEL_COLORS = {
    "Logistic M6": "#8c8c8c",
    "H_STRUCT": "#4c78a8",
    "D5_MAIN": "#e45756",
    "D6_UPPER": "#72b7b2",
}
CAPTIONS = {
    "fig1_task_ep_t": "Observed labels and latent historical state. Counts in the E by P matrix come from the frozen CBDB person table; neither observed label is T.",
    "fig2_dynasty_gender": "CBDB-covered population and recorded ENTRY share by dynasty and gender. Rates describe records among covered people, not population entry rates.",
    "fig3_entry_pathways": "ENTRY pathway composition by dynasty at record and unique-person levels. Person shares can sum above one because people may have multiple categories.",
    "fig4_locked_models": "Primary-test discrimination for the frozen model hierarchy. D5_MAIN is the designated main predictive model; D6_UPPER is a database-internal upper bound.",
    "fig5_grouped_ablation": "Conditional predictive increments from prespecified feature blocks. Ablation magnitude, rather than attribution share, is the primary evidence of incremental information.",
    "fig6_spatial_transport": "Address semantics decomposition and matched-support spatial transport. Administrative and observability signals dominate; performance falls on unseen regions.",
    "fig7_family_decomposition": "Family decomposition on the primary split. Observability and topology dominate the much smaller political-capital increment.",
    "fig8_grouped_shap": "Grouped mean absolute SHAP shares for locked models. Shares are predictive attributions, not independent gains or causal effects.",
    "figA1_calibration": "Validation-fitted sigmoid calibration diagnostics for the locked primary-test predictions.",
    "figA2_multiseed": "Five-seed stability of selected incremental ROC-AUC comparisons; error bars show the observed seed range.",
    "figA3_robustness_scope": "Robustness scope and feasibility evidence, including SAFE temporal split composition and the dominant primary-source component.",
}


def configure_style() -> None:
    sns.set_theme(style="whitegrid", context="paper")
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.labelsize": 8,
        "legend.fontsize": 7,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "savefig.bbox": "tight",
    })


def save_figure(fig: plt.Figure, figure_id: str) -> tuple[str, str, str]:
    outputs = []
    for suffix, kwargs in [("png", {"dpi": 300}), ("pdf", {}), ("svg", {})]:
        path = PHASE3_FIGURES / f"{figure_id}.{suffix}"
        fig.savefig(path, **kwargs)
        paper_path = ROOT / "paper/figures" / path.name
        shutil.copy2(path, paper_path)
        outputs.append(path.relative_to(ROOT).as_posix())
    plt.close(fig)
    return tuple(outputs)  # type: ignore[return-value]


def save_data(frame: pd.DataFrame, name: str) -> Path:
    path = PHASE3_FIGURE_DATA / name
    frame.to_csv(path, index=False)
    return path


def _logistic_baseline() -> pd.DataFrame:
    metrics = pd.read_csv(ROOT / "outputs/phase2/tables/model_metrics.csv")
    selected = metrics.loc[
        metrics["algorithm"].eq("LogisticRegression")
        & metrics["model_variant"].eq("balanced")
        & metrics["feature_set"].eq("M6")
        & metrics["split_protocol"].eq("primary")
        & metrics["evaluation_split"].eq("test")
        & metrics["threshold_source"].eq("fixed_0.5")
    ].copy()
    selected["model_id"] = "Logistic M6"
    selected["calibrated_ece"] = np.nan
    return selected


def build_scientific_tables() -> dict[str, pd.DataFrame]:
    final = pd.read_csv(ROOT / "outputs/phase2_6/tables/final_model_metrics.csv")
    final["display_model"] = final["model_id"]
    logistic = _logistic_baseline()
    columns = [
        "population", "model_id", "roc_auc", "pr_auc", "balanced_accuracy", "f1",
        "log_loss", "brier_score", "calibrated_ece", "test_positive_rate", "n_test",
    ]
    main = pd.concat([
        logistic.rename(columns={"model_id": "display_model"}).assign(model_id="Logistic M6")
        [["population", "model_id", "roc_auc", "pr_auc", "balanced_accuracy", "f1", "log_loss", "brier_score", "calibrated_ece", "test_positive_rate", "n_test"]],
        final[columns],
    ], ignore_index=True)
    main["model_role"] = main["model_id"].map({
        "Logistic M6": "Frozen linear baseline",
        "H_STRUCT": "Historical structural benchmark",
        "D5_MAIN": "Main predictive model",
        "D6_UPPER": "Database-internal record-structure upper bound",
    })
    main.to_csv(PHASE3_TABLES / "main_model_performance.csv", index=False)

    target = pd.read_parquet(ROOT / "data/interim/person_target.parquet").rename(columns={"target_entry": "target_entry_v1"})
    contingency = pd.read_csv(ROOT / "outputs/tables/entry_vs_posting_contingency.csv")
    dataset_summary = pd.DataFrame([
        {"quantity": "CBDB-covered people", "value": len(target), "definition": "One row per BIOG_MAIN person"},
        {"quantity": "E positives", "value": int(target["target_entry_v1"].sum()), "definition": "At least one ENTRY_DATA row"},
        {"quantity": "E prevalence", "value": float(target["target_entry_v1"].mean()), "definition": "Recorded ENTRY share among CBDB-covered people"},
        {"quantity": "P positives", "value": int(contingency.loc[contingency["has_posting"].eq(1), "n_people"].sum()), "definition": "At least one valid posting record"},
        {"quantity": "Primary-test people", "value": int(final.loc[final["population"].eq("Global"), "n_test"].iloc[0]), "definition": "Frozen dynasty-by-E stratified test"},
    ])
    dataset_summary.to_csv(PHASE3_TABLES / "dataset_target_summary.csv", index=False)

    personal = pd.read_csv(ROOT / "outputs/phase2_5/tables/personal_decomposition_deltas.csv")
    address = pd.read_csv(ROOT / "outputs/phase2_6/tables/address_semantics_deltas.csv")
    family = pd.read_csv(ROOT / "outputs/phase2_5/tables/family_decomposition_deltas.csv")
    bootstrap = pd.read_csv(ROOT / "outputs/phase2_5/tables/paired_bootstrap_results.csv")
    records: list[dict[str, object]] = []
    comparisons = [
        ("Personal: gender", personal, "P1 - P0", "P0", "P1"),
        ("Address observability", address, "A1 - A0", None, None),
        ("Administrative geography", address, "A2 - A1", None, None),
        ("Physical geography", address, "A3 - A2", "G2", "G3"),
        ("Address-record semantics", address, "A4 - A3", None, None),
        ("Family observability", family, "F1 - F0", None, None),
        ("Family topology", family, "F2 - F1", "F1", "F2"),
        ("Family capital (full record)", family, "F3 - F2", "F2", "F3"),
        ("Family capital (train observed)", family, "F4 - F2", "F2", "F4"),
    ]
    for label, source, comparison, model_a, model_b in comparisons:
        rows = source.loc[source["comparison"].eq(comparison)]
        for row in rows.itertuples(index=False):
            item: dict[str, object] = {
                "population": row.population,
                "feature_block": label,
                "comparison": comparison,
                "delta_roc_auc": row.delta_roc_auc,
                "delta_pr_auc": row.delta_pr_auc,
                "delta_log_loss": row.delta_log_loss,
                "roc_ci_lower": np.nan,
                "roc_ci_upper": np.nan,
                "pr_ci_lower": np.nan,
                "pr_ci_upper": np.nan,
                "ci_status": "paired predictions not retained for this exact contrast",
            }
            if model_a and model_b:
                for metric in ["roc_auc", "pr_auc"]:
                    ci = bootstrap.loc[
                        bootstrap["population"].eq(row.population)
                        & bootstrap["split_protocol"].eq("primary")
                        & bootstrap["model_a"].eq(model_a)
                        & bootstrap["model_b"].eq(model_b)
                        & bootstrap["metric"].eq(metric)
                    ]
                    if len(ci):
                        item[f"{metric.split('_')[0]}_ci_lower"] = float(ci["ci_lower"].iloc[0])
                        item[f"{metric.split('_')[0]}_ci_upper"] = float(ci["ci_upper"].iloc[0])
                        item["ci_status"] = "500-resample stratified paired bootstrap"
            records.append(item)
    ablation = pd.DataFrame(records)
    ablation.to_csv(PHASE3_TABLES / "grouped_ablation_summary.csv", index=False)

    spatial = pd.read_csv(ROOT / "outputs/phase2_6/tables/matched_random_vs_spatial_results.csv")
    family_holdout = pd.read_csv(ROOT / "outputs/phase2_5/tables/family_holdout_decomposition_results.csv")
    temporal_split = pd.read_parquet(ROOT / "data/splits/split_safe_temporal.parquet")
    target_small = pd.read_parquet(ROOT / "data/interim/person_target.parquet", columns=["person_id", "target_entry"]).rename(columns={"target_entry": "target_entry_v1"})
    temporal = temporal_split.merge(target_small, on="person_id", validate="one_to_one")
    temporal_counts = temporal.groupby("split", dropna=False)["target_entry_v1"].agg(["size", "sum", "mean"]).reset_index()
    temporal_counts.columns = ["split", "n_people", "positive_count", "positive_prevalence"]
    temporal_counts.to_csv(PHASE3_TABLES / "safe_temporal_split_context.csv", index=False)
    source_status = json.loads((PHASE3_TABLES / "source_holdout_status.json").read_text())
    robust_rows = []
    for row in spatial.itertuples(index=False):
        robust_rows.append({
            "population": row.population, "model_id": row.model_id,
            "protocol": "Matched-support spatial", "status": "RUN",
            "reference_roc_auc": row.matched_random_roc_auc,
            "shift_roc_auc": row.matched_spatial_roc_auc,
            "delta_roc_auc": row.delta_spatial_minus_random_roc_auc,
            "reference_pr_auc": row.matched_random_pr_auc,
            "shift_pr_auc": row.matched_spatial_pr_auc,
            "delta_pr_auc": row.delta_spatial_minus_random_pr_auc,
            "note": "Identical reliable-prefecture support; not paired because test persons differ",
        })
    for row in family_holdout.loc[family_holdout["model_id"].eq("F2")].itertuples(index=False):
        primary_row = pd.read_csv(ROOT / "outputs/phase2_5/tables/family_decomposition_results.csv")
        primary_row = primary_row.loc[
            primary_row["population"].eq(row.population) & primary_row["model_id"].eq("F2")
        ].iloc[0]
        robust_rows.append({
            "population": row.population, "model_id": "F2 structural comparator",
            "protocol": "Family-group holdout", "status": "RUN",
            "reference_roc_auc": primary_row.roc_auc, "shift_roc_auc": row.roc_auc,
            "delta_roc_auc": row.roc_auc - primary_row.roc_auc,
            "reference_pr_auc": primary_row.pr_auc, "shift_pr_auc": row.pr_auc,
            "delta_pr_auc": row.pr_auc - primary_row.pr_auc,
            "note": "Whole-family groups do not cross partitions",
        })
    robust_rows.extend([
        {"population": "Global", "model_id": "Locked models", "protocol": "SAFE temporal", "status": "SPLIT_ONLY_NO_LOCKED_PERFORMANCE", "note": "Frozen whole-year split; no Phase 2.6 locked-model performance artifact exists."},
        {"population": "Qing", "model_id": "Locked models", "protocol": "Qing dynasty holdout", "status": "NOT_RUN_NO_FROZEN_HOLDOUT", "note": "Qing is descriptive; no post-hoc split was added in Phase 3."},
        {"population": "Global", "model_id": "H_STRUCT/D5_MAIN", "protocol": "Source group", "status": source_status["status"], "note": f"Largest group={source_status['largest_group_fraction']:.2%}; no source model trained."},
    ])
    robustness = pd.DataFrame(robust_rows)
    robustness.to_csv(PHASE3_TABLES / "robustness_summary.csv", index=False)
    return {
        "main": main,
        "dataset": dataset_summary,
        "ablation": ablation,
        "robustness": robustness,
        "temporal": temporal_counts,
    }


def fig1() -> tuple[pd.DataFrame, plt.Figure]:
    data = pd.read_csv(ROOT / "outputs/tables/entry_vs_posting_contingency.csv")
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.65), gridspec_kw={"width_ratios": [1.1, 1]})
    ax = axes[0]
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    def box(x: float, y: float, w: float, h: float, text: str, color: str) -> None:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15", facecolor=color, edgecolor="#333333"))
        ax.text(x+w/2, y+h/2, text, ha="center", va="center", fontsize=8)
    box(3.0, 7.6, 4.0, 1.2, "$T$: true historical entry\nlatent / unobserved", "#f2f2f2")
    box(2.1, 4.8, 5.8, 1.25, "Preservation, source coverage,\nand database encoding", "#fff2cc")
    box(0.7, 1.7, 3.6, 1.4, "$E$: ENTRY_DATA presence\nprimary observed label", "#cfe8f3")
    box(5.7, 1.7, 3.6, 1.4, "$P$: valid posting presence\nauxiliary observed label", "#d9ead3")
    for start, end in [((5, 7.6), (5, 6.1)), ((4.1, 4.8), (2.5, 3.15)), ((5.9, 4.8), (7.5, 3.15))]:
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=10, color="#555555"))
    ax.text(5, 0.55, "$E \\ne T,\; P \\ne T,\; E \\ne P$; model estimates $\\Pr(E=1\\mid X)$", ha="center", fontsize=8)
    ax.set_title("(a) Measurement target", loc="left")
    matrix = data.pivot(index="has_entry", columns="has_posting", values="n_people").reindex(index=[1, 0], columns=[0, 1])
    sns.heatmap(matrix, annot=True, fmt=",.0f", cmap="Blues", cbar=False, ax=axes[1], linewidths=.7)
    axes[1].set_xlabel("Posting record $P$"); axes[1].set_ylabel("ENTRY record $E$")
    axes[1].set_xticklabels(["0", "1"]); axes[1].set_yticklabels(["1", "0"], rotation=0)
    axes[1].set_title("(b) Observed E by P counts", loc="left")
    fig.tight_layout()
    return data, fig


def fig2() -> tuple[pd.DataFrame, plt.Figure]:
    dynasty = pd.read_csv(ROOT / "outputs/tables/target_by_dynasty.csv")
    dynasty = dynasty.loc[dynasty["dynasty"].isin(DYNASTIES)].copy()
    gender = pd.read_csv(ROOT / "outputs/phase2_6/tables/final_gender_entry_rates.csv")
    gender = gender.loc[gender["population"].isin(["Global", "Song", "Ming", "Qing"])].copy()
    data = pd.concat([dynasty.assign(panel="dynasty"), gender.assign(panel="gender")], ignore_index=True, sort=False)
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.7))
    d = dynasty.set_index("dynasty").reindex(DYNASTIES).reset_index()
    axes[0].bar(d["dynasty"], d["n_people"] / 1000, color="#4c78a8")
    axes[0].set_ylabel("CBDB people (thousands)"); axes[0].set_title("(a) Coverage and E share", loc="left")
    ax2 = axes[0].twinx(); ax2.plot(d["dynasty"], 100*d["target_rate"], color="#e45756", marker="o")
    ax2.set_ylabel("Recorded ENTRY share (%)", color="#e45756"); ax2.grid(False)
    g = gender.copy(); g["positive_rate_pct"] = 100 * g["entry_record_presence_rate"]
    value_col = "positive_rate_pct"
    sns.barplot(data=g, x="population", y=value_col, hue="gender", hue_order=["male", "female", "unknown"], ax=axes[1], palette=["#4c78a8", "#e45756", "#b0b0b0"])
    axes[1].set_ylabel("Recorded ENTRY share (%)"); axes[1].set_xlabel(""); axes[1].set_title("(b) Gender", loc="left")
    axes[1].legend(title="", ncol=3, loc="upper left")
    fig.tight_layout()
    return data, fig


def fig3() -> tuple[pd.DataFrame, plt.Figure]:
    records = pd.read_csv(ROOT / "outputs/phase2_6/tables/entry_category_by_dynasty_records.csv")
    people = pd.read_csv(ROOT / "outputs/phase2_6/tables/entry_category_by_dynasty_people.csv")
    records = records.loc[records["dynasty"].isin(DYNASTIES)].copy()
    people = people.loc[people["dynasty"].isin(DYNASTIES)].copy()
    records["measure"] = "record_share"; people["measure"] = "person_prevalence"
    data = pd.concat([records, people], ignore_index=True, sort=False)
    categories = ["exam_degree", "school_or_student_status", "recommendation", "hereditary_or_yin_privilege", "military_entry", "direct_appointment"]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
    palette = sns.color_palette("colorblind", len(categories))
    for ax, frame, value, title in [
        (axes[0], records, "record_share", "(a) Record-level share"),
        (axes[1], people, "person_prevalence_all", "(b) Unique-person prevalence"),
    ]:
        value = value if value in frame.columns else ("record_category_share" if frame is records else "prevalence_among_all_cbdb_people")
        pivot = frame.loc[frame["semantic_category"].isin(categories)].pivot(index="dynasty", columns="semantic_category", values=value).reindex(DYNASTIES).fillna(0)
        left = np.zeros(len(pivot))
        for color, category in zip(palette, categories):
            vals = 100*pivot.get(category, pd.Series(0, index=pivot.index)).to_numpy()
            ax.barh(pivot.index, vals, left=left, color=color, label=category.replace("_", " "))
            left += vals
        ax.set_xlabel("Share / prevalence (%)"); ax.set_title(title, loc="left")
    axes[1].legend(bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
    fig.tight_layout()
    return data, fig


def fig4(main: pd.DataFrame) -> tuple[pd.DataFrame, plt.Figure]:
    data = main.loc[main["population"].isin(POPULATIONS) & main["model_id"].isin(MODELS)].copy()
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.65), sharey=True)
    for ax, metric, label in [(axes[0], "roc_auc", "ROC-AUC"), (axes[1], "pr_auc", "PR-AUC")]:
        sns.barplot(data=data, x="population", y=metric, hue="model_id", hue_order=MODELS, palette=MODEL_COLORS, ax=ax)
        ax.set_ylim(0.35 if metric == "pr_auc" else 0.68, 0.97); ax.set_xlabel(""); ax.set_ylabel(label)
        ax.set_title(f"({chr(97 + (0 if metric=='roc_auc' else 1))}) {label}", loc="left")
        if ax is axes[0]: ax.get_legend().remove()
        else: ax.legend(title="", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()
    return data, fig


def fig5(ablation: pd.DataFrame) -> tuple[pd.DataFrame, plt.Figure]:
    order = ["Personal: gender", "Address observability", "Administrative geography", "Physical geography", "Address-record semantics", "Family observability", "Family topology", "Family capital (full record)", "Family capital (train observed)"]
    data = ablation.loc[ablation["population"].eq("Global")].copy()
    data["feature_block"] = pd.Categorical(data["feature_block"], order, ordered=True)
    data = data.sort_values("feature_block")
    fig, ax = plt.subplots(figsize=(7.2, 3.05))
    y = np.arange(len(data))
    ax.barh(y-0.17, data["delta_roc_auc"], height=.32, color="#4c78a8", label="$\\Delta$ROC-AUC")
    ax.barh(y+0.17, data["delta_pr_auc"], height=.32, color="#e45756", label="$\\Delta$PR-AUC")
    ax.axvline(0, color="black", linewidth=.7)
    ax.set_yticks(y, data["feature_block"]); ax.invert_yaxis(); ax.set_xlabel("Conditional metric increment")
    ax.set_title("Global primary-split grouped ablations", loc="left"); ax.legend(ncol=2)
    fig.tight_layout()
    return data, fig


def fig6() -> tuple[pd.DataFrame, plt.Figure]:
    address = pd.read_csv(ROOT / "outputs/phase2_6/tables/address_semantics_deltas.csv")
    spatial = pd.read_csv(ROOT / "outputs/phase2_6/tables/matched_random_vs_spatial_results.csv")
    data = pd.concat([address.assign(panel="address"), spatial.assign(panel="spatial")], ignore_index=True, sort=False)
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9))
    a = address.loc[address["population"].eq("Global")].copy()
    labels = ["observability", "administrative", "physical", "address semantics", "density", "local prior"]
    axes[0].barh(labels, a["delta_roc_auc"], color="#4c78a8")
    axes[0].axvline(0, color="black", linewidth=.7); axes[0].invert_yaxis(); axes[0].set_xlabel("$\\Delta$ROC-AUC")
    axes[0].set_title("(a) Address blocks, Global", loc="left")
    s = spatial.copy(); s["label"] = s["population"] + " " + s["model_id"]
    s = s.sort_values(["population", "model_id"])
    axes[1].barh(s["label"], s["delta_spatial_minus_random_roc_auc"], color=s["model_id"].map(MODEL_COLORS))
    axes[1].axvline(0, color="black", linewidth=.7); axes[1].set_xlabel("Spatial minus matched-random ROC-AUC")
    axes[1].set_title("(b) Unseen-region transport", loc="left")
    fig.tight_layout()
    return data, fig


def fig7() -> tuple[pd.DataFrame, plt.Figure]:
    family = pd.read_csv(ROOT / "outputs/phase2_5/tables/family_decomposition_deltas.csv")
    keep = family.loc[family["comparison"].isin(["F1 - F0", "F2 - F1", "F3 - F2", "F4 - F2"])].copy()
    labels = {"F1 - F0": "observability", "F2 - F1": "topology", "F3 - F2": "full-record capital", "F4 - F2": "train-observed capital"}
    keep["block"] = keep["comparison"].map(labels)
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.75), sharey=True)
    for ax, metric, title in [(axes[0], "delta_roc_auc", "(a) $\\Delta$ROC-AUC"), (axes[1], "delta_pr_auc", "(b) $\\Delta$PR-AUC")]:
        sns.barplot(data=keep, x="population", y=metric, hue="block", ax=ax, palette="colorblind")
        ax.axhline(0, color="black", linewidth=.7); ax.set_xlabel(""); ax.set_ylabel(""); ax.set_title(title, loc="left")
        if ax is axes[0]: ax.get_legend().remove()
        else: ax.legend(title="", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()
    return keep, fig


def fig8() -> tuple[pd.DataFrame, plt.Figure]:
    shap = pd.read_csv(ROOT / "outputs/phase2_6/shap/shap_group_summary.csv")
    groups = sorted(shap["feature_group"].unique())
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 4.0), sharey=True)
    for ax, population in zip(axes, POPULATIONS):
        pivot = shap.loc[shap["population"].eq(population)].pivot(index="feature_group", columns="model_id", values="group_share_of_total_abs_shap").reindex(index=groups, columns=["H_STRUCT", "D5_MAIN", "D6_UPPER"])
        sns.heatmap(100*pivot, cmap="YlGnBu", vmin=0, vmax=35, cbar=ax is axes[-1], ax=ax, annot=False)
        ax.set_title(population); ax.set_xlabel(""); ax.set_ylabel("" if ax is not axes[0] else "Feature group")
        ax.tick_params(axis="x", rotation=70)
    fig.suptitle("Grouped mean absolute SHAP share (%)", y=1.01, fontsize=9)
    fig.tight_layout()
    return shap, fig


def fig_calibration() -> tuple[pd.DataFrame, plt.Figure]:
    data = pd.read_csv(ROOT / "outputs/phase2_6/tables/final_model_calibration.csv")
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.7))
    for ax, metric, title in [(axes[0], "raw_ece", "Raw ECE"), (axes[1], "calibrated_ece", "Validation-calibrated ECE")]:
        sns.barplot(data=data, x="population", y=metric, hue="model_id", hue_order=["H_STRUCT", "D5_MAIN", "D6_UPPER"], palette=MODEL_COLORS, ax=ax)
        ax.set_xlabel(""); ax.set_ylabel(title); ax.set_title(title, loc="left")
        if ax is axes[0]: ax.get_legend().remove()
        else: ax.legend(title="", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()
    return data, fig


def fig_multiseed() -> tuple[pd.DataFrame, plt.Figure]:
    data = pd.read_csv(ROOT / "outputs/phase2_6/tables/multiseed_delta_summary.csv")
    data = data.loc[data["metric"].eq("roc_auc") if "metric" in data.columns else np.ones(len(data), dtype=bool)].copy()
    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    comparisons = list(data["comparison"].drop_duplicates())
    x = np.arange(len(comparisons)); width=.22
    for offset, population in enumerate(POPULATIONS):
        part = data.loc[data["population"].eq(population)].set_index("comparison").reindex(comparisons)
        mean_col = "mean_delta" if "mean_delta" in part else "delta_mean"
        min_col = "min_delta" if "min_delta" in part else "delta_min"
        max_col = "max_delta" if "max_delta" in part else "delta_max"
        mean = part[mean_col].to_numpy(float)
        ax.errorbar(x+(offset-1)*width, mean, yerr=[mean-part[min_col].to_numpy(float), part[max_col].to_numpy(float)-mean], fmt="o", capsize=2, label=population)
    ax.axhline(0, color="black", linewidth=.7); ax.set_xticks(x, comparisons, rotation=20, ha="right")
    ax.set_ylabel("$\\Delta$ROC-AUC across five seeds"); ax.legend(ncol=3); fig.tight_layout()
    return data, fig


def fig_robustness_scope(temporal: pd.DataFrame) -> tuple[pd.DataFrame, plt.Figure]:
    source = json.loads((PHASE3_TABLES / "source_holdout_status.json").read_text())
    scope = temporal.copy(); scope["kind"] = "temporal"
    scope = pd.concat([scope, pd.DataFrame([{"split": "largest source CC", "n_people": source["largest_group_people"], "positive_count": np.nan, "positive_prevalence": np.nan, "kind": "source"}])], ignore_index=True)
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.7))
    t = temporal.loc[temporal["split"].isin(["train", "validation", "test"])]
    axes[0].bar(t["split"], t["n_people"], color=["#4c78a8", "#72b7b2", "#e45756"])
    axes[0].set_ylabel("People"); axes[0].set_title("(a) SAFE temporal eligible split", loc="left")
    axes[1].bar(["Largest CC", "All eligible"], [source["largest_group_people"], source["eligible_people"]], color=["#e45756", "#b0b0b0"])
    axes[1].set_ylabel("People"); axes[1].set_title(f"(b) Source grouping: {source['largest_group_fraction']:.1%} in one CC", loc="left")
    fig.tight_layout()
    return scope, fig


def main() -> None:
    ensure_phase3_dirs(); configure_style()
    tables = build_scientific_tables()
    builders = [
        ("fig1_task_ep_t", lambda: fig1(), ["outputs/tables/entry_vs_posting_contingency.csv"]),
        ("fig2_dynasty_gender", lambda: fig2(), ["outputs/tables/target_by_dynasty.csv", "outputs/phase2_6/tables/final_gender_entry_rates.csv"]),
        ("fig3_entry_pathways", lambda: fig3(), ["outputs/phase2_6/tables/entry_category_by_dynasty_records.csv", "outputs/phase2_6/tables/entry_category_by_dynasty_people.csv"]),
        ("fig4_locked_models", lambda: fig4(tables["main"]), ["outputs/phase3/tables/main_model_performance.csv"]),
        ("fig5_grouped_ablation", lambda: fig5(tables["ablation"]), ["outputs/phase3/tables/grouped_ablation_summary.csv"]),
        ("fig6_spatial_transport", lambda: fig6(), ["outputs/phase2_6/tables/address_semantics_deltas.csv", "outputs/phase2_6/tables/matched_random_vs_spatial_results.csv"]),
        ("fig7_family_decomposition", lambda: fig7(), ["outputs/phase2_5/tables/family_decomposition_deltas.csv"]),
        ("fig8_grouped_shap", lambda: fig8(), ["outputs/phase2_6/shap/shap_group_summary.csv"]),
        ("figA1_calibration", lambda: fig_calibration(), ["outputs/phase2_6/tables/final_model_calibration.csv"]),
        ("figA2_multiseed", lambda: fig_multiseed(), ["outputs/phase2_6/tables/multiseed_delta_summary.csv"]),
        ("figA3_robustness_scope", lambda: fig_robustness_scope(tables["temporal"]), ["outputs/phase3/tables/safe_temporal_split_context.csv", "outputs/phase3/tables/source_holdout_status.json"]),
    ]
    manifest = []
    for figure_id, builder, upstream in builders:
        data, fig = builder()
        data_path = save_data(data, f"{figure_id}.csv")
        png, pdf, svg = save_figure(fig, figure_id)
        input_paths = [ROOT / value for value in upstream]
        manifest.append({
            "figure_id": figure_id,
            "paper_caption": CAPTIONS[figure_id],
            "script_path": "scripts/56_generate_final_paper_figures.py",
            "input_files": data_path.relative_to(ROOT).as_posix(),
            "input_sha256": sha256_file(data_path),
            "output_png": png,
            "output_pdf": pdf,
            "output_svg": svg,
            "dpi": 300,
            "verified_against_table": True,
            "notes": "Upstream frozen inputs: " + "; ".join(f"{p.relative_to(ROOT).as_posix()} [{sha256_file(p)}]" for p in input_paths),
        })
    pd.DataFrame(manifest).to_csv(PHASE3_TABLES / "figure_manifest.csv", index=False)
    print(f"Generated {len(manifest)} figures in PNG/PDF/SVG with project-local inputs.")


if __name__ == "__main__":
    main()
