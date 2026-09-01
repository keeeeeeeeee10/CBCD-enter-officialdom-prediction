# Course-task alignment

This study combines open-ended exploratory analysis of dynastic, gender, ENTRY-pathway, geographic, and kin-observability patterns with predictive modeling of ENTRY-record presence.

| Course task | Manuscript evidence | Boundary |
| --- | --- | --- |
| Open-ended exploratory data mining | Dynasty and gender coverage, ENTRY-pathway composition, address decomposition, family observability/topology/capital decomposition | Describes CBDB-covered records, not the historical Chinese population |
| Predictive modeling | Frozen Logistic M6, H_STRUCT, D5_MAIN and D6_UPPER primary-test results | Predicts observed ENTRY-record presence E, not latent true entry T |
| Robustness and distribution shift | Grouped ablations, five-seed checks, F2-only whole-family holdout, matched-support spatial shift | D5_MAIN was not directly evaluated under whole-family grouping; SAFE and source protocols lack locked performance |
| Reproducibility | Frozen release identifier, split/model/prediction hashes, figure source tables, exact method specifications and release archives | Raw CBDB SQLite and large intermediates are not redistributed |

The assignment brief reports approximately 515,488 people, whereas the verified release used in this study contains 661,124 BIOG_MAIN person records. CBDB counts are release-specific; all results here refer only to cbdb_20260829.sqlite3.
