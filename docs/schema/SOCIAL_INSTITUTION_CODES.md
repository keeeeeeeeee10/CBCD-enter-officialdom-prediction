# SOCIAL_INSTITUTION_CODES

Rows: **4,012**; columns: **19**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_inst_name_code | smallint(6) | 0 | 0.0000% | 0 | 2603 | False | [0, 1, 2] |
| c_inst_code | smallint(6) | 0 | 0.0000% | 0 | 4012 | False | [0, 1, 2] |
| c_inst_type_code | smallint(6) | 0 | 0.0000% | 0 | 7 | False | [0, 1, 2] |
| c_inst_begin_year | smallint(6) | 497 | 12.3878% | 0 | 581 | False | [0, 1250, 1272] |
| c_by_nianhao_code | smallint(6) | 619 | 15.4287% | 0 | 73 | False | [0, 538, 593] |
| c_by_nianhao_year | smallint(6) | 619 | 15.4287% | 0 | 26 | False | [0, 1, 2] |
| c_by_year_range | smallint(6) | 579 | 14.4317% | 0 | 4 | False | [0, 2, -1] |
| c_inst_begin_dy | smallint(6) | 237 | 5.9073% | 0 | 8 | False | [0, 15, 18] |
| c_inst_floruit_dy | smallint(6) | 1028 | 25.6231% | 0 | 4 | False | [18, 20, 19] |
| c_inst_first_known_year | smallint(6) | 4012 | 100.0000% | 0 | 0 | False | [] |
| c_inst_end_year | smallint(6) | 4012 | 100.0000% | 0 | 0 | False | [] |
| c_ey_nianhao_code | smallint(6) | 4012 | 100.0000% | 0 | 0 | False | [] |
| c_ey_nianhao_year | smallint(6) | 4012 | 100.0000% | 0 | 0 | False | [] |
| c_ey_year_range | smallint(6) | 4012 | 100.0000% | 0 | 0 | False | [] |
| c_inst_end_dy | smallint(6) | 4010 | 99.9501% | 0 | 1 | False | [19] |
| c_inst_last_known_year | smallint(6) | 4012 | 100.0000% | 0 | 0 | False | [] |
| c_source | INTEGER(11) | 231 | 5.7577% | 0 | 31 | False | [0, 9599, 27842] |
| c_pages | varchar(255) | 349 | 8.6989% | 0 | 707 | False | ["5461", "6140", "14182"] |
| c_notes | TEXT | 815 | 20.3141% | 0 | 3054 | False | ["from L.Walton: YR II.1317; II,1954; Lao, p.122", "from L.Walton: 大明一統志 12.8a", "元代釋法憶113233居雞足山安定寺"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_inst_name_code | c_inst_code | c_inst_type_code | c_inst_begin_year | c_by_nianhao_code | c_by_nianhao_year | c_by_year_range | c_inst_begin_dy | c_inst_floruit_dy | c_inst_first_known_year | c_inst_end_year | c_ey_nianhao_code | c_ey_nianhao_year | c_ey_year_range | c_inst_end_dy | c_inst_last_known_year | c_source | c_pages | c_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |  |  |  |  |  |  |  |  | 0 |  |  |
| 1 | 1 | 1 | 1250 |  |  | 2 | 15 | 18 |  |  |  |  |  |  |  | 9599 | 5461 | from L.Walton: YR II.1317; II,1954; Lao, p.122 |
| 1 | 2 | 1 |  |  |  |  | 18 | 18 |  |  |  |  |  |  |  | 9599 | 6140 | from L.Walton: 大明一統志 12.8a |
| 2 | 3 | 2 |  |  |  |  |  | 18 |  |  |  |  |  |  |  | 9599 | 14182 | 元代釋法憶113233居雞足山安定寺 |
| 3 | 4 | 2 |  |  |  |  |  | 18 |  |  |  |  |  |  |  | 9599 | 14019 | 元代釋允清113075居衢州子湖安國禪寺 |
