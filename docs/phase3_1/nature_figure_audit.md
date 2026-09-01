# Phase 3.1 Nature-style figure audit

## Figure contract

- **Core conclusion:** the frozen models discriminate retrospective CBDB ENTRY-record presence strongly, but the signal is structured by database observability and weakens under historical-region shift; it is not evidence of latent historical entry truth.
- **Results-level sequence:** measurement definition → descriptive record context → locked discrimination → conditional feature evidence → transport boundary → attribution with explicit non-causal limits.
- **Archetypes:** Figure 1 is a schematic-led composite; Figures 2–8 are quantitative grids or compact quantitative summaries; Figures A1–A3 are supporting diagnostics.
- **Backend:** Python/Matplotlib exclusively.
- **Final size:** approximately 184 mm wide for double-column figures, with a rendered glyph floor above 5 pt.
- **Evidence hierarchy:** grouped ablation and transport tests are primary interpretation evidence; SHAP is subordinate attribution evidence; calibration, five-seed ranges, and feasibility evidence are appendix checks.
- **Integrity contract:** no external or AI-generated imagery; no manual bar-height editing; every quantitative panel is linked to a project-local CSV snapshot and frozen upstream hash.

## Disposition of the original 11 figures

| Figure | Decision | Role and revision |
|---|---|---|
| Figure 1, E/P/T task definition | **revise; keep in main text** | Rebuilt the causal-looking topology. Historical entry/credential events, posting/office-holding events, and other biographical processes are distinct upstream concepts before survival, selection, extraction, and encoding. The true frozen E × P counts remain in panel b. |
| Figure 2, dynasty/gender context | **revise; keep in main text** | Retains coverage and within-CBDB E prevalence, moves the gender legend outside the data region, and states the denominator and non-population-rate boundary in the caption. |
| Figure 3, ENTRY pathways | **revise; keep in main text** | Retains record composition and unique-person prevalence as complementary roles. The caption states that person categories are nonexclusive; the legend is moved outside the plot. |
| Figure 4, locked models | **revise; keep in main text** | Replaced truncated-axis bars with point comparisons, preserving all frozen metrics while avoiding visual exaggeration. D5_MAIN and D6_UPPER roles are explicit. |
| Figure 5, grouped ablation | **revise; keep in main text** | Uses the corrected Phase 3.1 table, makes the zero line and negative Physical Geography PR increment visible, and omits unsupported intervals rather than borrowing G2/G3 intervals. |
| Figure 6, address/spatial transport | **revise; keep in main text** | Retains complementary decomposition and boundary panels. Negative unseen-region deltas receive a quiet red background and an explicit directional axis label. |
| Figure 7, family decomposition | **revise; keep in main text** | Retains observability, topology, full-record capital, and train-observed capital as distinct conditional blocks; political-capital increments remain visibly small. |
| Figure 8, grouped SHAP | **revise; keep in main text** | Rebuilt with a shared color scale and equal panel geometry. The ambiguous `other` label is replaced by `Historical regime`; the caption prohibits causal or independent-increment readings. |
| Figure A1, calibration | **revise; move_to_appendix** | Titles and axes now distinguish raw from validation-calibrated probability ECE. The caption states that calibration used validation predictions only. |
| Figure A2, five-seed stability | **keep; move_to_appendix** | Mean and observed five-seed range remain visible; this is reassurance rather than a new main-text claim. |
| Figure A3, robustness scope | **revise; move_to_appendix** | Explicitly shows that the temporal result is split-only and that source grouping was infeasible, preventing readers from mistaking either panel for model performance. |

No figure was removed or merged because the eight main figures map to eight different inferential steps and the three appendix figures document distinct diagnostics or feasibility boundaries.

## Rendered QA

- Source preflight: **ready**, 0 FAIL. The PNG-only warning is accepted because the requested raster deliverable is 300-dpi PNG; PDF and SVG are the authoritative vector files.
- Input completeness: no row sampling or missing-data exclusion was introduced by the Phase 3.1 renderer.
- Alignment: all nine multi-panel figures **PASS** at the 1.5-pt tolerance; the two single-panel figures are correctly marked NOT APPLICABLE.
- PDF text: all 11 files are auditable; minimum rendered text is **6.7 pt**, with 0 glyphs below 5 pt.
- Collision audit: ten figures **PASS** without warnings. Figure 1 has five reviewed `text-fill-edge` warnings caused by text intentionally placed inside colored concept boxes; final-size inspection confirms that no text touches a box boundary and no arrow crosses text. There are no collision FAIL findings.
- Visual inspection: every panel was inspected at final size for labels, axes, legend clearance, negative values, color consistency, and ambiguity. No decorative or third-party image is present.

## Provenance and outputs

The machine-readable manifest is `outputs/phase3_1/tables/figure_manifest_revised.csv`. Each of its 11 rows records the paper section, self-contained caption, upstream table(s), upstream SHA256 value(s), generating script, PNG/PDF/SVG paths, input snapshot, and verification status. The plotting source is `scripts/63_phase3_1_figures.py`; figure-level alignment, glyph, and collision reports are under `outputs/phase3_1/figure_qa/`.
