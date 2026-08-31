# Target definition and audit

## Default: Target V1

`target_entry = 1` exactly when a non-NULL `BIOG_MAIN.c_personid` appears at least once in `ENTRY_DATA`; otherwise it is 0. Counts are aggregated in SQLite before the one-person target table is materialized.

> Interpret 0 as “no entry record found in the current CBDB `ENTRY_DATA`”, not as proof that the historical person never entered office.

## Population statistics

| people | positive | negative | positive rate | negative rate |
| --- | --- | --- | --- | --- |
| 661124 | 220627 | 440497 | 33.3715% | 66.6285% |

## Integrity checks

| check | value |
| --- | --- |
| entry_rows | 264775 |
| entry_unique_people | 220627 |
| entry_null_person_ids | 0 |
| entry_orphan_rows | 0 |
| entry_orphan_unique_ids | 0 |
| people_with_multiple_entry_rows | 27525 |
| max_entry_rows_per_person | 8 |
| duplicate_person_code_year_groups | 2 |
| unmapped_entry_code_rows | 0 |

Multiple rows per person and repeated person/code/year groups are reported rather than deleted: sources, sequences, institutions, or other fields may legitimately distinguish them. Target V1 collapses all such rows to presence.

## Frozen Phase 1.5 Patch display semantics

| key | display name | 中文解释 | role |
| --- | --- | --- | --- |
| V1 | ENTRY record presence | 是否存在 `ENTRY_DATA` 记录 | Primary record-presence target; unchanged |
| V2a | Broad formal entry/credential target | 广义正式入仕途径/资格记录 | Taxonomy-based sensitivity candidate |
| V2b | High-confidence formal entry/credential target | 高置信度正式入仕途径/资格记录 | Higher-confidence sensitivity candidate; credentials do not imply posting |
| Posting | Recorded office-holding / posting outcome | 是否存在任官记录 | Auxiliary robustness outcome |

`POSTING_DATA` is also an incomplete historical record and is not treated as ground-truth verification of `ENTRY_DATA`. Consequently, lower overlap with Posting does not automatically imply a worse target definition. V2 semantics follow historical interpretation plus official CBDB code descriptions; overlap with Posting is only an auxiliary diagnostic.

## Entry modes observed

| code | English | 中文 | type | type English | type 中文 | records | people |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 36 | examination: jinshi (general) | 科舉: 進士(籠統) | 040101 | Jinshi Examinations | 進士類 | 92572 | 90718 |
| 39 | examination: juren (prefect or provincial graduates) | 科舉: 鄉貢舉人 | 040102 | Juren Examinations | 舉人科 | 56882 | 56784 |
| 110 | Imperial Academy student: general | 監生(籠統) | 0502 | Imperial Academy Students | 監生門 | 28108 | 28107 |
| 47 | school: licentiate | 學校: 生員(庠生) | 040103 | Licenciate | 生員 | 16951 | 16949 |
| 182 | Tribute Student by Purchase, First Class | 廩貢生 | 0503 | Tribute Students | 貢生門 | 7316 | 7316 |
| 152 | tribute student: selected | 貢生: 拔貢 | 0503 | Tribute Students | 貢生門 | 7286 | 7281 |
| 29 | examination: jinshi or zhuke (facilitated degree) | 科舉: 特奏名進士、特奏名諸科 、大挑 | 0401 | Regular Examination | 正常科舉 | 4280 | 4279 |
| 109 | tribute student: general | 貢生 = 貢監生(籠統) (明清賓貢,功貢) | 0503 | Tribute Students | 貢生門 | 3900 | 3898 |
| 177 | tribute student by purchase, third class | 附貢生 | 0503 | Tribute Students | 貢生門 | 3800 | 3800 |
| 312 | soldier | 行伍 | 90 | Other Method of Entry | 其他入仕途徑 | 3662 | 3662 |
| 188 | On the Supplementary List of Graduates | 副榜 | 0401 | Regular Examination | 正常科舉 | 2736 | 2730 |
| 111 | tribute student: annual routine | 貢生: 歲貢、常貢、挨貢 | 0503 | Tribute Students | 貢生門 | 2183 | 2183 |
| 180 | stipend student | 廩生 | 0501 | Students in Schools | 學生門 | 2150 | 2150 |
| 22 | tribute student: by grace | 貢生: 恩貢 | 0503 | Tribute Students | 貢生門 | 2011 | 2010 |
| 118 | yin privilege: general | 恩蔭、蔭補(籠統) | 06 | Yin Privilege | 恩蔭門 | 1973 | 1965 |
| 324 | school student | 庠生 | 0501 | Students in Schools | 學生門 | 1825 | 1825 |
| 311 | Passed Scholar (passed Metropolitan, not yet Palace, Exam) | 科舉: 考上會試/貢士 | 04 | Examination | 科舉門 | 1722 | 1722 |
| 44 | examination: military jinshi (wuju) | 科舉: 武舉進士 | 0401 | Regular Examination | 正常科舉 | 1599 | 1586 |
| 64 | rank or office by inheritance | 世襲(替) | 02 | Kinship | 血親門 | 1557 | 1556 |
| 171 | supplementary student at county school | 縣學附生 | 0501 | Students in Schools | 學生門 | 1452 | 1452 |
| 94 | honorific title based on merit of relative | 封贈 | 13 | Decree of Special Grace | 特旨門 | 1339 | 1338 |
| 199 | Graduate for Excellence | 優貢生 | 0503 | Tribute Students | 貢生門 | 1088 | 1088 |
| 155 | tribute student: by purchase | 貢生: 納貢(例貢,增貢,捐貢) | 0503 | Tribute Students | 貢生門 | 1015 | 1015 |
| 154 | tribute student: appended | 貢生: 副貢 | 0503 | Tribute Students | 貢生門 | 896 | 896 |
| 101 | recommendation | 薦舉 (保任,保舉) | 08 | Recommendation | 薦舉門 | 891 | 886 |

`ENTRY_DATA` contains heterogeneous modes including examinations, school/student statuses, kin privilege, inheritance, purchase, military service, palace routes, recommendations, and unknown/deprecated values. Therefore table presence is reproducible but not synonymous with a single, uniform act of entering government service.

## Candidate Target V2 (not activated in Phase 1)

A later V2 should whitelist entry codes or entry-type branches that domain review classifies as clearly governmental entry modes. The whitelist must be versioned and should separately consider examination success, student status, honorific titles, inheritance, purchase, and routes that do not demonstrate an actual appointment. No codes are silently removed in Phase 1; V1 remains the default for faithful reproduction of the stated task.

## Group diagnostics

Target rates by dynasty and index year are in `outputs/tables/target_by_dynasty.csv` and `outputs/tables/target_by_index_year.csv`. They are coverage diagnostics, not estimates of population-level historical entry rates.
