#!/usr/bin/env python3
"""Recover retained methods/operating parameters and summarize frozen supports."""

from __future__ import annotations

import hashlib
import inspect
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.feature_builders import load_yaml
from src.geography import FoldSafeLocalEntryEncoder, MISSING_REGION, _stable_fold


OUT = ROOT / "outputs/phase3_1_1"
DOCS = ROOT / "docs/phase3_1_1"
TABLES = OUT / "tables"
METHODS = OUT / "methods"
FINAL_TABLES = ROOT / "paper/final/tables"
POP_ORDER = {"Global": 0, "Song": 1, "Ming": 2}
MODEL_ORDER = {"Logistic M6": 0, "H_STRUCT": 1, "D5_MAIN": 2, "D6_UPPER": 3}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_local_prior_spec() -> None:
    config = load_yaml(ROOT / "configs/phase2_6_features.yaml")
    model_config = load_yaml(ROOT / "configs/phase2_6_models.yaml")
    source = ROOT / "src/geography.py"
    phase26 = ROOT / "src/phase26.py"
    spec = {
        "schema_version": 1,
        "status": "RECOVERED_FROM_EXECUTED_CODE_AND_FROZEN_CONFIG",
        "feature_name": "local_target_prior",
        "target": "target_entry_v1 (observed ENTRY_DATA record presence E)",
        "region_key": str(config["region_key"]),
        "grouping": {
            "level": "exact addr_id key",
            "hierarchical": False,
            "minimum_group_size": None,
            "minimum_group_size_status": "NOT_USED",
        },
        "smoothing": {
            "alpha": float(config["local_prior_alpha"]),
            "formula": "(s_r + alpha * mu) / (n_r + alpha)",
            "s_r": "sum of target_entry_v1 in the fitting rows for region r",
            "n_r": "number of fitting rows for region r",
            "mu": "mean target_entry_v1 in the fitting rows",
        },
        "training_encoding": {
            "method": "deterministic out-of-fold target encoding",
            "folds": int(config["local_prior_oof_folds"]),
            "seed": int(model_config["canonical_seed"]),
            "fold_assignment": "int.from_bytes(SHA256(f'{seed}|{person_id}')[:8], 'little') mod n_folds",
            "leakage_rule": "the encoded value for a training row is computed only from rows outside that row's fold",
            "unseen_in_fold_fallback": "out-of-fold target mean mu_-f",
            "post_oof_fit": "after OOF values are produced, the encoder is fitted on the complete training partition for forward transforms",
        },
        "validation_test_encoding": {
            "labels_read": False,
            "mapping_source": "complete training partition only",
            "unseen_region_fallback": "complete-training target mean",
        },
        "missing_geography": {
            "conversion": f"missing addr_id is converted to the literal group {MISSING_REGION}",
            "treatment": "a smoothed region group when observed in fitting rows; otherwise the relevant global fallback",
            "separate_missing_indicator_added_by_encoder": False,
        },
        "population_rules": {
            "fitted_separately": ["Global", "Song", "Ming"],
            "order": ["Global", "Song", "Ming"],
            "rule": "population filtering precedes partitioning and encoder fitting",
        },
        "split_and_shift_rules": {
            "primary": "fit on the population-specific frozen primary training partition; transform its validation and test partitions",
            "matched_random": "refit from the matched-random training partition only",
            "matched_spatial": "refit from the matched-spatial training partition only; validation/test addr_id values absent from training use the training global mean",
            "no_cross_protocol_mapping_reuse": True,
        },
        "not_documented_or_not_used": {
            "hierarchical_backoff": "NOT_USED",
            "minimum_count_pooling": "NOT_USED",
            "coordinate_nearest_neighbor_backoff": "NOT_USED",
            "external_geographic_prior": "NOT_USED",
        },
        "provenance": {
            "implementation": "src/geography.py:FoldSafeLocalEntryEncoder",
            "caller": "src/phase26.py:prepare_phase26_data",
            "config": "configs/phase2_6_features.yaml",
            "implementation_sha256": sha256(source),
            "caller_sha256": sha256(phase26),
            "class_source_sha256": hashlib.sha256(inspect.getsource(FoldSafeLocalEntryEncoder).encode()).hexdigest(),
        },
    }
    METHODS.mkdir(parents=True, exist_ok=True)
    (METHODS / "local_target_prior_spec.json").write_text(
        json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    markdown = f"""# `local_target_prior` implementation specification

Status: **recovered from the executed implementation and frozen configuration**. No method was reconstructed from model performance.

## Exact estimator

The feature groups people by the exact `addr_id` key. For a fitting sample with regional positive count $s_r$, regional sample size $n_r$, fitting-sample target mean $\\mu$, and frozen smoothing strength $\\alpha={spec['smoothing']['alpha']:.1f}$,

$$
\\widehat p_r=\\frac{{s_r+\\alpha\\mu}}{{n_r+\\alpha}}.
$$

There is no hierarchical geographic backoff and no minimum group-size rule. Missing `addr_id` is converted to the literal `{MISSING_REGION}` group. If that group has fitting observations it receives the same smoothed estimate; otherwise it uses the relevant fitting-sample mean.

## Leakage boundary

Training values use {spec['training_encoding']['folds']}-fold deterministic out-of-fold encoding. Fold membership is the first eight bytes of `SHA256("seed|person_id")`, interpreted as a little-endian integer modulo {spec['training_encoding']['folds']}; the canonical seed is {spec['training_encoding']['seed']}. A training row's label and every label in its held-out fold are excluded from that row's encoded value. A region unseen outside the held-out fold falls back to the out-of-fold mean $\\mu_{{-f}}$.

After producing all training OOF values, the encoder is fitted once on the complete training partition. Validation and test transformations accept region keys only and never accept their labels. An unseen `addr_id` falls back to the complete-training target mean.

## Population and shift behavior

The dataset is filtered to Global, Song, or Ming before the split is materialized, so each population receives a separate encoder. Primary, matched-random, and matched-spatial runs each refit the encoder from that protocol's training partition; mappings are not shared across protocols. Under matched-spatial shift, an `addr_id` absent from spatial training therefore receives that population/protocol training mean.

## Provenance

- Implementation: `src/geography.py:FoldSafeLocalEntryEncoder`
- Executed caller: `src/phase26.py:prepare_phase26_data`
- Frozen configuration: `configs/phase2_6_features.yaml`
- Unsupported additions explicitly absent: hierarchical pooling, minimum-count pooling, coordinate-nearest backoff, and external priors.
"""
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "local_target_prior_spec.md").write_text(markdown, encoding="utf-8")


