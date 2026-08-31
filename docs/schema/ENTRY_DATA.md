# ENTRY_DATA

Rows: **264,775**; columns: **28**.

Person identifier fields observed: `c_personid`, `c_kin_id`, `c_assoc_id`.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_personid | INTEGER(11) | 0 | 0.0000% | 0 | 119858 | True | [397212, 420579, 578680] |
| c_entry_code | smallint(6) | 0 | 0.0000% | 0 | 226 | True | [0, 1, 4] |
| c_sequence | smallint(6) | 0 | 0.0000% | 0 | 8 | True | [1, 0, 2] |
| c_exam_rank | varchar(255) | 154925 | 58.5119% | 18530 | 2255 | True | ["0", "高等", "1"] |
| c_kin_code | smallint(6) | 0 | 0.0000% | 0 | 25 | True | [0, 62, 75] |
| c_kin_id | INTEGER(11) | 0 | 0.0000% | 0 | 169 | True | [0, 10565, 25088] |
| c_assoc_code | smallint(6) | 0 | 0.0000% | 0 | 5 | True | [0, 13, 14] |
| c_assoc_id | INTEGER(11) | 0 | 0.0000% | 0 | 10 | True | [0, 8113, 135997] |
| c_year | smallint(6) | 0 | 0.0000% | 0 | 1034 | True | [0, 1840, 1618] |
| c_age | smallint(6) | 236592 | 89.3559% | 0 | 71 | True | [37, 28, 46] |
| c_entry_nh_id | smallint(6) | 171092 | 64.6179% | 0 | 143 | True | [664, 652, 663] |
| c_entry_nh_year | smallint(6) | 186327 | 70.3718% | 0 | 66 | True | [20, 46, 23] |
| c_entry_dy | smallint(6) | 264775 | 100.0000% | 0 | 0 | True | [] |
| c_entry_range | smallint(6) | 225042 | 84.9937% | 0 | 6 | True | [2, 0, 1] |
| c_inst_code | smallint(6) | 0 | 0.0000% | 0 | 1 | True | [0] |
| c_inst_name_code | smallint(6) | 0 | 0.0000% | 0 | 1 | True | [0] |
| c_exam_field | varchar(255) | 230393 | 87.0146% | 19769 | 54 | True | ["服勤詞學經明行修科", "書", "詩賦"] |
| c_entry_addr_id | INTEGER(11) | 249553 | 94.2510% | 0 | 85 | True | [0, 18339, 400001] |
| c_parental_status_code | smallint(6) | 176333 | 66.5973% | 0 | 7 | True | [0, 3, 2] |
| c_attempt_count | smallint(6) | 261659 | 98.8232% | 0 | 8 | True | [0, 5, 1] |
| c_source | INTEGER(11) | 68 | 0.0257% | 0 | 380 | True | [0, 39136, 67015] |
| c_pages | varchar(255) | 12147 | 4.5877% | 249 | 58070 | True | ["lgid=152243", "lgid= 870130-870131", "lgid=293912"] |
| c_notes | TEXT | 227354 | 85.8669% | 19667 | 3399 | True | ["有缺字，\"萬□戊午以禮□□□初署\"", "亦由掾吏起○○○家", "[吏員]"] |
| c_posting_notes | varchar(255) | 158849 | 59.9940% | 17840 | 276 | True | ["0000000", "0025434", "0028871"] |
| c_created_by | varchar(255) | 0 | 0.0000% | 0 | 137 | True | ["李睿诗", "劉慧楠", "Gaomx"] |
| c_modified_by | varchar(255) | 240562 | 90.8553% | 20025 | 109 | True | ["BDGL", "BDLYH", "BDZWZ"] |
| c_created_date | TEXT | 1 | 0.0004% | 0 | 2570 | True | ["2025-12-14 00:00:00", "2026-01-07 22:00:25", "2024-07-07 00:00:00"] |
| c_modified_date | TEXT | 260587 | 98.4183% | 0 | 780 | True | ["2013-05-31 00:00:00", "2008-05-10 00:00:00", "2008-07-03 00:00:00"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

| source key | target | basis | matched/non-NULL | match rate |
| --- | --- | --- | --- | --- |
| c_personid | BIOG_MAIN.c_personid | inferred join key | 264775/264775 | 100.0000% |
| c_entry_code | ENTRY_CODES.c_entry_code | inferred join key | 264775/264775 | 100.0000% |
| c_kin_code | KINSHIP_CODES.c_kincode | inferred join key | 264775/264775 | 100.0000% |
| c_kin_id | BIOG_MAIN.c_personid | inferred join key | 264775/264775 | 100.0000% |
| c_assoc_code | ASSOC_CODES.c_assoc_code | inferred join key | 264775/264775 | 100.0000% |
| c_assoc_id | BIOG_MAIN.c_personid | inferred join key | 264775/264775 | 100.0000% |
| c_entry_dy | DYNASTIES.c_dy | inferred join key | 0/0 |  |
| c_entry_addr_id | ADDR_CODES.c_addr_id | inferred join key | 15218/15222 | 99.9737% |

## First five rows

| c_personid | c_entry_code | c_sequence | c_exam_rank | c_kin_code | c_kin_id | c_assoc_code | c_assoc_id | c_year | c_age | c_entry_nh_id | c_entry_nh_year | c_entry_dy | c_entry_range | c_inst_code | c_inst_name_code | c_exam_field | c_entry_addr_id | c_parental_status_code | c_attempt_count | c_source | c_pages | c_notes | c_posting_notes | c_created_by | c_modified_by | c_created_date | c_modified_date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 47386 | 0 | 0 |  | 0 | 0 | 0 | 0 | 1112 |  | 536 | 2 |  |  | 0 | 0 |  | 0 |  |  | 0 |  |  |  | Tang Xinan |  | 2025-05-13 00:00:00 |  |
| 397212 | 0 | 1 |  | 0 | 0 | 0 | 0 | 0 |  |  |  |  |  | 0 | 0 |  | 0 |  |  | 0 |  |  |  | 李睿诗 |  | 2025-12-14 00:00:00 |  |
| 415584 | 0 | 0 |  | 0 | 0 | 0 | 0 | 0 |  |  |  |  |  | 0 | 0 |  | 0 |  |  | 38533 | lgid=664673 |  |  | 李睿诗 |  | 2025-12-01 00:00:00 |  |
| 420579 | 0 | 0 |  | 0 | 0 | 0 | 0 | 1840 |  | 664 | 20 |  |  | 0 | 0 |  | 0 |  |  | 39136 | lgid=152243 |  |  | 劉慧楠 |  | 2026-01-07 22:00:25 |  |
| 578247 | 0 | 0 |  | 0 | 0 | 0 | 0 | 0 |  |  |  |  |  | 0 | 0 |  | 0 |  |  | 64847 | 四九四  甘子華及夫人李氏墓記券 | 試太學覃恩免解待省進士 |  | 焦克龍 |  | 2024-06-19 00:00:00 |  |
