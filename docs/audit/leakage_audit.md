# Feature leakage audit

The historical research target is presence in current CBDB `ENTRY_DATA`, not a cleanly timed intervention. This audit separates record-completeness prediction (Model A) from a temporally safer background model (Model B).

## Model A — full information

May use post-entry evidence as an upper-bound/record-completeness signal, but never `ENTRY_DATA`, decoded entry codes, or `n_entry_records`. Its performance must not be interpreted causally or as genuine ex-ante prediction.

## Model B — leakage-controlled / pre-entry

Uses only information demonstrably available before the person's entry/risk time. Personal postings, offices, explicit official outcomes, and unanchored later-life relations, statuses, institutions, and writings are excluded.

## Levels

- **Level 0 — Direct target:** the target table and decoded/count variants; prohibited everywhere.
- **Level 1 — Strong post-entry leakage:** realized offices/postings and explicit official outcomes; Model A only.
- **Level 2 — Potential temporal leakage:** associations, institutions, statuses, texts, and later addresses without reliable pre-entry timing.
- **Level 3 — Safer background:** individually audited personal, family, and pre-entry geographic attributes, still subject to recording bias and temporal checks. Raw index year is explicitly excluded from this level.

## Classification

| table/source | feature group | level | reason | full | pre-entry |
| --- | --- | --- | --- | --- | --- |
| ENTRY_DATA | table presence / entry_code / entry counts | 0 | Defines Target V1 and directly encodes entry mode. | False | False |
| ENTRY_CODES / ENTRY_TYPES / View_EntryData | entry labels and enriched entry rows | 0 | Code labels are a decoded form of the direct target source. | False | False |
| person_base_v0 | n_entry_records | 0 | Count of records used to define the target. | False | False |
| POSTING_DATA | has_posting_record / n_posting_records | 1 | A person's appointments normally reveal realized office holding. | True | False |
| POSTED_TO_OFFICE_DATA | office IDs, dates, counts, ranks | 1 | Explicit realized office postings are strong post-entry outcome leakage. | True | False |
| POSTED_TO_ADDR_DATA | posting locations and counts | 1 | Locations are attached to realized postings. | True | False |
| OFFICE_CODES / OFFICE_CATEGORIES | office name, hierarchy, category | 1 | Decodes the person's realized office outcome. | True | False |
| View_PostingOfficeData / View_PostingAddrData | enriched posting and office features | 1 | Denormalized views expose realized office and posting outcomes. | True | False |
| STATUS_DATA + STATUS_CODES | explicit official/office/jinshi/government statuses | 1 | Several observed status labels directly identify office holding or examination outcomes. | True | False |
| ASSOC_DATA | association presence, degree, type, dates | 2 | Relationships may have formed after entry and are not uniformly dated. | True | False |
| BIOG_INST_DATA | institution roles and counts | 2 | Institutional affiliations may postdate entry or reflect official responsibility. | True | False |
| BIOG_TEXT_DATA / BIOG_SOURCE_DATA | texts, roles, source/record counts | 2 | Later-life production and documentation intensity can follow official success. | True | False |
| STATUS_DATA | non-explicit later-life status categories | 2 | Status observations can occur after entry; temporal anchoring is required. | True | False |
| BIOG_ADDR_DATA | residence/migration/burial/death addresses | 2 | Some address types occur after entry; use only pre-entry-safe types and dates. | True | False |
| BIOG_MAIN | gender | 3 / SAFE | Substantive personal background field; retain unknown as missing. | True | True |
| BIOG_MAIN | birth_year | 3 / SAFE | Allowed only after field-aware sentinel and historical-range validation. | True | True |
| BIOG_MAIN | dynasty | 3 / SAFE background regime | Historical regime baseline; preserve missing/unknown category. | True | True |
| BIOG_MAIN | raw_index_year | 1 / UNSAFE AS RAW FEATURE | Some values are derived from ENTRY/examinations, death, relatives, or later-life events. **Never use directly in a leakage-controlled / pre-entry model.** | True | False |
| person_safe_time_anchor | safe_index_year | 3 / SAFE | Only provenance `01 — Based on Birth Year`, after year validation. | True | True |
| BIOG_MAIN provenance subset | conditional_index_year | 2 / CONDITIONAL | Kin/recursive provenance without explicit outcome evidence; sensitivity analysis only. | True | sensitivity only |
| BIOG_MAIN provenance subset | unsafe_index_year | 1 / UNSAFE | Derived from ENTRY/examination, death, descendants, or other later-life information. | True | False |
| BIOG_MAIN provenance subset | unknown_index_year | 1 / UNKNOWN | Unknown/unparsed provenance is never promoted to SAFE. | True | False |
| BIOG_MAIN + BIOG_ADDR_DATA | index/basic/natal/ancestral geographic background | 3 | Background geography is usable when address semantics and timing precede entry. | True | True |
| KIN_DATA + KINSHIP_CODES | kin structure and kin type | 3 | Family structure is background-like, but relatives' later outcomes require temporal controls. | True | True |
| relatives' ENTRY/POSTING data | parent/grandparent political capital | 3 | Usable only if the relative outcome predates the focal person's entry/risk time. | True | conditional |

