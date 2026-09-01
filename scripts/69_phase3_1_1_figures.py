#!/usr/bin/env python3
"""Render the Phase 3.1.1 figure set from frozen, retained inputs only."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
FIG_DIR = ROOT / "outputs/phase3_1_1/figures"
DATA_DIR = ROOT / "outputs/phase3_1_1/figure_data"
TABLE_DIR = ROOT / "outputs/phase3_1_1/tables"
PAPER_FIG_DIR = ROOT / "paper/final/figures"
QA_DIR = ROOT / "outputs/phase3_1_1/figure_qa"
POPULATIONS = ["Global", "Song", "Ming"]
MODELS = ["H_STRUCT", "D5_MAIN", "D6_UPPER"]


def load_phase31():
    path = ROOT / "scripts/63_phase3_1_figures.py"
    spec = importlib.util.spec_from_file_location("phase31_figures_readonly", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.FIG_DIR = FIG_DIR
    module.DATA_DIR = DATA_DIR
    module.TABLE_DIR = TABLE_DIR
    module.PAPER_FIG_DIR = PAPER_FIG_DIR
    module.QA_DIR = QA_DIR
    return module


CAPTIONS = {
    "final_task_definition_ep_t": (
        "Measurement and construct boundary. Panel a distinguishes latent true historical entry T; "
        "credential, education, recommendation, privilege, and other entry-related events that are not T; "
        "posting or office-holding events related to but not equivalent to T; other biographical processes; "
        "source survival; extraction and encoding; and the observed E and P relations. E, P, and T are "
        "distinct constructs and are not interchangeable. Panel b preserves the frozen E by P contingency counts."
    ),
    "fig2_dynasty_gender": (
        "CBDB-covered people and recorded ENTRY share. Panel a reports coverage and E prevalence for "
        "Tang, Song, Yuan, Ming, and Qing. Panel b reports E prevalence by recorded gender; neither panel "
        "estimates historical population entry rates."
    ),
    "fig3_entry_pathways": (
        "Recorded ENTRY pathway composition. Record shares and nonexclusive person prevalence describe "
        "heterogeneous observed entry-related records, not latent true historical entry T."
    ),
    "fig4_locked_models": (
        "Frozen primary-test discrimination in Global, Song, and Ming. D5_MAIN is the designated main "
        "within-database predictor; D6_UPPER is a database-internal record-structure upper bound."
    ),
    "fig5_grouped_ablation": (
        "Conditional Global primary-split increments in the prespecified nested feature order. They are "
        "order-dependent predictive increments, not unique or causal contributions; Physical geography "
        "has no interval because exact paired predictions were not retained."
    ),
    "fig6_spatial_transport": (
        "Address decomposition and matched-support spatial transport. Negative unseen-region minus "
        "matched-random ROC-AUC means weaker discrimination on unseen historical regions."
    ),
    "fig7_family_decomposition": (
        "Family-feature decomposition in Global, Song, and Ming order. Family-capital increments are "
        "conditional on observability and topology; Ming ROC-AUC and PR-AUC intervals include zero."
    ),
    "fig8_grouped_shap": (
        "Grouped mean absolute SHAP shares for Global, Song, and Ming. Physical geography denotes "
        "latitude, longitude, and distance to the dynasty-specific capital. Shares are model attribution, "
        "not independent gains or causal effects."
    ),
    "figA1_calibration": (
        "Raw and validation-calibrated expected calibration error. Sigmoid calibrators were fitted on "
        "validation predictions only; lower ECE is better."
    ),
    "figA2_multiseed": (
        "Five-seed stability of selected incremental ROC-AUC contrasts in Global, Song, and Ming order."
    ),
    "figA3_robustness_scope": (
        "Scope of unavailable robustness performance. SAFE is split-only, and source grouping was infeasible "
        "under the prespecified full-coverage connected-component protocol."
    ),
}


def task_figure(base) -> tuple[pd.DataFrame, plt.Figure, list[plt.Axes]]:
    data = pd.read_csv(ROOT / "outputs/tables/entry_vs_posting_contingency.csv")
    fig, axes = plt.subplots(1, 2, figsize=(7.25, 3.55), gridspec_kw={"width_ratios": [1.7, 0.9]})
    ax = axes[0]
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 14)
    ax.axis("off")

    def box(x: float, y: float, w: float, h: float, label: str, fill: str) -> None:
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.10,rounding_size=0.12",
            facecolor=fill, edgecolor="#555555", linewidth=0.55,
        ))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
                fontsize=6.5, linespacing=1.08)

    box(5.75, 12.25, 4.50, 1.15, "$T$: true historical entry\ninto government (latent)", "#E8E0F0")
    box(0.20, 9.15, 5.20, 2.10,
        "Credential / education /\nrecommendation / privilege /\nother entry-related events\n(not identical to $T$)", "#DCEAF4")
    box(5.75, 9.30, 4.55, 1.80,
        "Posting / office-holding\nevents related to $T$\nbut not equivalent", "#DDEFE9")
    box(10.65, 9.30, 5.10, 1.80,
        "Other historical\nbiographical processes", "#EEEEEE")
    box(1.25, 6.90, 13.50, 1.10, "Source survival and selection", "#FFF1CC")
    box(1.25, 4.80, 13.50, 1.10, "Editorial extraction and database encoding", "#F7E4C4")
    box(1.85, 2.15, 5.20, 1.30, "Observed $E$\nENTRY_DATA record presence", "#DCEAF4")
    box(8.95, 2.15, 5.20, 1.30, "Observed $P$\nvalid posting-record presence", "#DDEFE9")

    arrow = dict(arrowstyle="-|>", mutation_scale=8, color="#6A6A6A", linewidth=0.75)
    ax.add_patch(FancyArrowPatch((7.25, 12.20), (3.25, 11.15), linestyle="--",
                                 connectionstyle="arc3,rad=0.08", **arrow))
    ax.add_patch(FancyArrowPatch((8.75, 12.20), (8.05, 11.15), linestyle="--",
                                 connectionstyle="arc3,rad=-0.08", **arrow))
    ax.text(11.25, 11.70, r"association $\ne$ identity", fontsize=5.8, ha="center", color="#555555")
    for x in (2.8, 8.0, 13.2):
        ax.add_patch(FancyArrowPatch((x, 9.25), (8.0, 8.05), **arrow))
    ax.add_patch(FancyArrowPatch((8.0, 6.85), (8.0, 5.95), **arrow))
    ax.add_patch(FancyArrowPatch((6.6, 4.75), (4.45, 3.50), **arrow))
    ax.add_patch(FancyArrowPatch((9.4, 4.75), (11.55, 3.50), **arrow))
    ax.text(8.0, 0.65, "E, P, and T are distinct constructs and are not interchangeable.",
            ha="center", va="center", fontsize=7.1, fontweight="bold", color="#333333")
    ax.set_title("Constructs, historical events, and recorded labels", loc="left", pad=8)

    matrix = data.pivot(index="has_entry", columns="has_posting", values="n_people").reindex(
        index=[1, 0], columns=[0, 1]
    )
    sns.heatmap(
        matrix, annot=True, fmt=",.0f", cmap=sns.light_palette("#4C78A8", as_cmap=True),
        cbar=False, linewidths=0.8, linecolor="white", square=False, ax=axes[1],
        annot_kws={"fontsize": 8},
    )
    axes[1].set_xlabel("Observed Posting label $P$")
    axes[1].set_ylabel("Observed ENTRY label $E$")
    axes[1].set_xticklabels(["0", "1"])
    axes[1].set_yticklabels(["1", "0"], rotation=0)
    axes[1].set_title("Frozen $E\\times P$ contingency", loc="left", pad=8)
    fig.subplots_adjust(left=0.035, right=0.99, bottom=0.13, top=0.90, wspace=0.24)
    base.add_panel_labels(list(axes))
    return data, fig, list(axes)


def family_figure(base) -> tuple[pd.DataFrame, plt.Figure, list[plt.Axes]]:
    family = pd.read_csv(ROOT / "outputs/phase2_5/tables/family_decomposition_deltas.csv")
    keep = family.loc[family["comparison"].isin(["F1 - F0", "F2 - F1", "F3 - F2", "F4 - F2"])].copy()
    labels = {
        "F1 - F0": "observability", "F2 - F1": "topology",
        "F3 - F2": "full-record capital", "F4 - F2": "train-observed capital",
    }
    keep["block"] = keep["comparison"].map(labels)
    fig, axes = plt.subplots(1, 2, figsize=(7.25, 2.75), sharey=True)
    for ax, metric, title in [
        (axes[0], "delta_roc_auc", "$\\Delta$ROC-AUC"),
        (axes[1], "delta_pr_auc", "$\\Delta$PR-AUC"),
    ]:
        sns.barplot(
            data=keep, x="population", y=metric, hue="block", order=POPULATIONS,
            hue_order=list(labels.values()), ax=ax, palette="colorblind",
        )
        ax.axhline(0, color="black", linewidth=0.75)
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.set_title(title, loc="left")
        if ax is axes[0]:
            ax.get_legend().remove()
        else:
            ax.legend(title="", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=False)
    fig.subplots_adjust(left=0.08, right=0.78, bottom=0.19, top=0.89, wspace=0.22)
    base.add_panel_labels(list(axes))
    return keep, fig, list(axes)


def spatial_figure(base) -> tuple[pd.DataFrame, plt.Figure, list[plt.Axes]]:
    address = pd.read_csv(ROOT / "outputs/phase2_6/tables/address_semantics_deltas.csv")
    spatial = pd.read_csv(ROOT / "outputs/phase2_6/tables/matched_random_vs_spatial_results.csv")
    data = pd.concat(
        [address.assign(panel="address"), spatial.assign(panel="spatial")],
        ignore_index=True, sort=False,
    )
    fig, axes = plt.subplots(1, 2, figsize=(7.25, 2.95))
    address_global = address.loc[address["population"].eq("Global")].copy()
    labels = [
        "observability", "administrative", "physical geography",
        "address semantics", "density", "local target prior",
    ]
    axes[0].barh(labels, address_global["delta_roc_auc"], color="#4C78A8")
    axes[0].axvline(0, color="black", linewidth=0.8)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("$\\Delta$ROC-AUC")
    axes[0].set_title("Address blocks, Global", loc="left")
    axes[0].grid(axis="x", color="#E6E6E6", linewidth=0.5)
    axes[0].grid(axis="y", visible=False)

    ordered = spatial.copy()
    ordered["population"] = pd.Categorical(
        ordered["population"], POPULATIONS, ordered=True
    )
    ordered["model_id"] = pd.Categorical(
        ordered["model_id"], ["H_STRUCT", "D5_MAIN"], ordered=True
    )
    ordered = ordered.sort_values(["population", "model_id"])
    ordered["label"] = (
        ordered["population"].astype("string") + " " + ordered["model_id"].astype("string")
    )
    colors = ordered["model_id"].astype("string").map(
        {"H_STRUCT": "#4C78A8", "D5_MAIN": "#E45756"}
    )
    axes[1].barh(
        ordered["label"], ordered["delta_spatial_minus_random_roc_auc"], color=colors
    )
    axes[1].invert_yaxis()
    axes[1].set_xlim(-0.07, 0.005)
    axes[1].axvspan(-0.07, 0, color="#F8E0E0", alpha=0.45, zorder=-2)
    axes[1].axvline(0, color="black", linewidth=0.8)
    axes[1].set_xlabel(
        "Unseen-region − matched-random ROC-AUC\n(negative = weaker)"
    )
    axes[1].set_title("Unseen-region transport", loc="left")
    axes[1].grid(axis="x", color="#E6E6E6", linewidth=0.5)
    axes[1].grid(axis="y", visible=False)
    fig.subplots_adjust(left=0.16, right=0.98, bottom=0.25, top=0.88, wspace=0.56)
    base.add_panel_labels(list(axes))
    return data, fig, list(axes)


def shap_figure(base) -> tuple[pd.DataFrame, plt.Figure, list[plt.Axes]]:
    shap = pd.read_csv(ROOT / "outputs/phase2_6/shap/shap_group_summary.csv").copy()
    shap["feature_group"] = shap["feature_group"].replace({"other": "historical_regime"})
    display = {
        "address_observability": "Address observability",
        "address_record_semantics": "Address-record semantics",
        "administrative_geography": "Administrative geography",
        "continuous_geography": "Physical geography",
        "documentation_general": "General documentation",
        "family_full_record_capital": "Family political capital",
        "family_observability": "Family observability",
        "family_topology": "Family topology",
        "historical_regime": "Historical regime",
        "personal_birth_cohort": "Birth cohort",
        "personal_gender": "Gender",
        "regional_density": "Regional density",
        "supervised_local_prior": "Local target prior",
    }
    groups = sorted(shap["feature_group"].unique())
    labels = [display.get(group, group.replace("_", " ").capitalize()) for group in groups]
    fig = plt.figure(figsize=(7.25, 3.75))
    grid = fig.add_gridspec(1, 4, width_ratios=[1, 1, 1, 0.06], wspace=0.22)
    axes = [fig.add_subplot(grid[0, index]) for index in range(3)]
    cax = fig.add_subplot(grid[0, 3])
    for index, (ax, population) in enumerate(zip(axes, POPULATIONS)):
        pivot = (
            shap.loc[shap["population"].eq(population)]
            .pivot(index="feature_group", columns="model_id", values="group_share_of_total_abs_shap")
            .reindex(index=groups, columns=MODELS)
        )
        sns.heatmap(
            100 * pivot, cmap="Blues", vmin=0, vmax=35, cbar=index == 2,
            cbar_ax=cax if index == 2 else None, ax=ax, linewidths=0.35,
            linecolor="white", square=False,
        )
        ax.set_title(population, loc="center", pad=6)
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.set_xticklabels(MODELS, rotation=55, ha="right", rotation_mode="anchor")
        ax.set_yticks(np.arange(len(labels)) + 0.5)
        ax.set_yticklabels(labels if index == 0 else [], rotation=0)
    cax.set_ylabel("Mean |SHAP| share (%)", fontsize=7)
    fig.subplots_adjust(left=0.25, right=0.94, bottom=0.24, top=0.90)
    base.add_panel_labels(axes)
    return shap, fig, axes


def main() -> None:
    base = load_phase31()
    for directory in (FIG_DIR, DATA_DIR, TABLE_DIR, PAPER_FIG_DIR, QA_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    base.configure_style()
    legacy = base.load_legacy_plotters()
    base.configure_style()
    main_models = pd.read_csv(ROOT / "outputs/phase3/tables/main_model_performance.csv")
    ablation = pd.read_csv(ROOT / "outputs/phase3_1/tables/grouped_ablation_corrected.csv")
    temporal = pd.read_csv(ROOT / "outputs/phase3/tables/safe_temporal_split_context.csv")

    manifest = []
    input_hashes = []
    for figure_id in CAPTIONS:
        if figure_id == "final_task_definition_ep_t":
            data, fig, axes = task_figure(base)
        elif figure_id == "fig4_locked_models":
            data, fig, axes = base.locked_model_figure(main_models)
        elif figure_id == "fig7_family_decomposition":
            data, fig, axes = family_figure(base)
        elif figure_id == "fig6_spatial_transport":
            data, fig, axes = spatial_figure(base)
        elif figure_id == "fig8_grouped_shap":
            data, fig, axes = shap_figure(base)
        else:
            data, fig, axes = base.revise_legacy(
                figure_id, legacy, main_models, ablation, temporal
            )
        png, pdf, svg, snapshot = base.save_and_audit(figure_id, data, fig, axes)
        sources = base.SOURCES[figure_id]
        hashes = []
        for relative in sources:
            source = ROOT / relative
            digest = base.sha256_file(source)
            hashes.append(digest)
            input_hashes.append({
                "figure_id": figure_id, "source_path": relative, "sha256": digest,
            })
        manifest.append({
            "figure_id": figure_id,
            "paper_section": base.SECTIONS[figure_id],
            "caption": CAPTIONS[figure_id],
            "source_tables": ";".join(sources),
            "source_sha256": ";".join(hashes),
            "generation_script": "scripts/69_phase3_1_1_figures.py",
            "png_path": png, "pdf_path": pdf, "svg_path": svg,
            "snapshot_path": snapshot,
            "verification_status": "VERIFIED_FROM_FROZEN_INPUT; alignment=PASS",
        })
    pd.DataFrame(manifest).to_csv(TABLE_DIR / "figure_manifest_final.csv", index=False)
    pd.DataFrame(input_hashes).drop_duplicates().to_csv(
        TABLE_DIR / "figure_input_hashes.csv", index=False
    )
    print(f"PASS: rendered {len(manifest)} Phase 3.1.1 figures from frozen inputs")


if __name__ == "__main__":
    main()
