"""Shared helpers for Phase 2 feature construction."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: str | Path) -> dict[str, Any]:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = PROJECT_ROOT / resolved
    with resolved.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a YAML mapping: {resolved}")
    return value


def atomic_to_parquet(frame: pd.DataFrame, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    frame.to_parquet(temporary, index=False, compression="zstd")
    os.replace(temporary, output)


def atomic_to_csv(frame: pd.DataFrame, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    frame.to_csv(temporary, index=False)
    os.replace(temporary, output)


def ensure_unique_people(frame: pd.DataFrame, expected: int = 661_124) -> None:
    if len(frame) != expected:
        raise RuntimeError(f"Expected {expected:,} people, found {len(frame):,}")
    if frame["person_id"].isna().any() or frame["person_id"].duplicated().any():
        raise RuntimeError("person_id must be nonmissing and unique")


def resolve_feature_set(registry: dict[str, Any], name: str) -> tuple[list[str], list[str]]:
    definitions = registry["feature_sets"]
    if name not in definitions:
        raise KeyError(f"Unknown Phase 2 feature set: {name}")
    definition = definitions[name]
    categorical: list[str] = []
    numeric: list[str] = []
    for included in definition.get("include", []):
        child_categorical, child_numeric = resolve_feature_set(registry, included)
        categorical.extend(child_categorical)
        numeric.extend(child_numeric)
    categorical.extend(definition.get("categorical", []))
    numeric.extend(definition.get("numeric", []))
    return list(dict.fromkeys(categorical)), list(dict.fromkeys(numeric))


def population_mask(frame: pd.DataFrame, population: str) -> pd.Series:
    if population == "Global":
        return pd.Series(True, index=frame.index)
    return frame["dynasty_name"].eq(population)
