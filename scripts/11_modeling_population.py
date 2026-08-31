#!/usr/bin/env python3
"""Create explicit dynasty populations and quantify documentation-intensity bias."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import configured_path, load_config
from src.phase15 import MAJOR_DYNASTIES, clean_year_series
from src.utils import setup_logging


DOCUMENTATION_COLUMNS = [
    "has_address",
    "has_kin_record",
    "has_assoc_record",
    "has_status_record",
    "has_text_record",
    "has_institution_record",
]


def population_summary(frame: pd.DataFrame, name: str) -> dict[str, object]:
    n = len(frame)
    return {
        "population": name,
        "n_people": n,
        "entry_v1_positive": int(frame["target_entry_v1"].sum()),
        "entry_v1_rate": float(frame["target_entry_v1"].mean()) if n else 0.0,
        "entry_v2a_positive": int(frame["target_entry_v2a"].sum()),
        "entry_v2a_rate": float(frame["target_entry_v2a"].mean()) if n else 0.0,
        "entry_v2b_positive": int(frame["target_entry_v2b"].sum()),
        "entry_v2b_rate": float(frame["target_entry_v2b"].mean()) if n else 0.0,
        "posting_positive": int(frame["target_posting"].sum()),
        "posting_rate": float(frame["target_posting"].mean()) if n else 0.0,
        "kin_coverage": float(frame["has_kinship"].mean()) if n else 0.0,
        "address_coverage": float(frame["has_geography"].mean()) if n else 0.0,
        "assoc_coverage": float(frame["has_association"].mean()) if n else 0.0,
        "safe_time_anchor_coverage": float(frame["has_safe_time_anchor"].mean()) if n else 0.0,
        "basic_time_coverage": float(frame["has_basic_time"].mean()) if n else 0.0,
        "mean_documentation_intensity": float(frame["documentation_intensity"].mean()) if n else 0.0,
    }


def main() -> int:
    config = load_config()
    interim_dir = configured_path(config, "paths", "interim")
    processed_dir = configured_path(config, "paths", "processed")
    tables_dir = configured_path(config, "paths", "tables")
    figures_dir = configured_path(config, "paths", "figures")
    logger = setup_logging("population", configured_path(config, "paths", "logs") / "modeling_population.log")

    base_columns = [
        "person_id", "gender_code", "gender", "birth_year", "death_year", "index_year",
        "dynasty_code", "dynasty", "dynasty_chn",
        *DOCUMENTATION_COLUMNS,
        "n_kin_records", "n_assoc_records", "n_address_records", "n_status_records",
        "n_text_records", "n_institution_records",
    ]
    base = pd.read_parquet(processed_dir / "person_base_v0.parquet", columns=base_columns)
    targets = pd.read_parquet(interim_dir / "person_targets_v1_v2.parquet")
    safe_time = pd.read_parquet(interim_dir / "person_safe_time_anchor.parquet", columns=[
        "person_id", "safe_index_year", "safe_index_year_available", "index_year_leakage_class",
    ])
    population = base.merge(targets, on="person_id", how="left", validate="one_to_one").merge(safe_time, on="person_id", how="left", validate="one_to_one")

    population["population_global"] = 1
    for dynasty in MAJOR_DYNASTIES:
        population[f"population_{dynasty.lower()}"] = population["dynasty"].eq(dynasty).astype("int8")
    population["has_safe_time_anchor"] = population["safe_index_year_available"].fillna(0).astype("int8")
    valid_birth = clean_year_series(population["birth_year"], config).notna()
    population["has_basic_time"] = (valid_birth | population["has_safe_time_anchor"].eq(1)).astype("int8")
    population["has_geography"] = population["has_address"].astype("int8")
    population["has_kinship"] = population["has_kin_record"].astype("int8")
    population["has_association"] = population["has_assoc_record"].astype("int8")
    population["n_known_record_domains"] = population[DOCUMENTATION_COLUMNS].sum(axis=1).astype("int8")
    population["documentation_intensity"] = population["n_known_record_domains"]

    output_columns = [
        "person_id", "dynasty_code", "dynasty", "gender_code", "gender", "birth_year", "death_year", "index_year",
        "safe_index_year", "index_year_leakage_class",
        "target_entry_v1", "target_entry_v2a", "target_entry_v2b", "target_posting",
        "population_global", "population_tang", "population_song", "population_yuan", "population_ming", "population_qing",
        "has_basic_time", "has_safe_time_anchor", "has_geography", "has_kinship", "has_association",
        *DOCUMENTATION_COLUMNS, "n_known_record_domains", "documentation_intensity",
        "n_kin_records", "n_assoc_records", "n_address_records", "n_status_records", "n_text_records", "n_institution_records",
    ]
    population[output_columns].to_parquet(interim_dir / "person_modeling_population.parquet", index=False, compression="zstd")

    summary_rows = [population_summary(population, "Global")]
    for dynasty in MAJOR_DYNASTIES:
        summary_rows.append(population_summary(population[population["dynasty"].eq(dynasty)], dynasty))
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(tables_dir / "modeling_population_summary.csv", index=False)

    bias_rows = []
    subsets = {"Global": population}
    subsets.update({dynasty: population[population["dynasty"].eq(dynasty)] for dynasty in ("Song", "Ming", "Qing")})
    for name, frame in subsets.items():
        grouped = frame.groupby("documentation_intensity").agg(
            n_people=("person_id", "size"),
            entry_v1_positive=("target_entry_v1", "sum"),
            entry_v1_rate=("target_entry_v1", "mean"),
            posting_positive=("target_posting", "sum"),
            posting_rate=("target_posting", "mean"),
        ).reset_index()
        grouped.insert(0, "population", name)
        bias_rows.append(grouped)
    bias = pd.concat(bias_rows, ignore_index=True)
    bias.to_csv(tables_dir / "documentation_bias_summary.csv", index=False)

    plot_data = bias[bias["n_people"] >= 30]
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(9, 6))
    sns.lineplot(data=plot_data, x="documentation_intensity", y="entry_v1_rate", hue="population", marker="o")
    plt.title("Documentation-domain intensity vs ENTRY record rate")
    plt.xlabel("Known non-target record domains (0–6)")
    plt.ylabel("Share with current CBDB ENTRY_DATA record")
    plt.ylim(0, min(1.0, max(0.1, float(plot_data["entry_v1_rate"].max()) * 1.1)))
    plt.tight_layout()
    plt.savefig(figures_dir / "documentation_intensity_vs_entry.png", dpi=int(config["analysis"]["figure_dpi"]), bbox_inches="tight")
    plt.close()
    logger.info("Modeling populations complete: %d people, documentation intensity 0-%d", len(population), int(population["documentation_intensity"].max()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

