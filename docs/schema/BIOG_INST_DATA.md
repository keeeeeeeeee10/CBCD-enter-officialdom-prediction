# BIOG_INST_DATA

Rows: **567**; columns: **19**.

Person identifier fields observed: `c_personid`.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_personid | INTEGER(11) | 0 | 0.0000% | 0 | 475 | False | [696576, 438255, 30631] |
| c_inst_name_code | smallint(6) | 0 | 0.0000% | 0 | 314 | False | [0, 1625, 12] |
| c_inst_code | smallint(6) | 0 | 0.0000% | 0 | 345 | False | [0, 14, 4008] |
| c_bi_role_code | smallint(6) | 0 | 0.0000% | 0 | 18 | False | [0, 5, 6] |
| c_bi_begin_year | smallint(6) | 537 | 94.7090% | 0 | 22 | False | [1474, 1851, 1072] |
| c_bi_by_nh_code | smallint(6) | 528 | 93.1217% | 0 | 21 | False | [18, 647, 665] |
| c_bi_by_nh_year | smallint(6) | 539 | 95.0617% | 0 | 12 | False | [1, 5, 15] |
| c_bi_by_range | smallint(6) | 554 | 97.7072% | 0 | 3 | False | [-1, 2, 0] |
| c_bi_end_year | smallint(6) | 554 | 97.7072% | 0 | 7 | False | [1836, 1010, 1014] |
| c_bi_ey_nh_code | smallint(6) | 554 | 97.7072% | 0 | 6 | False | [664, 515, 529] |
| c_bi_ey_nh_year | smallint(6) | 554 | 97.7072% | 0 | 5 | False | [16, 3, 7] |
| c_bi_ey_range | smallint(6) | 559 | 98.5891% | 0 | 2 | False | [2, 0] |
| c_source | INTEGER(11) | 18 | 3.1746% | 0 | 33 | False | [64847, 2066, 0] |
| c_pages | varchar(255) | 17 | 2.9982% | 9 | 381 | False | ["一三九 李範墓誌", "lgid=1197282", "lgid=152451"] |
| c_notes | TEXT | 275 | 48.5009% | 1 | 284 | False | ["永安縣永定院僧", "歸隱西山香城寺潛心理學攜一僕與居尋遺與僧共晨夕而已山居十餘年而卒", "聘主白鹿書院"] |
| c_created_by | varchar(255) | 217 | 38.2716% | 7 | 31 | False | ["赵天祎", "李铮", "load"] |
| c_modified_by | varchar(255) | 467 | 82.3633% | 15 | 20 | False | ["LiuBangdong", "Ning Hao", "劉慧楠"] |
| c_created_date | TEXT | 224 | 39.5062% | 0 | 171 | False | ["2025-11-23 00:00:00", "2021-06-30 00:00:00", "2022-05-14 00:00:00"] |
| c_modified_date | TEXT | 482 | 85.0088% | 0 | 36 | False | ["2024-06-18 00:00:00", "2024-08-30 00:00:00", "2025-05-11 00:00:00"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

| source key | target | basis | matched/non-NULL | match rate |
| --- | --- | --- | --- | --- |
| c_personid | BIOG_MAIN.c_personid | inferred join key | 567/567 | 100.0000% |
| c_bi_role_code | BIOG_INST_CODES.c_bi_role_code | inferred join key | 567/567 | 100.0000% |

## First five rows

| c_personid | c_inst_name_code | c_inst_code | c_bi_role_code | c_bi_begin_year | c_bi_by_nh_code | c_bi_by_nh_year | c_bi_by_range | c_bi_end_year | c_bi_ey_nh_code | c_bi_ey_nh_year | c_bi_ey_range | c_source | c_pages | c_notes | c_created_by | c_modified_by | c_created_date | c_modified_date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 696576 | 0 | 0 | 0 |  |  |  |  |  |  |  |  | 64847 | 一三九 李範墓誌 | 永安縣永定院僧 | 赵天祎 |  | 2025-11-23 00:00:00 |  |
| 438255 | 1625 | 0 | 0 |  |  |  |  |  |  |  |  | 2066 | lgid=1197282 | 歸隱西山香城寺潛心理學攜一僕與居尋遺與僧共晨夕而已山居十餘年而卒 | 李铮 |  | 2021-06-30 00:00:00 |  |
| 30631 | 12 | 14 | 0 |  |  |  |  |  |  |  |  | 0 |  | 聘主白鹿書院 | 李铮 |  | 2022-05-14 00:00:00 |  |
| 27852 | 397 | 4008 | 0 |  | 18 |  |  |  |  |  |  |  |  | 出處：全元文，第25冊 P420。直學 | load |  | 2017-04-19 00:00:00 |  |
| 699249 | 0 | 0 | 5 |  |  |  |  |  |  |  |  | 39136 | lgid=152451 |  | 劉慧楠 |  | 2026-03-16 22:52:50 |  |
