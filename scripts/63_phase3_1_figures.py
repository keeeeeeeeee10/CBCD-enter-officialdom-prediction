#!/usr/bin/env python3
"""Render the Phase 3.1 submission figures from frozen, project-local artifacts."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
import types
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "outputs" / "phase3_1" / "figures"
DATA_DIR = ROOT / "outputs" / "phase3_1" / "figure_data"
TABLE_DIR = ROOT / "outputs" / "phase3_1" / "tables"
PAPER_FIG_DIR = ROOT / "paper" / "revised" / "figures"
QA_DIR = ROOT / "outputs" / "phase3_1" / "figure_qa"
FIGURE_AUDIT_SCRIPTS_VALUE = os.environ.get("PHASE31_FIGURE_AUDIT_SCRIPTS")
if not FIGURE_AUDIT_SCRIPTS_VALUE:
    raise RuntimeError(
        "Set PHASE31_FIGURE_AUDIT_SCRIPTS to the directory containing "
        "audit_panel_alignment.py before running this archival figure script."
    )
FIGURE_AUDIT_SCRIPTS = Path(FIGURE_AUDIT_SCRIPTS_VALUE).expanduser().resolve()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(FIGURE_AUDIT_SCRIPTS))

from audit_panel_alignment import require_matplotlib_panel_alignment  # noqa: E402
from src.utils import sha256_file  # noqa: E402


POPULATIONS = ["Global", "Song", "Ming"]
MODELS = ["H_STRUCT", "D5_MAIN", "D6_UPPER"]
MODEL_COLORS = {"Logistic M6": "#8A8A8A", "H_STRUCT": "#4C78A8", "D5_MAIN": "#D95F5F", "D6_UPPER": "#5FA39B"}

CAPTIONS = {
    "final_task_definition_ep_t": "Observed database labels and latent historical concepts. Panel a separates historical entry or credential events, posting or office-holding events, and broader biographical processes before source survival, editorial extraction, and database encoding. T is the latent true historical entry state; E and P are semantically distinct, incomplete observations. Panel b reports all CBDB-covered people in the frozen E by P contingency table.",
    "fig2_dynasty_gender": "CBDB-covered people and recorded ENTRY share. Panel a reports the number of covered people and E prevalence within each displayed dynasty. Panel b reports E prevalence within CBDB-covered gender groups for Global, Song, Ming, and Qing; neither panel estimates historical population entry rates.",
    "fig3_entry_pathways": "Recorded ENTRY pathway composition. Panel a shows the share of ENTRY records and panel b the prevalence among all CBDB-covered people, by dynasty. Person-level pathways are nonexclusive, so panel-b shares may sum above 100%.",
    "fig4_locked_models": "Frozen primary-test discrimination. ROC-AUC and PR-AUC compare the linear baseline and locked CatBoost models in Global, Song, and Ming. D5_MAIN is the designated main model; D6_UPPER includes lifetime relatives' record information and is a database-internal upper bound.",
    "fig5_grouped_ablation": "Conditional Global primary-split increments for prespecified feature blocks. Bars show the metric change when each block enters its stated nested comparison; intervals are omitted where exact paired prediction artifacts were not retained. Negative increments extend left of zero.",
    "fig6_spatial_transport": "Address decomposition and spatial transport. Panel a reports Global conditional ROC-AUC increments for address blocks. Panel b reports matched-support unseen-region minus matched-random ROC-AUC; every negative value denotes weaker discrimination on unseen historical regions, not a causal geographic effect.",
    "fig7_family_decomposition": "Family-feature decomposition on the frozen primary split. Conditional ROC-AUC and PR-AUC increments are reported for Global, Song, and Ming. Observability and topology are separated from full-record and train-observed political-capital summaries.",
    "fig8_grouped_shap": "Grouped mean absolute SHAP shares for Global, Song, and Ming locked models. Blank cells denote groups absent from a model. Historical regime replaces the previous ambiguous label 'other'. Shares describe attribution within the fitted model, not independent ablation gains or causal effects.",
    "figA1_calibration": "Raw and validation-calibrated expected calibration error on the frozen primary test. The sigmoid calibrator was fitted on validation predictions only; lower ECE is better.",
    "figA2_multiseed": "Five-seed stability of selected incremental ROC-AUC contrasts. Points are seed means and whiskers span the observed minimum to maximum across five prespecified seeds for Global, Song, and Ming.",
    "figA3_robustness_scope": "Scope of uncompleted robustness tests. Panel a reports eligible people in the frozen SAFE temporal split, for which no locked-model performance artifact exists. Panel b shows that the largest connected primary-source component exceeds the prespecified grouping cap, preventing the planned leakage-free source-group confirmation.",
}

SECTIONS = {
    "final_task_definition_ep_t": "Data and Measurement Problem",
    "fig2_dynasty_gender": "Descriptive Evidence",
    "fig3_entry_pathways": "Descriptive Evidence",
    "fig4_locked_models": "Primary Predictive Results",
    "fig5_grouped_ablation": "Feature-Block Evidence",
    "fig6_spatial_transport": "Distribution Shift",
    "fig7_family_decomposition": "Family Decomposition",
    "fig8_grouped_shap": "Model Interpretation",
    "figA1_calibration": "Appendix: Calibration",
    "figA2_multiseed": "Appendix: Stability",
    "figA3_robustness_scope": "Appendix: Robustness Scope",
}

SOURCES = {
    "final_task_definition_ep_t": ["outputs/tables/entry_vs_posting_contingency.csv"],
    "fig2_dynasty_gender": ["outputs/tables/target_by_dynasty.csv", "outputs/phase2_6/tables/final_gender_entry_rates.csv"],
    "fig3_entry_pathways": ["outputs/phase2_6/tables/entry_category_by_dynasty_records.csv", "outputs/phase2_6/tables/entry_category_by_dynasty_people.csv"],
    "fig4_locked_models": ["outputs/phase3/tables/main_model_performance.csv"],
    "fig5_grouped_ablation": ["outputs/phase3_1/tables/grouped_ablation_corrected.csv"],
    "fig6_spatial_transport": ["outputs/phase2_6/tables/address_semantics_deltas.csv", "outputs/phase2_6/tables/matched_random_vs_spatial_results.csv"],
    "fig7_family_decomposition": ["outputs/phase2_5/tables/family_decomposition_deltas.csv"],
    "fig8_grouped_shap": ["outputs/phase2_6/shap/shap_group_summary.csv"],
    "figA1_calibration": ["outputs/phase2_6/tables/final_model_calibration.csv"],
    "figA2_multiseed": ["outputs/phase2_6/tables/multiseed_delta_summary.csv"],
    "figA3_robustness_scope": ["outputs/phase3/tables/safe_temporal_split_context.csv", "outputs/phase3/tables/source_holdout_status.json"],
}


def load_legacy_plotters():
    """Load trusted plot constructors without rerunning or modifying Phase 3."""
    # The old plotting module imports src.phase3 only for path constants, while
    # src.phase3 imports CatBoost training code.  Supply a path-only shim so
    # this revision cannot import or invoke the training stack.
    phase3_shim = types.ModuleType("src.phase3")
    phase3_shim.ROOT = ROOT
    phase3_shim.PHASE3_FIGURE_DATA = ROOT / "outputs" / "phase3" / "figure_data"
    phase3_shim.PHASE3_FIGURES = ROOT / "outputs" / "phase3" / "figures"
    phase3_shim.PHASE3_TABLES = ROOT / "outputs" / "phase3" / "tables"
    phase3_shim.ensure_phase3_dirs = lambda: None
    sys.modules["src.phase3"] = phase3_shim
    path = ROOT / "scripts" / "56_generate_final_paper_figures.py"
    spec = importlib.util.spec_from_file_location("phase3_plotters_readonly", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def configure_style() -> None:
    sns.set_theme(style="ticks", context="paper")
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 7.5, "axes.titlesize": 8.3, "axes.labelsize": 7.5,
        "legend.fontsize": 6.7, "xtick.labelsize": 6.7, "ytick.labelsize": 6.7,
        "axes.spines.right": False, "axes.spines.top": False, "axes.linewidth": 0.7,
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
        "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    })


def add_panel_labels(axes: list[plt.Axes]) -> None:
    for idx, ax in enumerate(axes):
        ax.annotate(chr(ord("a") + idx), xy=(0, 1), xycoords="axes fraction",
                    xytext=(-18, 7), textcoords="offset points", ha="left", va="bottom",
                    fontsize=8, fontweight="bold", annotation_clip=False)


def clean_legacy_titles(axes: list[plt.Axes]) -> None:
    for ax in axes:
        title = ax.get_title(loc="left") or ax.get_title()
        if title.startswith("(") and len(title) > 4 and title[2:4] == ") ":
            ax.set_title(title[4:], loc="left")
        ax.grid(axis="x", color="#E6E6E6", linewidth=0.5)
        ax.grid(axis="y", visible=False)


def task_figure() -> tuple[pd.DataFrame, plt.Figure, list[plt.Axes]]:
    data = pd.read_csv(ROOT / SOURCES["final_task_definition_ep_t"][0])
    fig, axes = plt.subplots(1, 2, figsize=(7.25, 3.15), gridspec_kw={"width_ratios": [1.45, 1.0]})
    ax = axes[0]
    ax.set_xlim(0, 12); ax.set_ylim(0, 12); ax.axis("off")

    def box(x: float, y: float, w: float, h: float, label: str, fill: str, edge: str = "#4A4A4A") -> None:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.10,rounding_size=0.12",
                                    facecolor=fill, edgecolor="none", linewidth=0))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=7.1, linespacing=1.15)

    box(0.15, 9.6, 3.55, 1.35, "Historical entry /\ncredential events\n(T: latent entry state)", "#DCEAF4", "#4C78A8")
    box(4.20, 9.6, 3.55, 1.35, "Historical posting /\noffice-holding events", "#DDEFE9", "#5FA39B")
    box(8.25, 9.6, 3.55, 1.35, "Other historical\nbiographical processes", "#EEEEEE", "#777777")
    box(2.0, 6.65, 8.0, 1.05, "Source survival and selection", "#FFF1CC", "#B88B26")
    box(2.0, 4.45, 8.0, 1.05, "Editorial extraction and database encoding", "#F7E4C4", "#B87333")
    box(1.25, 1.65, 4.15, 1.20, "Observed ENTRY label E\nENTRY_DATA record present", "#DCEAF4", "#4C78A8")
    box(6.60, 1.65, 4.15, 1.20, "Observed Posting label P\nvalid posting record present", "#DDEFE9", "#5FA39B")
    for x in (1.95, 5.98, 10.03):
        ax.add_patch(FancyArrowPatch((x, 9.30), (6.0, 7.85), arrowstyle="-|>", mutation_scale=9,
                                     color="#777777", linewidth=0.8, connectionstyle="arc3,rad=0"))
    ax.add_patch(FancyArrowPatch((6.0, 6.60), (6.0, 5.55), arrowstyle="-|>", mutation_scale=9, color="#777777", linewidth=0.8))
    for x in (3.33, 8.67):
        ax.add_patch(FancyArrowPatch((6.0, 4.40), (x, 2.90), arrowstyle="-|>", mutation_scale=9, color="#777777", linewidth=0.8))
    ax.text(6, 0.45, "E, P, and T are semantically distinct; E and P are incomplete observations.",
            ha="center", va="center", fontsize=7.2, color="#333333")
    ax.set_title("Measurement and encoding processes", loc="left", pad=9)

    matrix = data.pivot(index="has_entry", columns="has_posting", values="n_people").reindex(index=[1, 0], columns=[0, 1])
    sns.heatmap(matrix, annot=True, fmt=",.0f", cmap=sns.light_palette("#4C78A8", as_cmap=True), cbar=False,
                linewidths=0.8, linecolor="white", square=True, ax=axes[1], annot_kws={"fontsize": 8})
    axes[1].set_xlabel("Observed Posting label P")
    axes[1].set_ylabel("Observed ENTRY label E")
    axes[1].set_xticklabels(["0", "1"]); axes[1].set_yticklabels(["1", "0"], rotation=0)
    axes[1].set_title("Frozen E × P contingency", loc="left", pad=9)
    fig.subplots_adjust(left=0.045, right=0.99, bottom=0.16, top=0.88, wspace=0.30)
    add_panel_labels(list(axes))
    return data, fig, list(axes)


def shap_figure() -> tuple[pd.DataFrame, plt.Figure, list[plt.Axes]]:
    shap = pd.read_csv(ROOT / SOURCES["fig8_grouped_shap"][0]).copy()
    shap["feature_group"] = shap["feature_group"].replace({"other": "historical_regime"})
    display = {
        "address_admin": "Administrative geography", "address_observability": "Address observability",
        "address_physical": "Physical geography", "address_semantics": "Address-record semantics",
        "density": "Spatial density", "family_capital": "Family political capital",
        "family_observability": "Family observability", "family_topology": "Family topology",
        "gender": "Gender", "historical_regime": "Historical regime", "local_prior": "Local prior",
        "personal": "Personal attributes",
    }
    groups = [g for g in sorted(shap["feature_group"].unique())]
    labels = [display.get(g, g.replace("_", " ").capitalize()) for g in groups]
    fig = plt.figure(figsize=(7.25, 3.75))
    grid = fig.add_gridspec(1, 4, width_ratios=[1, 1, 1, 0.06], wspace=0.22)
    axes = [fig.add_subplot(grid[0, i]) for i in range(3)]
    cax = fig.add_subplot(grid[0, 3])
    for idx, (ax, population) in enumerate(zip(axes, POPULATIONS)):
        pivot = (shap.loc[shap["population"].eq(population)]
                 .pivot(index="feature_group", columns="model_id", values="group_share_of_total_abs_shap")
                 .reindex(index=groups, columns=MODELS))
        sns.heatmap(100 * pivot, cmap="Blues", vmin=0, vmax=35, cbar=idx == 2, cbar_ax=cax if idx == 2 else None,
                    ax=ax, linewidths=0.35, linecolor="white", square=False)
        ax.set_title(population, loc="center", pad=6); ax.set_xlabel(""); ax.set_ylabel("")
        ax.set_xticklabels(MODELS, rotation=55, ha="right", rotation_mode="anchor")
        ax.set_yticks(np.arange(len(labels)) + 0.5)
        ax.set_yticklabels(labels if idx == 0 else [], rotation=0)
    cax.set_ylabel("Mean |SHAP| share (%)", fontsize=7)
    fig.subplots_adjust(left=0.25, right=0.94, bottom=0.24, top=0.90)
    add_panel_labels(axes)
    return shap, fig, axes


def locked_model_figure(main: pd.DataFrame) -> tuple[pd.DataFrame, plt.Figure, list[plt.Axes]]:
    order = ["Logistic M6", "H_STRUCT", "D5_MAIN", "D6_UPPER"]
    data = main.loc[main["population"].isin(POPULATIONS) & main["model_id"].isin(order)].copy()
    fig, axes = plt.subplots(1, 2, figsize=(7.25, 2.75), sharex=True)
    offsets = np.linspace(-0.18, 0.18, len(order))
    x = np.arange(len(POPULATIONS))
    for ax, metric, label, limits in (
        (axes[0], "roc_auc", "ROC-AUC", (0.68, 0.97)),
        (axes[1], "pr_auc", "PR-AUC", (0.35, 0.95)),
    ):
        for offset, model in zip(offsets, order):
            part = data.loc[data["model_id"].eq(model)].set_index("population").reindex(POPULATIONS)
            ax.scatter(x + offset, part[metric], s=28, color=MODEL_COLORS[model], label=model,
                       edgecolors="white", linewidths=0.5, zorder=3)
        ax.set_xticks(x, POPULATIONS); ax.set_ylim(*limits); ax.set_ylabel(label); ax.set_title(label, loc="left")
        ax.grid(axis="y", color="#E6E6E6", linewidth=0.5); ax.grid(axis="x", visible=False)
    axes[1].legend(title="Frozen model", loc="upper left", bbox_to_anchor=(1.02, 1.0), ncol=1,
                   columnspacing=0.9, handletextpad=0.35, frameon=False)
    fig.subplots_adjust(left=0.09, right=0.81, bottom=0.20, top=0.90, wspace=0.30)
    add_panel_labels(list(axes))
    return data, fig, list(axes)


def revise_legacy(figure_id: str, legacy, main: pd.DataFrame, ablation: pd.DataFrame, temporal: pd.DataFrame):
    if figure_id == "fig2_dynasty_gender": data, fig = legacy.fig2()
    elif figure_id == "fig3_entry_pathways": data, fig = legacy.fig3()
    elif figure_id == "fig4_locked_models": data, fig = legacy.fig4(main)
    elif figure_id == "fig5_grouped_ablation": data, fig = legacy.fig5(ablation)
    elif figure_id == "fig6_spatial_transport": data, fig = legacy.fig6()
    elif figure_id == "fig7_family_decomposition": data, fig = legacy.fig7()
    elif figure_id == "figA1_calibration": data, fig = legacy.fig_calibration()
    elif figure_id == "figA2_multiseed": data, fig = legacy.fig_multiseed()
    elif figure_id == "figA3_robustness_scope": data, fig = legacy.fig_robustness_scope(temporal)
    else: raise KeyError(figure_id)

    # Main plot axes are subplot axes; twins and colorbars are not separate inferential panels.
    axes: list[plt.Axes] = []
    seen = set()
    for ax in fig.axes:
        if not ax.get_visible() or str(ax.get_label()).startswith("<colorbar"):
            continue
        try: spec = ax.get_subplotspec()
        except AttributeError: spec = None
        key = (id(spec.get_gridspec()), spec.num1, spec.num2) if spec is not None else id(ax)
        if key in seen: continue
        seen.add(key); axes.append(ax)
    clean_legacy_titles(axes)
    if len(axes) > 1: add_panel_labels(axes)

    # Clarify ambiguous, direction-sensitive, and calibration displays.
    if figure_id == "fig6_spatial_transport":
        axes[1].axvspan(min(axes[1].get_xlim()[0], -0.2), 0, color="#F8E0E0", alpha=0.45, zorder=-2)
        axes[1].set_xlabel("Unseen-region − matched-random ROC-AUC")
    if figure_id == "figA1_calibration":
        axes[0].set_title("Raw probability ECE", loc="left")
        axes[1].set_title("Validation-calibrated probability ECE", loc="left")
    if figure_id == "fig3_entry_pathways" and axes:
        axes[-1].legend(title="ENTRY pathway", bbox_to_anchor=(1.01, 1), loc="upper left", frameon=False)
    if figure_id == "fig2_dynasty_gender":
        axes[1].legend(title="Recorded gender", bbox_to_anchor=(1.01, 1), loc="upper left", ncol=1, frameon=False)
    if figure_id == "fig5_grouped_ablation":
        axes[0].legend(loc="upper left", bbox_to_anchor=(1.01, 1), frameon=False, ncol=1)
    return data, fig, axes


def save_and_audit(figure_id: str, data: pd.DataFrame, fig: plt.Figure, axes: list[plt.Axes]) -> tuple[str, str, str, str]:
    data_path = DATA_DIR / f"{figure_id}.csv"
    data.to_csv(data_path, index=False)
    alignment_path = QA_DIR / f"{figure_id}.alignment.json"
    alignment_svg = QA_DIR / f"{figure_id}.alignment.svg"
    panel_ids = [chr(ord("a") + i) for i in range(len(axes))]
    require_matplotlib_panel_alignment(
        fig, axes=axes, panel_ids=panel_ids, json_out=alignment_path,
        overlay_svg=alignment_svg, tolerance_pt=1.5, gutter_tolerance_pt=1.5,
        require_panel_labels=len(axes) > 1, strict=True,
    )
    png_path = FIG_DIR / f"{figure_id}.png"
    pdf_path = FIG_DIR / f"{figure_id}.pdf"
    svg_path = FIG_DIR / f"{figure_id}.svg"
    fig.savefig(png_path, dpi=300, bbox_inches="tight", pad_inches=0.04)
    fig.savefig(pdf_path, bbox_inches="tight", pad_inches=0.04)
    fig.savefig(svg_path, bbox_inches="tight", pad_inches=0.04)
    for path in (png_path, pdf_path, svg_path):
        shutil.copy2(path, PAPER_FIG_DIR / path.name)
    plt.close(fig)
    return (png_path.relative_to(ROOT).as_posix(), pdf_path.relative_to(ROOT).as_posix(),
            svg_path.relative_to(ROOT).as_posix(), data_path.relative_to(ROOT).as_posix())


def main() -> None:
    for directory in (FIG_DIR, DATA_DIR, TABLE_DIR, PAPER_FIG_DIR, QA_DIR): directory.mkdir(parents=True, exist_ok=True)
    configure_style()
    legacy = load_legacy_plotters()
    configure_style()  # legacy module import does not choose the Phase 3.1 style.
    main_models = pd.read_csv(ROOT / "outputs/phase3/tables/main_model_performance.csv")
    ablation = pd.read_csv(ROOT / "outputs/phase3_1/tables/grouped_ablation_corrected.csv")
    temporal = pd.read_csv(ROOT / "outputs/phase3/tables/safe_temporal_split_context.csv")

    ids = list(CAPTIONS)
    manifest = []
    for figure_id in ids:
        if figure_id == "final_task_definition_ep_t": data, fig, axes = task_figure()
        elif figure_id == "fig4_locked_models": data, fig, axes = locked_model_figure(main_models)
        elif figure_id == "fig8_grouped_shap": data, fig, axes = shap_figure()
        else: data, fig, axes = revise_legacy(figure_id, legacy, main_models, ablation, temporal)
        png, pdf, svg, snapshot = save_and_audit(figure_id, data, fig, axes)
        source_paths = [ROOT / value for value in SOURCES[figure_id]]
        manifest.append({
            "figure_id": figure_id, "paper_section": SECTIONS[figure_id], "caption": CAPTIONS[figure_id],
            "source_tables": ";".join(SOURCES[figure_id]),
            "source_sha256": ";".join(sha256_file(path) for path in source_paths),
            "generation_script": "scripts/63_phase3_1_figures.py", "png_path": png, "pdf_path": pdf, "svg_path": svg,
            "verification_status": f"VERIFIED_FROM_FROZEN_INPUT; snapshot={snapshot}; alignment=PASS",
        })
    pd.DataFrame(manifest).to_csv(TABLE_DIR / "figure_manifest_revised.csv", index=False)
    print(f"PASS: rendered {len(manifest)} figures from project-local frozen artifacts")
    print(TABLE_DIR / "figure_manifest_revised.csv")


if __name__ == "__main__":
    main()
