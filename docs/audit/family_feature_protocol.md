# Family Political Capital feature protocol

Phase 2 must keep two analytically distinct family tracks. Neither track licenses causal language: estimates describe predictive association with recorded CBDB outcomes.

## Track A — Cross-sectional Family Capital

This large-sample track may use family outcomes observed anywhere in the retained historical record:

- `father_identified`, `mother_identified`
- `paternal_grandfather_identified`, `maternal_grandfather_identified`
- `father_ever_entry`, `father_ever_posting`
- `paternal_grandfather_ever_entry`, `paternal_grandfather_ever_posting`
- `maternal_grandfather_ever_entry`, `maternal_grandfather_ever_posting`
- `n_known_older_kin`, `n_older_kin_ever_entry`, `n_older_kin_ever_posting`
- `older_kin_entry_ratio`, `older_kin_posting_ratio`

Lifetime career variables must use the explicit `ever_` marker or be marked `cross_sectional` in metadata. They must never be named `pre_entry_*`, `prior_*`, or `before_anchor_*`. These features measure recorded family political capital in the full historical record; they are not strictly pre-entry background features.

## Track B — Pre-birth Lineage Political Capital（出生前家族政治资本）

The currently SAFE provenance is `01 — Based on Birth Year`, so `safe_index_year` is a validated birth-year proxy rather than an entry-risk time. This track is restricted to focal people with a valid `safe_birth_year` and asks whether recorded family political capital already existed before the focal person's birth. Candidate features are:

- `father_entry_before_birth`, `father_posting_before_birth`
- `paternal_grandfather_entry_before_birth`, `paternal_grandfather_posting_before_birth`
- `maternal_grandfather_entry_before_birth`, `maternal_grandfather_posting_before_birth`
- `n_older_kin_entry_before_birth`, `n_older_kin_posting_before_birth`
- `any_older_kin_entry_before_birth`, `any_older_kin_posting_before_birth`

Eligibility requires a valid relative event year with `relative_event_year < focal_safe_birth_year`. An invalid or absent relative year remains missing and is never converted to zero. This is not evidence that capital existed before the focal person's own entry.

## Future Track C — Matched Pre-entry Family Capital

This Phase 2 does not implement the matched case-control design. A future sensitivity analysis may define `risk_time` as the earliest valid ENTRY year for positives and assign negatives a pseudo-risk year matched within dynasty and similar SAFE cohort. Only relative events strictly earlier than that fold-assigned risk time may then use true `pre_entry_*` or `before_risk_time_*` names. Matching, outcome aggregation, encoding, and imputation must occur inside training folds.

## Conservative relation eligibility

- Prefer father, mother-side elders, grandfathers/grandmothers, and older ancestors.
- Same-generation siblings and cousins are CONDITIONAL and excluded from the first pre-birth specification.
- Descendants—including sons, daughters, grandchildren, and descendants' spouses—are excluded from the first pre-birth specification even if a rare recorded date appears earlier.
- Spouse and affinal relations require separate timing and are excluded from the first pre-birth specification.
- Family-connected grouping is a split constraint, never a predictor feature.
