from __future__ import annotations

import pandas as pd

from src.family import build_inductive_family_features


def test_inductive_family_reads_training_relatives_only() -> None:
    edges = pd.DataFrame({
        "person_id": [1, 1, 4],
        "kin_id": [2, 3, 2],
        "generation_class": ["parent_generation", "ancestor", "parent_generation"],
        "specific_relation": ["father", "paternal_grandfather", "father"],
    })
    outcomes = pd.DataFrame({"person_id": [1, 2, 3, 4], "relative_outcome": [1, 0, 1, 1]})
    result = build_inductive_family_features(pd.Series([1]), edges, {2, 4}, outcomes).iloc[0]
    assert result["ind_father_outcome"] == 0
    assert pd.isna(result["ind_paternal_grandfather_outcome"])
    assert result["ind_n_observed_older_kin"] == 1
    assert result["ind_n_positive_older_kin"] == 0
    assert result["ind_any_positive"] == 0


def test_heldout_relative_outcome_change_has_no_effect() -> None:
    edges = pd.DataFrame({
        "person_id": [1, 1], "kin_id": [2, 3],
        "generation_class": ["parent_generation", "ancestor"],
        "specific_relation": ["father", "paternal_grandfather"],
    })
    outcomes_a = pd.DataFrame({"person_id": [1, 2, 3], "relative_outcome": [1, 0, 0]})
    outcomes_b = outcomes_a.copy()
    outcomes_b.loc[outcomes_b["person_id"].eq(3), "relative_outcome"] = 1
    a = build_inductive_family_features(pd.Series([1]), edges, {2}, outcomes_a)
    b = build_inductive_family_features(pd.Series([1]), edges, {2}, outcomes_b)
    pd.testing.assert_frame_equal(a, b)


def test_inductive_family_rejects_self_edge() -> None:
    edges = pd.DataFrame({
        "person_id": [1], "kin_id": [1], "generation_class": ["parent_generation"],
        "specific_relation": ["father"],
    })
    outcomes = pd.DataFrame({"person_id": [1], "relative_outcome": [1]})
    try:
        build_inductive_family_features(pd.Series([1]), edges, {1}, outcomes)
    except ValueError as error:
        assert "self" in str(error)
    else:
        raise AssertionError("self edge was accepted")
