# STATUS_DATA

Rows: **73,250**; columns: **19**.

Person identifier fields observed: `c_personid`.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_personid | INTEGER(11) | 0 | 0.0000% | 0 | 56344 | False | [1, 2, 3] |
| c_sequence | smallint(6) | 0 | 0.0000% | 0 | 9 | False | [1, 2, 0] |
| c_status_code | smallint(6) | 0 | 0.0000% | 0 | 270 | False | [68, 34, 14] |
| c_firstyear | smallint(6) | 43223 | 59.0075% | 0 | 537 | False | [0, 1130, 1081] |
| c_fy_nh_code | smallint(6) | 18601 | 25.3939% | 0 | 96 | False | [0, 541, 529] |
| c_fy_nh_year | smallint(6) | 70452 | 96.1802% | 0 | 63 | False | [0, 1, 2] |
| c_fy_range | smallint(6) | 71878 | 98.1270% | 0 | 4 | False | [0, 2, 1] |
| c_lastyear | smallint(6) | 43723 | 59.6901% | 0 | 387 | False | [0, 1130, 1081] |
| c_ly_nh_code | smallint(6) | 19108 | 26.0860% | 0 | 52 | False | [0, 432, 507] |
| c_ly_nh_year | smallint(6) | 70954 | 96.8655% | 0 | 20 | False | [0, 3, 8] |
| c_ly_range | smallint(6) | 71931 | 98.1993% | 0 | 2 | False | [0, -1] |
| c_supplement | varchar(255) | 70738 | 96.5706% | 2349 | 133 | False | ["唐宋八大家", "楚州州學", "詩聖"] |
| c_source | INTEGER(11) | 23 | 0.0314% | 0 | 140 | False | [0, 7596, 2986] |
| c_pages | varchar(255) | 33884 | 46.2580% | 1201 | 17605 | False | ["3024", "10701", "10729"] |
| c_notes | TEXT | 56487 | 77.1154% | 1407 | 5951 | False | ["From Hartwell's STATUS code.", "平居未嘗以言徇物 以色假人 王安石用事 嶷然不少屈 以是望高一時", "《全唐詩・卷762》(據唐代人物知識ベース)。"] |
| c_created_by | varchar(255) | 0 | 0.0000% | 0 | 100 | False | ["TTS", "load", "BDLYH"] |
| c_modified_by | varchar(255) | 69811 | 95.3051% | 2339 | 75 | False | ["BDGSX", "BDWANGHY", "BDDYJ"] |
| c_created_date | TEXT | 0 | 0.0000% | 0 | 6212 | False | ["2007-03-12 00:00:00", "2010-12-01 00:00:00", "2024-10-10 00:00:00"] |
| c_modified_date | TEXT | 72150 | 98.4983% | 0 | 592 | False | ["2008-07-05 00:00:00", "2008-01-12 00:00:00", "2007-05-11 00:00:00"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

| source key | target | basis | matched/non-NULL | match rate |
| --- | --- | --- | --- | --- |
| c_personid | BIOG_MAIN.c_personid | inferred join key | 73250/73250 | 100.0000% |
| c_status_code | STATUS_CODES.c_status_code | inferred join key | 73250/73250 | 100.0000% |

## First five rows

| c_personid | c_sequence | c_status_code | c_firstyear | c_fy_nh_code | c_fy_nh_year | c_fy_range | c_lastyear | c_ly_nh_code | c_ly_nh_year | c_ly_range | c_supplement | c_source | c_pages | c_notes | c_created_by | c_modified_by | c_created_date | c_modified_date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 68 | 0 | 0 |  |  | 0 | 0 |  |  |  | 0 |  |  | TTS |  | 2007-03-12 00:00:00 |  |
| 1 | 2 | 34 | 0 | 0 |  |  | 0 | 0 |  |  |  | 0 |  |  | TTS |  | 2007-03-12 00:00:00 |  |
| 2 | 1 | 68 | 0 | 0 |  |  | 0 | 0 |  |  |  | 0 |  |  | TTS |  | 2007-03-12 00:00:00 |  |
| 3 | 0 | 14 |  | 0 |  |  |  | 0 |  |  |  | 7596 | 3024 |  | load |  | 2010-12-01 00:00:00 |  |
| 3 | 1 | 68 | 0 | 0 |  |  | 0 | 0 |  |  |  | 0 |  |  | TTS |  | 2007-03-12 00:00:00 |  |
