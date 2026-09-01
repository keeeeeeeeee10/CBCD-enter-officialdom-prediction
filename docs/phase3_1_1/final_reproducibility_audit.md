# Final reproducibility audit

Status: **PASS**

- All 97 frozen baseline files match their recorded SHA-256 values, including models, splits, predictions, databases, and Phase 3.1 tables and figures.
- Tables A2, A3, and A4 retain the exact Phase 3.1 rows and values; only Global, Song, Ming display ordering changed.
- `local_target_prior` is documented from executable code and frozen configuration, with leakage tests for OOF training and held-out transforms.
- Primary support contains 9 rows and shift support 29 rows. Missing quantities remain explicitly unavailable.
- No model was trained, tuned, recalibrated, or refitted; no split was selected; no missing CI was reconstructed; no protected or reserve data were accessed.
