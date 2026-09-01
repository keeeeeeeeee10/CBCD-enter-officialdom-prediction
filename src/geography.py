"""Historical geography utilities and leakage-safe local target encoding."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
import pandas as pd


EARTH_RADIUS_KM = 6371.0088
MISSING_REGION = "__MISSING__"


def haversine_km(
    latitude: pd.Series | np.ndarray,
    longitude: pd.Series | np.ndarray,
    capital_latitude: pd.Series | np.ndarray,
    capital_longitude: pd.Series | np.ndarray,
) -> np.ndarray:
    lat1 = np.radians(np.asarray(latitude, dtype=float))
    lon1 = np.radians(np.asarray(longitude, dtype=float))
    lat2 = np.radians(np.asarray(capital_latitude, dtype=float))
    lon2 = np.radians(np.asarray(capital_longitude, dtype=float))
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    a = np.sin(delta_lat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(delta_lon / 2.0) ** 2
    return 2.0 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))


def assign_capitals(frame: pd.DataFrame, capital_config: dict[str, object]) -> pd.DataFrame:
    result = pd.DataFrame(index=frame.index, columns=["capital_name", "capital_latitude", "capital_longitude"], dtype=object)
    for dynasty, definition in capital_config["dynasties"].items():
        dynasty_mask = frame["dynasty_name"].eq(dynasty)
        capitals = definition["capitals"]
        canonical = next(item for item in capitals if item.get("canonical_when_year_missing", False))
        result.loc[dynasty_mask, "capital_name"] = canonical["capital_name"]
        result.loc[dynasty_mask, "capital_latitude"] = float(canonical["latitude"])
        result.loc[dynasty_mask, "capital_longitude"] = float(canonical["longitude"])
        for item in capitals:
            year_mask = dynasty_mask & frame["safe_birth_year"].between(
                float(item["valid_start"]), float(item["valid_end"]), inclusive="both"
            )
            result.loc[year_mask, "capital_name"] = item["capital_name"]
            result.loc[year_mask, "capital_latitude"] = float(item["latitude"])
            result.loc[year_mask, "capital_longitude"] = float(item["longitude"])
    result["capital_latitude"] = pd.to_numeric(result["capital_latitude"], errors="coerce")
    result["capital_longitude"] = pd.to_numeric(result["capital_longitude"], errors="coerce")
    return result


def _stable_fold(person_id: object, seed: int, n_folds: int) -> int:
    digest = hashlib.sha256(f"{seed}|{person_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "little") % n_folds


@dataclass
class FoldSafeLocalEntryEncoder:
    alpha: float = 20.0
    n_folds: int = 5
    seed: int = 42

    def _regions(self, values: pd.Series) -> pd.Series:
        return values.astype("string").fillna(MISSING_REGION).astype(str)

    def fit(self, regions: pd.Series, target: pd.Series) -> "FoldSafeLocalEntryEncoder":
        region = self._regions(regions)
        y = pd.to_numeric(target, errors="raise").astype(float)
        self.global_prior_ = float(y.mean())
        stats = pd.DataFrame({"region": region, "target": y}).groupby("region")["target"].agg(["sum", "count"])
        self.mapping_ = ((stats["sum"] + self.alpha * self.global_prior_) / (stats["count"] + self.alpha)).to_dict()
        return self

    def transform(self, regions: pd.Series) -> pd.Series:
        if not hasattr(self, "mapping_"):
            raise RuntimeError("FoldSafeLocalEntryEncoder must be fitted before transform")
        region = self._regions(regions)
        return region.map(self.mapping_).fillna(self.global_prior_).astype(float)

    def fit_transform_train(
        self,
        regions: pd.Series,
        target: pd.Series,
        person_ids: pd.Series,
    ) -> pd.Series:
        region = self._regions(regions).reset_index(drop=True)
        y = pd.to_numeric(target, errors="raise").astype(float).reset_index(drop=True)
        ids = person_ids.reset_index(drop=True)
        folds = ids.map(lambda value: _stable_fold(value, self.seed, self.n_folds)).astype(int)
        encoded = pd.Series(index=region.index, dtype=float)
        for fold in range(self.n_folds):
            held_out = folds.eq(fold)
            fit_mask = ~held_out
            fold_prior = float(y.loc[fit_mask].mean())
            stats = pd.DataFrame({"region": region.loc[fit_mask], "target": y.loc[fit_mask]}).groupby("region")["target"].agg(["sum", "count"])
            mapping = ((stats["sum"] + self.alpha * fold_prior) / (stats["count"] + self.alpha)).to_dict()
            encoded.loc[held_out] = region.loc[held_out].map(mapping).fillna(fold_prior)
        self.fit(region, y)
        encoded.index = regions.index
        return encoded.astype(float)


@dataclass
class TrainOnlyRegionalDensity:
    """Count training people by region and map without reading held-out rows."""

    def _regions(self, values: pd.Series) -> pd.Series:
        return values.astype("string").fillna(MISSING_REGION).astype(str)

    def fit(self, regions: pd.Series) -> "TrainOnlyRegionalDensity":
        keys = self._regions(regions)
        self.mapping_ = keys.value_counts(dropna=False).astype(float).to_dict()
        return self

    def transform(self, regions: pd.Series) -> pd.DataFrame:
        if not hasattr(self, "mapping_"):
            raise RuntimeError("TrainOnlyRegionalDensity must be fitted before transform")
        count = self._regions(regions).map(self.mapping_).fillna(0.0).astype(float)
        return pd.DataFrame(
            {
                "train_region_person_count": count,
                "train_region_log_density": np.log1p(count),
            },
            index=regions.index,
        )
