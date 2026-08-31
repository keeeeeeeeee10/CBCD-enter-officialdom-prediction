# Documentation feature policy

Documentation variables primarily capture database recording intensity and source availability and must not be interpreted directly as historical causes.

The separated feature set contains `has_address`, `has_kin`, `has_assoc`, `has_status`, `has_text`, `has_institution`, and `documentation_intensity` (with actual dataframe aliases resolved by `configs/feature_policy.yaml`). ENTRY and posting themselves are never documentation predictors.

These variables are prohibited from the default `historical_only` and `pre_entry` tracks. They may be used only in explicitly named comparisons:

- **M5 Documentation-only**
- **Historical + Documentation**

The observed global V1 rates by intensity are 13.95%, 45.49%, 17.39%, 45.21%, 63.94%, 79.86%, and 91.89% for levels 0–6. This is strong but not simply monotonic. Phase 2 must therefore retain the individual domain flags and run:

- **D0:** intensity only
- **D1:** domain flags only
- **D2:** domain flags + intensity

Differences are evaluated as sensitivity to CBDB documentation patterns, not as effects of historical documentation on entry.
