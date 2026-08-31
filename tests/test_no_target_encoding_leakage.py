"""Tests that local target encoding never sees a row's own held-out label."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.geography import FoldSafeLocalEntryEncoder


def synthetic_data() -> tuple[pd.Series, pd.Series, pd.Series]:
    ids = pd.Series(np.arange(1, 61), name="person_id")
    regions = pd.Series([f"r{value % 6}" for value in ids], name="region")
    target = pd.Series([(value * 7) % 11 < 4 for value in ids], dtype=int, name="target")
    return ids, regions, target


def test_training_row_does_not_encode_its_own_target() -> None:
    ids, regions, target = synthetic_data()
    original = FoldSafeLocalEntryEncoder(alpha=20, n_folds=5, seed=42).fit_transform_train(
        regions, target, ids
    )
    flipped = target.copy()
    flipped.iloc[0] = 1 - flipped.iloc[0]
    changed = FoldSafeLocalEntryEncoder(alpha=20, n_folds=5, seed=42).fit_transform_train(
        regions, flipped, ids
    )
    assert original.iloc[0] == changed.iloc[0]


def test_validation_transform_uses_training_mapping_only() -> None:
    ids, regions, target = synthetic_data()
    encoder = FoldSafeLocalEntryEncoder(alpha=20, n_folds=5, seed=42)
    encoder.fit_transform_train(regions, target, ids)
    first = encoder.transform(pd.Series(["r1", "unseen"]))
    second = encoder.transform(pd.Series(["r1", "unseen"]))
    pd.testing.assert_series_equal(first, second)
    assert first.iloc[1] == target.mean()


def test_oof_encoding_is_complete_and_bounded() -> None:
    ids, regions, target = synthetic_data()
    encoded = FoldSafeLocalEntryEncoder(alpha=20, n_folds=5, seed=42).fit_transform_train(
        regions, target, ids
    )
    assert encoded.notna().all()
    assert encoded.between(0, 1).all()