def write_operating_parameters() -> None:
    metrics = pd.read_csv(ROOT / "outputs/phase2_6/tables/final_model_metrics.csv")
    calibration = pd.read_csv(ROOT / "outputs/phase2_6/tables/final_model_calibration.csv")
    rows: list[dict[str, object]] = []
    logistic = pd.read_csv(ROOT / "outputs/phase2/tables/model_metrics.csv")
    logistic = logistic.loc[
        logistic["algorithm"].eq("LogisticRegression")
        & logistic["model_variant"].eq("balanced")
        & logistic["feature_set"].eq("M6")
        & logistic["threshold_source"].eq("validation_balanced_accuracy")
    ]
    for row in logistic.itertuples(index=False):
        rows.append({
            "population": row.population,
            "model_id": "Logistic M6",
            "selected_weighting_scheme": "class_weight=balanced",
            "numeric_class_weights": "NOT_RETAINED",
            "threshold": float(row.threshold),
            "threshold_objective": "validation balanced accuracy",
            "training_objective": "binary logistic loss; lbfgs",
            "selection_objective": "frozen linear baseline",
            "calibrator": "NOT_RETAINED",
            "sigmoid_coefficient": "NOT_RETAINED",
            "sigmoid_intercept": "NOT_RETAINED",
        })
    merged = metrics.merge(calibration, on=["population", "model_id"], validate="one_to_one")
    for row in merged.itertuples(index=False):
        rows.append({
            "population": row.population,
            "model_id": row.model_id,
            "selected_weighting_scheme": "auto_class_weights=Balanced" if row.model_variant == "balanced" else "unweighted",
            "numeric_class_weights": "NOT_RETAINED",
            "threshold": float(row.frozen_threshold),
            "threshold_objective": "validation balanced accuracy",
            "training_objective": "CatBoost Logloss",
            "selection_objective": "validation ROC-AUC, then lower LogLoss",
            "calibrator": "validation-fitted sigmoid on raw-logit score",
            "sigmoid_coefficient": float(row.sigmoid_coefficient),
            "sigmoid_intercept": float(row.sigmoid_intercept),
        })
    frame = pd.DataFrame(rows)
    frame["population_order"] = frame["population"].map(POP_ORDER)
    frame["model_order"] = frame["model_id"].map(MODEL_ORDER)
    frame = frame.sort_values(["population_order", "model_order"]).drop(columns=["population_order", "model_order"])
    TABLES.mkdir(parents=True, exist_ok=True)
    frame.to_csv(TABLES / "operating_parameters.csv", index=False)

    def cal_text(row: pd.Series) -> str:
        if row["sigmoid_coefficient"] == "NOT_RETAINED":
            return "NOT\\_RETAINED"
        return f"$a={float(row['sigmoid_coefficient']):.6f}$; $b={float(row['sigmoid_intercept']):.6f}$"

    lines = [
        "\\begingroup",
        "\\setlength{\\tabcolsep}{4pt}",
        "\\begin{longtable}{>{\\raggedright\\arraybackslash}p{1.55cm}>{\\raggedright\\arraybackslash}p{1.75cm}>{\\raggedright\\arraybackslash}p{3.30cm}>{\\raggedright\\arraybackslash}p{1.45cm}>{\\raggedright\\arraybackslash}p{4.00cm}>{\\raggedright\\arraybackslash}p{3.90cm}}",
        "\\caption{Retained operating points for the frozen primary models. Numeric class weights were not serialized; the retained weighting scheme is reported without reconstruction. The sigmoid is $\\sigma(a\\,\\mathrm{logit}(p)+b)$ and was fitted only on validation predictions.}\\label{tab:app-operating}\\\\",
        "\\toprule",
        'Population & Model & Selected weighting & Threshold & Objective / selection & Calibrator parameters \\\\',
        "\\midrule", "\\endfirsthead", "\\toprule",
        'Population & Model & Selected weighting & Threshold & Objective / selection & Calibrator parameters \\\\',
        "\\midrule", "\\endhead",
    ]
    for _, row in frame.iterrows():
        model = str(row["model_id"]).replace("_", "\\_")
        scheme = str(row["selected_weighting_scheme"])
        weighting = (
            "Balanced (CatBoost); numeric weights NOT\\_RETAINED"
            if scheme == "auto_class_weights=Balanced"
            else "balanced (logistic); numeric weights NOT\\_RETAINED"
            if scheme == "class_weight=balanced"
            else scheme.replace("_", "\\_") + "; numeric weights NOT\\_RETAINED"
        )
        objective = str(row["training_objective"]) + "; " + str(row["selection_objective"])
        lines.append(f"{row['population']} & {model} & {weighting} & {float(row['threshold']):.2f} & {objective} & {cal_text(row)} \\\\")
    lines += ["\\bottomrule", "\\end{longtable}", "\\endgroup"]
    FINAL_TABLES.mkdir(parents=True, exist_ok=True)
    (FINAL_TABLES / "tableA1b_operating_parameters.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_support_summaries() -> None:
    metrics = pd.read_csv(ROOT / "outputs/phase2_6/tables/final_model_metrics.csv")
    primary = metrics.loc[metrics["model_id"].eq("D5_MAIN")].copy()
    split_rows = []
    for row in primary.sort_values("population", key=lambda s: s.map(POP_ORDER)).itertuples(index=False):
        for split, n, rate in [
            ("train", row.n_train, None),
            ("validation", row.n_validation, None),
            ("test", row.n_test, row.test_positive_rate),
        ]:
            split_rows.append({
                "population": row.population, "protocol": "frozen_primary", "split": split,
                "n_people": int(n), "positive_rate": rate,
                "source_artifact": "outputs/phase2_6/tables/final_model_metrics.csv",
                "note": "Population-specific D5_MAIN support; train/validation prevalence is not retained in this artifact" if rate is None else "Population-specific D5_MAIN test support",
            })
    pd.DataFrame(split_rows).to_csv(TABLES / "split_support_summary.csv", index=False)

    shift_rows: list[dict[str, object]] = []
    for name in ["matched_random", "matched_spatial"]:
        source = ROOT / f"outputs/phase2_6/tables/{name}_split_summary.csv"
        frame = pd.read_csv(source)
        for row in frame.itertuples(index=False):
            shift_rows.append({
                "population": row.population, "protocol": name, "split": row.split,
                "n_people": int(row.n_people), "positive_rate": float(row.positive_rate),
                "n_groups": int(row.n_spatial_groups),
                "group_definition": "dynasty_code x historical prefecture_id",
                "status": "RUN", "source_artifact": source.relative_to(ROOT).as_posix(),
                "note": "identical reliable-prefecture population for random/spatial comparison",
            })

    people = pd.read_parquet(ROOT / "data/interim/person_modeling_population.parquet", columns=["person_id", "dynasty", "target_entry_v1"])
    groups = pd.read_parquet(ROOT / "data/interim/person_family_groups.parquet", columns=["person_id", "family_group_id"])
    split = pd.read_parquet(ROOT / "data/splits/split_family_group_robustness.parquet")
    family = split.merge(groups, on="person_id", validate="one_to_one").merge(people, on="person_id", validate="one_to_one")
    for population in ["Global", "Ming"]:
        current = family if population == "Global" else family.loc[family["dynasty"].eq(population)]
        for split_name, block in current.groupby("split", sort=True):
            shift_rows.append({
                "population": population, "protocol": "family_group_holdout_F2_only", "split": split_name,
                "n_people": len(block), "positive_rate": float(block["target_entry_v1"].mean()),
                "n_groups": int(block["family_group_id"].nunique()),
                "group_definition": "core blood-family connected group",
                "status": "RUN", "source_artifact": "data/splits/split_family_group_robustness.parquet",
                "note": "Performance evaluated only for F2 structural comparator",
            })

    safe = pd.read_csv(ROOT / "outputs/phase3/tables/safe_temporal_split_context.csv")
    for row in safe.itertuples(index=False):
        shift_rows.append({
            "population": "Global", "protocol": "SAFE_temporal", "split": row.split,
            "n_people": int(row.n_people), "positive_rate": float(row.positive_prevalence),
            "n_groups": None, "group_definition": "whole-year SAFE birth anchor",
            "status": "SPLIT_ONLY_NO_LOCKED_PERFORMANCE",
            "source_artifact": "outputs/phase3/tables/safe_temporal_split_context.csv",
            "note": "No locked-model temporal performance artifact",
        })
    source_status = json.loads((ROOT / "outputs/phase3/tables/source_holdout_status.json").read_text())
    shift_rows.append({
        "population": "Global", "protocol": "source_connected_components", "split": "eligible",
        "n_people": int(source_status["eligible_people"]), "positive_rate": None,
        "n_groups": int(source_status["source_groups"]),
        "group_definition": source_status["grouping_protocol"], "status": source_status["status"],
        "source_artifact": "outputs/phase3/tables/source_holdout_status.json",
        "note": f"largest component={source_status['largest_group_people']} ({source_status['largest_group_fraction']:.6%})",
    })
    shifts = pd.DataFrame(shift_rows)
    shifts["population_order"] = shifts["population"].map({"Global": 0, "Song": 1, "Ming": 2}).fillna(9)
    shifts = shifts.sort_values(["protocol", "population_order", "split"]).drop(columns="population_order")
    shifts.to_csv(TABLES / "shift_support_summary.csv", index=False)


def write_course_alignment() -> None:
    (DOCS / "course_task_alignment.md").write_text(
        """# Course-task alignment

This study combines open-ended exploratory analysis of dynastic, gender, ENTRY-pathway, geographic, and kin-observability patterns with predictive modeling of ENTRY-record presence.

| Course task | Manuscript evidence | Boundary |
| --- | --- | --- |
| Open-ended exploratory data mining | Dynasty and gender coverage, ENTRY-pathway composition, address decomposition, family observability/topology/capital decomposition | Describes CBDB-covered records, not the historical Chinese population |
| Predictive modeling | Frozen Logistic M6, H_STRUCT, D5_MAIN and D6_UPPER primary-test results | Predicts observed ENTRY-record presence E, not latent true entry T |
| Robustness and distribution shift | Grouped ablations, five-seed checks, F2-only whole-family holdout, matched-support spatial shift | D5_MAIN was not directly evaluated under whole-family grouping; SAFE and source protocols lack locked performance |
| Reproducibility | Frozen release identifier, split/model/prediction hashes, figure source tables, exact method specifications and release archives | Raw CBDB SQLite and large intermediates are not redistributed |

The assignment brief reports approximately 515,488 people, whereas the verified release used in this study contains 661,124 BIOG_MAIN person records. CBDB counts are release-specific; all results here refer only to cbdb_20260829.sqlite3.
""",
        encoding="utf-8",
    )


def main() -> None:
    write_local_prior_spec()
    write_operating_parameters()
    write_support_summaries()
    write_course_alignment()
    print("PASS: method specification, operating points, and frozen support summaries written")


if __name__ == "__main__":
    main()
