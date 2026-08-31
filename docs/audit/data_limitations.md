# CBDB data limitations

CBDB is not a random sample of the historical population of China. It is a prosopographical database assembled from surviving and selected historical sources, so its recorded people and fields reflect who was documented, which sources survived, and what editors encoded.

## Required interpretation

In this release, **220,627 of 661,124 CBDB people (33.37%)** have at least one current `ENTRY_DATA` record. This is the **entry-record share among people included in CBDB**, not the true historical entry rate of people in China.

`target_entry = 0` means **no entry record was found in the current CBDB ENTRY_DATA table**. It must not be described as “this person certainly never held office” or “never entered government.”

## Main biases

- **Selection bias:** inclusion follows research sources and database scope, not population sampling.
- **Survivorship bias:** people and events in surviving texts are disproportionately observable.
- **Recording bias:** a missing row or field can mean missing documentation or incomplete encoding, not absence in history.
- **Elite bias:** officials, examination candidates, writers, and well-connected families are more likely to be documented.
- **Gender bias:** women and gender-minority/unknown records have markedly different documentation coverage; `c_female=0` is retained as the database code and NULL remains unknown.
- **Temporal coverage bias:** dynasties and periods have unequal source survival and CBDB coverage.
- **Regional coverage bias:** place coverage and geocoding differ by region and period.

## Modeling consequences

Model A measures how well all non-target CBDB records identify database entry-record presence and is an upper bound on record-completeness prediction. Model B requires temporal anchoring and safer background features. Neither supports causal claims without a separate research design. Missingness and relationship counts may themselves encode scholarly attention, so even apparently neutral coverage indicators require interpretation.

No anomalous or missing records are deleted in Phase 1. Exact issue counts are retained in `outputs/tables/data_quality_issues.csv`; field and relation coverage is retained in `base_missingness.csv` and `coverage_summary.csv`.
