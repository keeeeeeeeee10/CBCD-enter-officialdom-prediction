# HOUSEHOLD_STATUS_CODES

Rows: **34**; columns: **3**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_household_status_code | smallint(6) | 0 | 0.0000% | 0 | 34 | False | [0, 1, 2] |
| c_household_status_desc | varchar(255) | 0 | 0.0000% | 0 | 34 | False | ["Unknown", "Civilian household", "Military household"] |
| c_household_status_desc_chn | varchar(255) | 0 | 0.0000% | 0 | 34 | False | ["未詳", "民戶", "軍戶"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_household_status_code | c_household_status_desc | c_household_status_desc_chn |
| --- | --- | --- |
| 0 | Unknown | 未詳 |
| 1 | Civilian household | 民戶 |
| 2 | Military household | 軍戶 |
| 3 | Artisan household | 匠戶 |
| 4 | Official household | 官戶 |
