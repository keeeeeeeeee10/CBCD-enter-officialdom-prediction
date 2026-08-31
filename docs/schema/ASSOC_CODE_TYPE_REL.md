# ASSOC_CODE_TYPE_REL

Rows: **463**; columns: **2**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_assoc_code | smallint(6) | 0 | 0.0000% | 0 | 463 | False | [0, 4, 5] |
| c_assoc_type_code | varchar(255) | 0 | 0.0000% | 0 | 34 | False | ["0101", "0405", "0301"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_assoc_code | c_assoc_type_code |
| --- | --- |
| 0 | 0101 |
| 4 | 0405 |
| 5 | 0405 |
| 7 | 0405 |
| 8 | 0405 |
