# Final statistical consistency audit

Status: **PASS**

This is the single focused `nature-statistics` audit for Phase 3.1.1. It reads only frozen tables and manuscript outputs. It does not train, refit, resample, or reconstruct missing intervals.

- Family capital: frozen Global full-record ΔROC = +0.000701, Song = +0.001821, Ming = -0.000319; Ming train-observed = -0.000394. Both Ming ROC-AUC and PR-AUC intervals include zero.
- Physical geography: all three A3-A2 rows retain unavailable confidence intervals. No interval was recreated.
- Operating points: 12 retained population-model rows are reported. Thresholds and sigmoid parameters come from existing artifacts; numeric class weights and Logistic calibrators remain `NOT_RETAINED`.
- Shift support: family-group performance is limited to the F2 comparator in Global and Ming. SAFE and source rows remain availability or feasibility diagnostics, not new model results.
- Nested ablations: increments are reported as prespecified conditional, order-dependent contrasts, not unique or causal contributions.
