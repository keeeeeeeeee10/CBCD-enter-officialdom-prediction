# Nature skill revision log

| skill | recommendation | accepted_or_rejected | evidence | changed_files | reason |
| --- | --- | --- | --- | --- | --- |
| nature-reviewer | Separate construct validity, leakage, transport, and contribution concerns. | accepted | Round 1 major concerns and revised argument | main_body_revised.tex; nature_review_round1.md | Required for an evidence-led review. |
| nature-reviewer | Treat model choice or SHAP as novelty. | rejected | No new algorithm was developed | main_body_revised.tex | Would overstate the contribution. |
| nature-reviewer | Re-audit the completed manuscript against every major concern. | accepted | Round 2 checklist | nature_review_round2.md | Final submission gate. |
| nature-statistics | Recompute all headline metrics from retained predictions. | accepted | 436,881 prediction rows | 61_phase3_1_statistics.py; final_metric_recomputation.csv | Direct numerical verification. |
| nature-statistics | Remove the mismatched Physical Geography CI. | accepted | A2/A3 predictions absent; old interval is G2/G3 | table4_ablation.tex; statistical_correction_manifest.csv | Exact paired identity is mandatory. |
| nature-statistics | Approximate the missing interval. | rejected | No exact retained pair | nature_statistics_audit.md | Approximation would misrepresent uncertainty. |
| nature-writing | Reframe the manuscript around five research questions and an evidence hierarchy. | accepted | Frozen results and Round 1 critique | main_body_revised.tex; nature_writing_structure.md | Clarifies contribution without changing results. |
| nature-writing | Rewrite limitations as four thematic arguments. | accepted | All required limitations retained | main_body_revised.tex | Improves inference boundaries. |
| nature-writing | Add unrun temporal, Qing, or source-holdout results. | rejected | No frozen locked performance artifact | main_body_revised.tex | Would invent evidence. |
| nature-citation | Cover six relevant literature families with claim-specific sources. | accepted | 20 selected sources | nature_citation_search.md; references_revised.bib | Each source supports text actually used. |
| nature-citation | Add papers solely to reach a larger count. | rejected | Relevance screening | nature_citation_search.md | Citation count is not an objective. |
| nature-ref-verifier | Verify title, authors, year, venue, DOI or official URL, and claim fit. | accepted | 20 of 20 VERIFIED | reference_audit_revised.csv; reference_verification_report.md | Required before formal citation. |
| nature-ref-verifier | Retain the Fuller--Wang item after official-journal verification when Crossref was incomplete. | accepted | Journal page and DOI metadata | reference_audit_revised.csv | Independent authoritative fallback resolved the exception. |
| nature-figure | Redraw E/P/T without a false single-event causal chain. | accepted | Frozen contingency plus audited semantics | 63_phase3_1_figures.py; final_task_definition_ep_t.* | Corrects the measurement diagram. |
| nature-figure | Standardize 11 figures and move three diagnostics to the appendix. | accepted | Figure manifest and PDF inspection | paper/revised/figures; figure_manifest_revised.csv | Improves hierarchy and legibility. |
| nature-figure | Use AI imagery or external screenshots for the concept figure. | rejected | All visual elements are data/code-native | nature_figure_audit.md | Would weaken provenance and editability. |
| nature-data | State official access, version, SHA256, and non-redistribution. | accepted | CBDB access and local file audit | nature_data_audit.md; main_body_revised.tex | Defines lawful reproducibility boundaries. |
| nature-data | Include predictions and figure inputs but exclude large regenerable matrices. | accepted | Artifact inventory | data_availability_inventory.csv | Balances reviewability and package size. |
| nature-data | Redistribute raw or working SQLite files. | rejected | Third-party data boundary | DATA_USAGE.md | Project licence does not grant CBDB redistribution rights. |
| nature-polishing | Use precise, evidence-first English and canonical terminology. | accepted | Consistency sweep | main_body_revised.tex; nature_polishing_audit.md | Improves clarity without altering evidence. |
| nature-polishing | Compress the paper by shrinking type, margins, or spacing. | rejected | Page-layout audit | page_count_audit.json | The page limit was met through prose and float revision. |
