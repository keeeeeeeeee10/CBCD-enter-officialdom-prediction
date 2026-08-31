# ENTRY code taxonomy and Target V2 candidates

The official schema contains **273** `ENTRY_CODES`; **253** are used by `ENTRY_DATA`. Classifications use official Chinese/English descriptions and `ENTRY_CODE_TYPE_REL → ENTRY_TYPES`, never code number alone.

## Semantic categories among used codes

| category | used codes | records | sum of per-code people | manual-review codes |
| --- | --- | --- | --- | --- |
| exam_degree | 121 | 163002 | 161023 | 104 |
| school_or_student_status | 47 | 86607 | 86586 | 47 |
| military_entry | 14 | 5001 | 5001 | 10 |
| hereditary_or_yin_privilege | 16 | 4578 | 4569 | 8 |
| ambiguous | 30 | 2157 | 2155 | 30 |
| direct_appointment | 10 | 1332 | 1330 | 0 |
| recommendation | 3 | 957 | 952 | 0 |
| other_clear_entry | 5 | 743 | 740 | 5 |
| failed_entry | 4 | 336 | 335 | 0 |
| purchase_or_donation | 1 | 48 | 48 | 0 |
| unknown | 2 | 14 | 14 | 2 |

The per-code people column is not a unique category-person count because one person may have multiple codes. Person-level target counts are reported below.

## Candidate policy

- **V1:** any `ENTRY_DATA` record; unchanged.
- **V2a — Broad formal entry/credential target（广义正式入仕途径/资格记录）:** exam degree, recommendation, hereditary/yin, military, purchase/donation, direct appointment, and other clear entry. School/student status is conservatively excluded pending manual review.
- **V2b — High-confidence formal entry/credential target（高置信度正式入仕途径/资格记录）:** only V2a codes with HIGH semantic confidence. Examination codes require description-level evidence of passing/degree/graduate status. A credential does not establish actual office holding; this remains a candidate, not the sole official target.
- **Auxiliary Posting — Recorded office-holding / posting outcome（是否存在任官记录）:** posting is also an incomplete historical record and is not ground-truth verification of ENTRY_DATA. Overlap is an auxiliary diagnostic only.
- Failed, ambiguous, unknown, honorific-only, palace/dynastic, religious, and unsupported school/student records are excluded from both candidates.

| target | positives | rate | overlap V1 | overlap posting | posting overlap rate | posting Jaccard |
| --- | --- | --- | --- | --- | --- | --- |
| ENTRY record presence | 220627 | 33.37% | 220627 | 135372 | 61.36% | 35.23% |
| Broad formal entry/credential target | 155531 | 23.53% | 155531 | 81913 | 52.67% | 21.98% |
| High-confidence formal entry/credential target | 148528 | 22.47% | 148528 | 76353 | 51.41% | 20.57% |
| Recorded office-holding / posting outcome | 299011 | 45.23% | 135372 | 299011 | 100.00% | 100.00% |

## Twenty largest used codes

| code | English | 中文 | official type | category | confidence | records | people | V2a | V2b |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 36 | examination: jinshi (general) | 科舉: 進士(籠統) | 040101 | exam_degree | HIGH | 92572 | 90718 | True | True |
| 39 | examination: juren (prefect or provincial graduates) | 科舉: 鄉貢舉人 | 040102 | exam_degree | HIGH | 56882 | 56784 | True | True |
| 110 | Imperial Academy student: general | 監生(籠統) | 0502 | school_or_student_status | LOW | 28108 | 28107 | False | False |
| 47 | school: licentiate | 學校: 生員(庠生) | 040103 | school_or_student_status | LOW | 16951 | 16949 | False | False |
| 182 | Tribute Student by Purchase, First Class | 廩貢生 | 0503 | school_or_student_status | LOW | 7316 | 7316 | False | False |
| 152 | tribute student: selected | 貢生: 拔貢 | 0503 | school_or_student_status | LOW | 7286 | 7281 | False | False |
| 29 | examination: jinshi or zhuke (facilitated degree) | 科舉: 特奏名進士、特奏名諸科 、大挑 | 0401 | exam_degree | HIGH | 4280 | 4279 | True | True |
| 109 | tribute student: general | 貢生 = 貢監生(籠統) (明清賓貢,功貢) | 0503 | school_or_student_status | LOW | 3900 | 3898 | False | False |
| 177 | tribute student by purchase, third class | 附貢生 | 0503 | school_or_student_status | LOW | 3800 | 3800 | False | False |
| 312 | soldier | 行伍 | 90 | military_entry | MEDIUM | 3662 | 3662 | True | False |
| 188 | On the Supplementary List of Graduates | 副榜 | 0401 | exam_degree | HIGH | 2736 | 2730 | True | True |
| 111 | tribute student: annual routine | 貢生: 歲貢、常貢、挨貢 | 0503 | school_or_student_status | LOW | 2183 | 2183 | False | False |
| 180 | stipend student | 廩生 | 0501 | school_or_student_status | LOW | 2150 | 2150 | False | False |
| 22 | tribute student: by grace | 貢生: 恩貢 | 0503 | school_or_student_status | LOW | 2011 | 2010 | False | False |
| 118 | yin privilege: general | 恩蔭、蔭補(籠統) | 06 | hereditary_or_yin_privilege | HIGH | 1973 | 1965 | True | True |
| 324 | school student | 庠生 | 0501 | school_or_student_status | LOW | 1825 | 1825 | False | False |
| 311 | Passed Scholar (passed Metropolitan, not yet Palace, Exam) | 科舉: 考上會試/貢士 | 04 | exam_degree | HIGH | 1722 | 1722 | True | True |
| 44 | examination: military jinshi (wuju) | 科舉: 武舉進士 | 0401 | exam_degree | HIGH | 1599 | 1586 | True | True |
| 64 | rank or office by inheritance | 世襲(替) | 02 | hereditary_or_yin_privilege | HIGH | 1557 | 1556 | True | True |
| 171 | supplementary student at county school | 縣學附生 | 0501 | school_or_student_status | LOW | 1452 | 1452 | False | False |

All LOW/MEDIUM, school/student, ambiguous, and unknown cases are explicitly marked for manual review in `target_v2_candidate_codes.csv`. These rules are reproducible hypotheses, not final historical adjudications.

Lower overlap with Posting does not automatically mean a worse target definition. V2a/V2b are based on historical semantics and official CBDB code definitions; Posting supplies a separate, incomplete outcome diagnostic rather than ground truth.
