# KINSHIP_CODES

Rows: **488**; columns: **13**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_kincode | smallint(6) | 0 | 0.0000% | 0 | 488 | False | [-10000, -1, 0] |
| c_kin_pair1 | smallint(6) | 0 | 0.0000% | 0 | 296 | False | [-10000, -1, 0] |
| c_kin_pair2 | smallint(6) | 0 | 0.0000% | 0 | 156 | False | [-10000, -1, 0] |
| c_kin_pair_notes | varchar(255) | 352 | 72.1311% | 2 | 131 | False | ["Not Applicable", "G+17H", "G+7H"] |
| c_kinrel_chn | varchar(255) | 0 | 0.0000% | 0 | 488 | False | ["非可用", "[missing data]", "未詳"] |
| c_kinrel | varchar(255) | 0 | 0.0000% | 0 | 485 | False | ["\t\r\nNot Applicable", "[missing data]", "U"] |
| c_kinrel_alt | varchar(255) | 6 | 1.2295% | 0 | 482 | False | ["Not Applicable", "[missing data]", "undetermined"] |
| c_pick_sorting | smallint(6) | 80 | 16.3934% | 0 | 31 | False | [10000, 9999, 50] |
| c_upstep | smallint(6) | 0 | 0.0000% | 0 | 51 | False | [100, 0, 99] |
| c_dwnstep | smallint(6) | 0 | 0.0000% | 0 | 51 | False | [100, 0, 99] |
| c_marstep | smallint(6) | 0 | 0.0000% | 0 | 5 | False | [100, 0, 99] |
| c_colstep | smallint(6) | 0 | 0.0000% | 0 | 5 | False | [100, 0, 99] |
| c_kinrel_simplified | varchar(255) | 0 | 0.0000% | 0 | 325 | False | ["ZZZZZZZ", "[missing data]", "U"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_kincode | c_kin_pair1 | c_kin_pair2 | c_kin_pair_notes | c_kinrel_chn | c_kinrel | c_kinrel_alt | c_pick_sorting | c_upstep | c_dwnstep | c_marstep | c_colstep | c_kinrel_simplified |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| -10000 | -10000 | -10000 | Not Applicable | 非可用 | 	  Not Applicable | Not Applicable | 10000 | 100 | 100 | 100 | 100 | ZZZZZZZ |
| -1 | -1 | -1 |  | [missing data] | [missing data] | [missing data] | 10000 | 0 | 0 | 0 | 0 | [missing data] |
| 0 | 0 | 0 |  | 未詳 | U | undetermined | 9999 | 99 | 99 | 99 | 99 | U |
| 2 | 303 | 303 |  | 直系祖先 | G-n | G-n, lineal ancestor, generation unknown | 50 | 99 | 0 | 0 | 0 | G-n |
| 3 | 301 | -10000 |  | 妻之直系祖先 | WG-n | Ancestor of wife | 150 | 99 | 0 | 1 | 0 | WG-n |
