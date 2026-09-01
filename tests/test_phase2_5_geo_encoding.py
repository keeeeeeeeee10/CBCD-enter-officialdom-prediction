from __future__ import annotations

import numpy as np
import pandas as pd

from src.geography import FoldSafeLocalEntryEncoder, TrainOnlyRegionalDensity


def sample() -> tuple[pd.Series, pd.Series, pd.Series]:
    regions = pd.Series(["A", "A", "A", "B", "B", "B", "C", "C", "C", "C"])
    target = pd.Series([0, 1, 0, 1, 1, 0, 0, 1, 1, 0])
    ids = pd.Series(np.arange(100, 110))
    return regions, target, ids


def test_training_rows_receive_oof_values_and_not_own_target() -> None:
    regions, target, ids = sample()
    encoder = FoldSafeLocalEntryEncoder(alpha=2, n_folds=5, seed=42)
    original = encoder.fit_transform_train(regions, target, ids)
    changed = target.copy()
    changed.iloc[0] = 1 - changed.iloc[0]
    altered = FoldSafeLocalEntryEncoder(alpha=2, n_folds=5, seed=42).fit_transform_train(regions, changed, ids)
    assert original.iloc[0] == altered.iloc[0]


def test_target_permutation_changes_oof_encoding() -> None:
    regions, target, ids = sample()
    original = FoldSafeLocalEntryEncoder(alpha=2, n_folds=5, seed=42).fit_transform_train(regions, target, ids)
    permuted = FoldSafeLocalEntryEncoder(alpha=2, n_folds=5, seed=42).fit_transform_train(
        regions, target.sample(frac=1, random_state=7).reset_index(drop=True), ids
    )
    assert not np.allclose(original, permuted)


def test_heldout_labels_cannot_change_transform() -> None:
    regions, target, _ = sample()
    encoder = FoldSafeLocalEntryEncoder(alpha=2, n_folds=5, seed=42).fit(regions, target)
    heldout_regions = pd.Series(["A", "UNSEEN", "B"])
    before = encoder.transform(heldout_regions)
    arbitrary_test_labels = pd.Series([1, 0, 1])
    after = encoder.transform(heldout_regions)
    assert arbitrary_test_labels.sum() == 2
    assert np.allclose(before, after)
    assert before.iloc[1] == encoder.global_prior_


def test_density_uses_training_people_only() -> None:
    density = TrainOnlyRegionalDensity().fit(pd.Series(["A", "A", "B"]))
    heldout = density.transform(pd.Series(["A", "C", "C"]))
    assert heldout["train_region_person_count"].tolist() == [2.0, 0.0, 0.0]
