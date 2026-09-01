#!/usr/bin/env python3
"""Prepare revised LaTeX tables and non-destructive SHAP label artifacts."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OLD_TABLES = ROOT / "paper" / "tables"
NEW_TABLES = ROOT / "paper" / "revised" / "tables"
OUT_TABLES = ROOT / "outputs" / "phase3_1" / "tables"


def copy_tables() -> None:
    NEW_TABLES.mkdir(parents=True, exist_ok=True)
    for source in sorted(OLD_TABLES.glob("*.tex")):
        shutil.copy2(source, NEW_TABLES / source.name)

    performance = (NEW_TABLES / "table3_performance.tex").read_text(encoding="utf-8")
    performance = performance.replace("LogLoss & Brier & Cal. ECE", "Raw LogLoss & Raw Brier & Validation-calibrated ECE")
    performance = performance.replace(
        "Frozen primary-test performance. ECE is after a validation-fitted sigmoid; the earlier logistic artifact did not retain a directly comparable calibrated ECE.",
        "Frozen primary-test performance. Log loss and Brier score use raw model probabilities; ECE uses probabilities from a sigmoid calibrator fitted on validation predictions only. The logistic artifact did not retain a directly comparable calibrated ECE.",
    )
    (NEW_TABLES / "table3_performance.tex").write_text(performance, encoding="utf-8")

    ablation = (NEW_TABLES / "table4_ablation.tex").read_text(encoding="utf-8")
    ablation = ablation.replace(
        "Physical geography & +0.0000 & [-0.0002, 0.0003] & -0.0003 & [-0.0016, -0.0004]",
        "Physical geography & +0.0000 & -- & -0.0003 & --",
    )
    ablation = ablation.replace(
        "Intervals are 500-resample paired bootstrap intervals where the exact paired predictions were retained; dashes identify contrasts without a retained exact prediction pair, not zero uncertainty.",
        "Point estimates are frozen conditional increments. Intervals are 500-resample paired bootstrap intervals only where the exact paired prediction pair was retained. Dashes, including Physical Geography, mean that no valid exact-pair interval is available, not zero uncertainty.",
    )
    (NEW_TABLES / "table4_ablation.tex").write_text(ablation, encoding="utf-8")

    appendix_path = NEW_TABLES / "tableA3_full_ablation.tex"
    appendix_lines = []
    for line in appendix_path.read_text(encoding="utf-8").splitlines():
        if "& Physical geography & A3 - A2 &" in line:
            fields = line.split("&")
            fields[4] = " -- "
            fields[6] = " -- \\\\"
            line = "&".join(fields)
        appendix_lines.append(line)
    appendix_path.write_text("\n".join(appendix_lines) + "\n", encoding="utf-8")


def revise_shap_labels() -> None:
    OUT_TABLES.mkdir(parents=True, exist_ok=True)
    sources = {
        "shap_group_summary_revised.csv": ROOT / "outputs/phase2_6/shap/shap_group_summary.csv",
        "shap_feature_summary_revised.csv": ROOT / "outputs/phase2_6/shap/shap_feature_summary.csv",
        "shap_direction_summary_revised.csv": ROOT / "outputs/phase2_6/shap/shap_direction_summary.csv",
    }
    for name, source in sources.items():
        frame = pd.read_csv(source)
        if "feature_group" not in frame.columns:
            raise RuntimeError(f"Missing feature_group in {source}")
        affected = frame["feature_group"].eq("other")
        if name != "shap_group_summary_revised.csv" and affected.any():
            features = set(frame.loc[affected, "feature"].astype(str))
            if features != {"dynasty_name"}:
                raise RuntimeError(f"The 'other' group contains unexpected features: {features}")
        frame.loc[affected, "feature_group"] = "historical_regime"
        if frame["feature_group"].eq("other").any():
            raise RuntimeError("Ambiguous SHAP group label survived replacement")
        frame.to_csv(OUT_TABLES / name, index=False)

    registry = {
        "schema_version": 1,
        "status": "RELABELED_WITHOUT_RETRAINING",
        "source_feature": "dynasty_name",
        "old_group": "other",
        "canonical_group": "historical_regime",
        "scientific_boundary": "A display and aggregation-label correction only; SHAP values, models, samples, and additivity checks are unchanged.",
    }
    (OUT_TABLES / "shap_group_registry_revised.json").write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")


def validate_manuscript_sources() -> None:
    required = [
        ROOT / "paper/revised/main_author_revised.tex",
        ROOT / "paper/revised/main_anonymous_revised.tex",
        ROOT / "paper/revised/main_body_revised.tex",
        ROOT / "paper/revised/references_revised.bib",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(f"Missing revised manuscript sources: {missing}")
    body = (ROOT / "paper/revised/main_body_revised.tex").read_text(encoding="utf-8")
    phrases = [
        "E, P, and T are not semantically equivalent",
        "Full-coverage source-group confirmation was infeasible under the prespecified connected-component protocol.",
        "Raw LogLoss", "Validation-calibrated ECE", "historical_regime",
        "Data Mining Course Project", "\\FloatBarrier\n\\clearpage\n\\label{mainend}",
    ]
    absent = [phrase for phrase in phrases if phrase not in body and phrase not in (NEW_TABLES / "table3_performance.tex").read_text(encoding="utf-8")]
    if absent:
        raise RuntimeError(f"Required manuscript safeguards are absent: {absent}")


def main() -> None:
    copy_tables()
    revise_shap_labels()
    validate_manuscript_sources()
    print("PASS: revised tables, SHAP labels, and manuscript safeguards prepared")


if __name__ == "__main__":
    main()
