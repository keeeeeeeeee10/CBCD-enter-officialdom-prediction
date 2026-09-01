# Phase 3.1 strict reference verification

## Result

- Total audited: **20**
- VERIFIED: **20**
- CHECK SUGGESTED: **0**
- NEEDS FIX: **0**
- UNVERIFIABLE: **0**

All references admitted to the revised bibliography have a verified DOI or official project/proceedings URL and support a retained manuscript statement. Bibliographic existence and claim support were audited separately.

## Field-level decisions

- DOI-bearing records were checked against DOI metadata and a publisher, journal, or official proceedings page.
- Fuller and Wang (2021) is the one Crossref exception: Crossref did not return the DOI, while the journal page independently reports the same title, authors, year, volume, issue, pages, DOI, and peer-reviewed status.
- Bol (2012) retains the official volume year although its DOI contains `2011`; this is a registration/publication-year difference, not a mismatch.
- Author suffixes and diacritics were normalized without changing author order. No author was omitted.
- Official project documentation is used only for project, schema, and access facts; conceptual claims use peer-reviewed work.

## Claim-boundary controls

- Label-noise literature does not imply that the operational CBDB label is random corruption of historical truth.
- Measurement literature is conceptual support and is not evidence of CBDB-specific coverage rates.
- Dataset-shift literature motivates grouped evaluation but does not turn the study into a causal transport analysis.
- SHAP references support additive attribution and interpretation limits, not causal claims.
- Calibration references support validation-fitted post-hoc calibration, never fitting on test labels.

The machine-readable audit is `paper/revised/reference_audit_revised.csv`; corrected BibTeX is `paper/revised/references_revised.bib`.