## Observed overlap evidence

| metric | people |
| --- | --- |
| entry_people | 220627 |
| posting_people | 299010 |
| posted_to_office_people | 299011 |
| explicit_status_people | 26753 |
| entry_and_posting_people | 135371 |
| entry_and_explicit_status_people | 15199 |

High overlap does not prove leakage by itself, but the semantics and timing of postings/offices make them outcome information. The overlap quantifies how strongly these sources could shortcut Target V1.

## STATUS_DATA terms requiring exclusion or review

| code | English | 中文 | records | people |
| --- | --- | --- | --- | --- |
| 40 | civil office | [為官者：文] | 17034 | 17033 |
| 68 | office: finance | [財政官員] | 2785 | 2785 |
| 61 | military | [武官] | 2487 | 2487 |
| 157 | honest official | 良吏;循吏 | 995 | 995 |
| 2 | army officer | 武將 | 793 | 793 |
| 296 | Righteous person | 義民/義官 | 496 | 496 |
| 34 | office:state council | [宰執] | 455 | 455 |
| 117 | refused office | 拒絕出仕 | 410 | 409 |
| 121 | chose not to seek office | 不求仕 | 306 | 306 |
| 24 | died before taking office | 未仕而卒 | 288 | 288 |
| 70 | official title | [有官銜] | 242 | 242 |
| 69 | office: chief councilor | [宰相] | 230 | 230 |
| 110 | recluse who refused office | 隱居不仕 | 207 | 207 |
| 29 | eunuch | 宦官 | 189 | 189 |
| 47 | jinshi degree holder | [進士] | 189 | 189 |
| 10 | cashiered civil servant | 削籍官員 | 181 | 181 |
| 90 | studying for jinshi | 業進士 | 159 | 159 |
| 78 | gentleman without office | 處士 | 125 | 125 |
| 25 | education official | [學官] | 80 | 80 |
| 136 | student: xianggong jinshi | [鄉貢進士] | 80 | 80 |
| 66 | private secretary of official | [幕僚] | 58 | 58 |
| 67 | office: medical office | [醫官] | 49 | 49 |
| 95 | teacher: military | 教師：軍事教官 | 40 | 40 |
| 53 | holder of minor office | [低級官僚] | 18 | 18 |
| 156 | merciless official | 酷吏 | 17 | 17 |
| 116 | military officer | [軍事將校] | 9 | 9 |
| 79 | secretary: muguan | [幕官] | 5 | 5 |
| 81 | seeking office | 求仕 | 4 | 4 |
| 158 | foreign official who give allegiance to dynasty | 歸明人 | 3 | 3 |
| 18 | office title from contribution | [捐納得官] | 2 | 2 |

The text search is deliberately inclusive (`official`, `office`, `jinshi`, `government`, 官, 進士/进士). False positives and statuses such as refusal/died-before-office must be reviewed rather than automatically treated as positive outcomes. In the strict pre-entry model, all explicitly outcome-bearing status fields remain excluded.

## Frozen index-year rule

Raw `BIOG_MAIN.c_index_year` mixes SAFE, CONDITIONAL, UNSAFE, and UNKNOWN provenance. Some index years are algorithmically derived from `ENTRY_DATA`, examination years, death years, relatives, or later-life events. Raw index year therefore cannot be used directly in any leakage-controlled/pre-entry model. Only the separately materialized `safe_index_year` is allowed; conditional provenance is sensitivity-only, while UNSAFE and UNKNOWN are denied.

This boundary is enforced in code by `configs/feature_policy.yaml` and `src.feature_policy.validate_feature_set`. Violations raise an exception rather than a warning.
