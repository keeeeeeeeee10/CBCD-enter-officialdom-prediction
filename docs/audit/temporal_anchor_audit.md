# Temporal anchor audit

Phase 1.5 does not force a single precise risk year. Raw fields remain unchanged; year sentinels and implausible values are converted to missing only in derived audit fields.

## Observed coverage

| candidate | people | coverage |
| --- | --- | --- |
| valid birth year | 59851 | 9.05% |
| valid raw index year | 307706 | 46.54% |
| SAFE index-year provenance | 59851 | 9.05% |
| ENTRY positives with valid entry year | 96388 | 43.69% |

## Anchor A — birth year + fixed age

Birth-year coverage is 9.05%. Among 19,927 ENTRY-positive people with both a valid birth and earliest entry year, median recorded entry age is 31.0; 17.87% enter before age 25 and 44.00% before age 30. A +25/+30 landmark is genuinely background-based but changes the estimand and loses most people; it cannot be treated as each person's true entry-risk date.

## Anchor B — safe index year + offset

SAFE index-year coverage is only 9.05%. The only SAFE provenance is code `01`, based directly on birth year, so `safe_index_year + 20` is effectively another birth-cohort landmark rather than independent timing information. It is suitable only for sensitivity subsets, not as a universal anchor.

## Anchor C — earliest ENTRY year plus matched pseudo-risk year

A valid earliest entry year is available for 43.69% of ENTRY positives. Matching negatives by dynasty, safe cohort and age can support a matched case-control analysis, but pseudo-risk assignment must occur inside training folds and preserve matching groups. It does not create a natural event time for all negatives.

## Recommendation

Use dynasty/cohort baselines on the safe-anchor subset and report the global cross-sectional record-prediction task separately. Anchor A and matched Anchor C should be parallel sensitivity designs. Current coverage does not justify manufacturing one universal pre-entry year.

## Association timing

Only 15,773 of 189,970 association rows (8.30%) contain a valid first or last year, covering 5,530 people. Undated edges are not treated as pre-entry; network work remains a subset analysis without PageRank/GNN in this phase.
