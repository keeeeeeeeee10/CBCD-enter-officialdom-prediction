# CBDB Phase 3.1.1 最新结果

这是课程提交审查用精简包。Phase 3.1.1 未训练模型、未调参、未改变 split、未访问 reserve/protected data，也未重建缺失置信区间。

核心结果保持不变：Global D5_MAIN ROC-AUC 0.936956、PR-AUC 0.882535、raw LogLoss 0.315106、raw Brier 0.097356、validation-calibrated ECE 0.003438。

论文预测的是 CBDB 中 `ENTRY_DATA` 记录是否存在 (E)，不是潜在真实历史入仕 (T)，也不主张因果效应。Whole-family 证据只适用于 Global 与 Ming 的冻结 F2 comparator，未直接检验 D5_MAIN。原始 CBDB SQLite、模型、大型特征矩阵和全量中间预测不在本包中。

优先阅读 `paper/final/` 中 PDF、`docs/phase3_1_1/latest_results_summary.md`、`docs/phase3_1_1/final_claim_evidence_map.md` 与 `docs/phase3_1_1/final_nature_review.md`。`outputs/phase3_1_1/manifests/` 中的基线清单记录了冻结文件的 SHA-256；清单列出的许多受保护 artifact 在公开仓库中被明确排除。
