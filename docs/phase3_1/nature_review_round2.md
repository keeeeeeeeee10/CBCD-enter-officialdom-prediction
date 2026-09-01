# Phase 3.1 pre-submission review, Round 2

## Overall assessment

The revised manuscript resolves the Round 1 blocking scientific-reporting issues without changing a frozen model, split, or headline result. Its contribution is now stated at the correct level: an auditable, documentation-aware analysis of retrospective ENTRY-record presence in CBDB, not a new learning algorithm or a reconstruction of true historical entry. The evidence order is coherent, the construct boundary is explicit, and the paper is suitable for course submission.

During Round 2, the first revised build revealed that Appendix Table A3 still carried legacy Physical Geography intervals even though main-text Table 4 had removed them. This was a blocking cross-manuscript inconsistency. The generation script was corrected, all Global/Song/Ming A3--A2 appendix intervals were replaced by dashes, both PDFs were rebuilt, and the automated appendix check now passes.

## Round 1 major-concern resolution

| Round 1 concern | Resolution | Evidence | Status |
| --- | --- | --- | --- |
| Mismatched Physical Geography interval | Exact A2/A3 paired predictions were not retained; all main and appendix intervals for this contrast are omitted | `statistical_correction_manifest.csv`; Tables 4 and A3; automated contrast/containment test | RESOLVED |
| Person-level-looking E/P/T inequality | Construct-level `\not\equiv` notation and an explicit semantic statement replace ordinary inequality | Data and Measurement Problem; Figure 1 | RESOLVED |
| Misleading Figure 1 process | Historical entry/credential, posting/office-holding, and other processes are separated before survival, extraction, and encoding | Figure 1 plus frozen 2-by-2 contingency | RESOLVED |
| Inadequate field positioning | Related Work now synthesizes six relevant areas using 20 verified sources | revised bibliography and reference audit | RESOLVED |
| Compressed evidence chain and faulty page count | EDA, evidence hierarchy, discussion, and four-theme limitations were rebuilt; float boundary is correctly counted | revised PDF; `page_count_audit.json` | RESOLVED |

## Required final checklist

1. **Round 1 concerns:** All five major concerns and eight minor/presentation concerns are resolved or reduced to non-blocking typography notes.
2. **Table 4 confidence intervals:** PASS. Physical Geography is explicitly A3--A2 and has no interval because exact paired predictions are absent. No G3--G2 interval is reused. The same correction appears in Appendix Table A3.
3. **E/P/T semantics:** PASS. $T$ is latent true historical entry; $E$ and $P$ are semantically distinct observed database relations. The estimand is $\Pr(E=1\mid X)$.
4. **Causal interpretation:** PASS. The manuscript repeatedly distinguishes conditional information, attribution, transport, and causation. It does not claim true-entry prediction or historical causal effects.
5. **Related Work:** PASS. Twenty verified references cover CBDB/prosopography, GIS and networks, tabular learning, distribution shift and transport, documentation/measurement/label noise, SHAP, and calibration.
6. **Figure captions:** PASS. All eight main figures and three appendix figures state population or scope, quantity, denominator or missing-cell meaning where relevant, and interpretation boundaries. Figure inputs and scripts are local and manifest-traced.
7. **Statistical consistency:** PASS. Headline metrics were recomputed from retained predictions; paired intervals require exact pairs; retained intervals contain their point estimates; five-seed ranges are not called confidence intervals; raw losses are separated from validation-calibrated ECE.
8. **Source-level wording:** PASS. The claim is limited to infeasibility under the prespecified full-coverage connected-component protocol. A narrower selective subset is identified only as future sensitivity work.
9. **Data availability:** PASS. The official CBDB acquisition path, release filename, SHA256 verification, non-redistribution boundary, review predictions, excluded large intermediates, code licence, environments, seeds, frozen splits, hashes, and figure provenance are disclosed.
10. **Submission state:** PASS. Both PDFs compile with resolved references, neutral course-report metadata, embedded content, and no placeholders. Both have eight main pages; references begin on page 9 and appendices on page 10. The anonymous PDF and its anonymous/shared sources contain no author identity.

## Statistical and scientific assessment

The main claim is supported by frozen test evidence: Global D5_MAIN ROC-AUC is 0.936956 and PR-AUC is 0.882535. The paper does not treat this as historical-truth recovery. Grouped ablation is appropriately primary, with family observability and topology separated from recorded political capital. The latter's increments remain correctly described as small. Matched-support spatial degradation bounds transport, and the family/source/temporal/Qing results are reported only to the extent permitted by frozen artifacts.

The uncertainty language is now defensible. Paired bootstrap intervals are attached only to retained exact model pairs, matched-support spatial comparisons are not called paired-person tests, and bootstrap sampling uncertainty is separated from target validity, source survival, and database selection. Table 3 clearly distinguishes raw LogLoss and Brier from validation-calibrated ECE.

## Presentation and reproducibility assessment

The revised figures are clear at two-column scale, use consistent visual conventions, and contain no external or decorative images. Appendix figures and tables are now numbered A1 onward. The largest remaining overfull box is 12.12 pt in a long appendix status token; it is visibly contained within the table and is not a scientific or submission blocker. No severe overflow, undefined reference, placeholder, or anonymous-identity leak was observed.

Reproducibility is unusually strong for a course paper: the review artifact exposes de-identified final predictions for nine population-model pairs, verified source snapshots for every figure, exact model and data hashes, correction manifests, environments, and automated scientific checks. Raw/working CBDB databases and the full feature master are correctly excluded.

## Remaining non-blocking notes

- A production venue could restyle long appendix status tokens for visual elegance.
- A future study could preregister a truly prospective cohort and a selective source subset, but neither experiment should be added post hoc to this frozen paper.
- External archival deposition and a persistent DOI would improve long-term FAIRness; the manuscript correctly avoids claiming one now.

## Final recommendation

**ACCEPTABLE_FOR_COURSE_SUBMISSION**

## Confidence

**High, 0.96.** This assessment used the revised author and anonymous PDFs, shared LaTeX body and wrappers, recomputed metrics, correction manifest, full appendix, figure manifest and source snapshots, 20-item reference audit, data audit, page audit, claim--evidence map, frozen invariant precheck, and 21 passing pre-package scientific/LaTeX tests.
