# CBDB Phase 3.1.1 latest results

This compact archive is intended for course-submission review. Phase 3.1.1 performed no model training, tuning, split selection, reserve/protected-data access, or reconstruction of missing confidence intervals.

The frozen Global D5_MAIN result remains ROC-AUC 0.936956, PR-AUC 0.882535, raw LogLoss 0.315106, raw Brier 0.097356, and validation-calibrated ECE 0.003438.

The paper predicts the presence of a CBDB `ENTRY_DATA` record (E), not latent true historical entry (T), and makes no causal claim. Whole-family evidence is limited to the frozen F2 comparator in Global and Ming; D5_MAIN was not directly evaluated. Raw CBDB SQLite files, models, large feature matrices, and full intermediate predictions are excluded.

Start with the PDFs in `paper/final/`, `docs/phase3_1_1/latest_results_summary.md`, `docs/phase3_1_1/final_claim_evidence_map.md`, and `docs/phase3_1_1/final_nature_review.md`. The baseline inventory in `outputs/phase3_1_1/manifests/` records frozen file-level SHA-256 values; many protected artifacts listed there are intentionally absent from this public repository.
