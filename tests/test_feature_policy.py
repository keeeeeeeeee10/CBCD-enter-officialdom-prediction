"""Regression tests for the frozen Phase 2 feature boundary."""

from __future__ import annotations

import pytest

from src.feature_policy import FeaturePolicyError, validate_feature_set


def test_raw_index_year_fails_pre_entry() -> None:
    with pytest.raises(FeaturePolicyError):
        validate_feature_set(["dynasty", "gender", "raw_index_year"], "pre_entry")


def test_safe_index_year_passes_pre_entry() -> None:
    assert validate_feature_set(["dynasty", "gender", "safe_index_year"], "pre_entry")


def test_documentation_fails_historical_only() -> None:
    with pytest.raises(FeaturePolicyError):
        validate_feature_set(["has_kin", "documentation_intensity"], "historical_only")


@pytest.mark.parametrize("target", ["target_entry_v1", "target_entry_v2a", "target_entry_v2b"])
def test_target_always_fails(target: str) -> None:
    with pytest.raises(FeaturePolicyError):
        validate_feature_set(["dynasty", target], "historical_plus_documentation")


@pytest.mark.parametrize("posting", ["target_posting", "n_posting_records", "has_posting_record"])
def test_personal_posting_fails_pre_entry(posting: str) -> None:
    with pytest.raises(FeaturePolicyError):
        validate_feature_set(["dynasty", posting], "pre_entry")


def test_conditional_year_requires_sensitivity_track() -> None:
    with pytest.raises(FeaturePolicyError):
        validate_feature_set(["dynasty", "conditional_index_year"], "pre_entry")
    assert validate_feature_set(
        ["dynasty", "conditional_index_year"], "pre_entry_sensitivity"
    )


def test_documentation_track_is_explicit() -> None:
    assert validate_feature_set(
        ["has_kin", "documentation_intensity"], "documentation_only"
    )


def test_family_group_id_is_never_a_predictor() -> None:
    with pytest.raises(FeaturePolicyError):
        validate_feature_set(["dynasty", "family_group_id"], "cross_sectional_family")
