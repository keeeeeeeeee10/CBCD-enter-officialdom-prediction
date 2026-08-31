"""Fail-closed feature policy for CBDB predictor matrices.

The validator intentionally raises on leakage rather than emitting warnings.
Callers must name a model track so documentation and conditional-time features
cannot silently enter a historical/pre-entry model.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = PROJECT_ROOT / "configs" / "feature_policy.yaml"


class FeaturePolicyError(ValueError):
    """Raised when a predictor set violates the frozen feature policy."""


def load_feature_policy(path: str | Path | None = None) -> dict[str, object]:
    policy_path = Path(path).resolve() if path else DEFAULT_POLICY
    with policy_path.open("r", encoding="utf-8") as handle:
        policy = yaml.safe_load(handle)
    if not isinstance(policy, dict):
        raise FeaturePolicyError(f"Invalid feature policy: {policy_path}")
    return policy


def _normalise(feature_names: Iterable[str]) -> list[str]:
    names = [str(name).strip() for name in feature_names]
    if any(not name for name in names):
        raise FeaturePolicyError("Predictor names must be non-empty strings")
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise FeaturePolicyError(f"Duplicate predictor names: {duplicates}")
    return names


def validate_feature_set(
    feature_names: Iterable[str],
    model_track: str,
    policy_path: str | Path | None = None,
) -> bool:
    """Validate a feature set and return True, or raise FeaturePolicyError.

    Direct targets and decoded/count variants are prohibited for every track.
    Raw/unsafe/unknown index years and personal posting outcomes are prohibited
    in all leakage-controlled historical tracks. Documentation variables require
    an explicitly documentation-enabled track.
    """

    names = _normalise(feature_names)
    policy = load_feature_policy(policy_path)
    tracks = policy.get("tracks", {})
    if model_track not in tracks:
        raise FeaturePolicyError(
            f"Unknown model track {model_track!r}; choose one of {sorted(tracks)}"
        )

    forbidden = set(policy.get("forbidden_all_predictors", []))
    direct = sorted(set(names) & forbidden)
    target_like = sorted(name for name in names if name.startswith("target_"))
    if direct or target_like:
        raise FeaturePolicyError(
            f"Direct target/ENTRY-derived predictors are forbidden: {sorted(set(direct + target_like))}"
        )

    pre_entry = policy.get("pre_entry", {})
    denied = set(pre_entry.get("deny", []))
    denied_present = sorted(set(names) & denied)
    if denied_present:
        raise FeaturePolicyError(
            f"Leakage-controlled predictors forbidden by policy: {denied_present}"
        )

    track = tracks[model_track]
    conditional = set(pre_entry.get("conditional", []))
    conditional_present = sorted(set(names) & conditional)
    if conditional_present and not bool(track.get("allow_conditional", False)):
        raise FeaturePolicyError(
            f"Conditional index-year features require a sensitivity track: {conditional_present}"
        )

    documentation = set(policy.get("documentation", {}).get("separate_only", []))
    documentation_present = sorted(set(names) & documentation)
    if documentation_present and not bool(track.get("allow_documentation", False)):
        raise FeaturePolicyError(
            "Documentation features are separated from historical-only models: "
            f"{documentation_present}"
        )

    if model_track == "documentation_only":
        non_documentation = sorted(set(names) - documentation)
        if non_documentation:
            raise FeaturePolicyError(
                f"documentation_only accepts only documentation variables: {non_documentation}"
            )
    return True
