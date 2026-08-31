# STATUS_CODE_TYPE_REL

Rows: **285**; columns: **2**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_status_code | smallint(6) | 0 | 0.0000% | 0 | 285 | False | [-1, 0, 2] |
| c_status_type_code | varchar(255) | 0 | 0.0000% | 0 | 14 | False | ["00", "01", "02"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_status_code | c_status_type_code |
| --- | --- |
| -1 | 00 |
| 0 | 00 |
| 2 | 01 |
| 3 | 01 |
| 4 | 02 |
