from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def test_spatial_groups_never_cross_partitions() -> None:
    for population in ["global", "song", "ming"]:
        frame = pd.read_parquet(ROOT / f"data/phase2_5/splits/split_spatial_group_{population}.parquet")
        assert not frame["person_id"].duplicated().any()
        assert not frame["spatial_group_id"].isna().any()
        assert frame.groupby("spatial_group_id")["split"].nunique().max() == 1


def test_spatial_overlap_audit_passes() -> None:
    audit = json.loads((ROOT / "outputs/phase2_5/tables/spatial_split_overlap_check.json").read_text())
    assert audit["status"] == "PASS"
    for details in audit["populations"].values():
        assert details["status"] == "PASS"
        assert not any(details["intersections"].values())
