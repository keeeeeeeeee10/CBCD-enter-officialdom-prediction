# ENTRY × posting semantics

This audit distinguishes presence in `ENTRY_DATA` from evidence of an actual recorded posting. A valid auxiliary posting outcome requires a nonzero person and posting ID in `POSTING_DATA` or `POSTED_TO_OFFICE_DATA`; records are deduplicated by person/posting ID.

| ENTRY | posting | people | share of all | share within ENTRY group |
| --- | --- | --- | --- | --- |
| 0 | 0 | 276858 | 41.88% | 62.85% |
| 0 | 1 | 163639 | 24.75% | 37.15% |
| 1 | 0 | 85255 | 12.90% | 38.64% |
| 1 | 1 | 135372 | 20.48% | 61.36% |

- ENTRY-positive without a posting record: **85,255** (38.64% of ENTRY positives).
- ENTRY-negative with a posting record: **163,639** (37.15% of ENTRY negatives).
- Both records present: **135,372**; this is 61.36% of ENTRY positives and 45.27% of posting positives.
- Jaccard overlap between the two recorded-person sets: **35.23%**.
- Neither record present: **276,858**.

The incomplete overlap is substantive and also reflects source/editorial coverage. `ENTRY_DATA` includes degrees, student statuses and institutional routes that need not be appointments, while posting records can exist without a separately encoded ENTRY route.

## Interpretation

**Target V1 is ENTRY record presence. It must not be described as actual government office holding.** `target_posting` is retained as an auxiliary outcome for target-validity and robustness analysis, not as a Phase 1.5 training target.

Dynasty-specific cells are in `outputs/tables/entry_vs_posting_by_dynasty.csv`; the chart reports within-dynasty composition and should be read as CBDB recording patterns, not population office-holding rates.
