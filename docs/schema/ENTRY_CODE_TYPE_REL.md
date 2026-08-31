# ENTRY_CODE_TYPE_REL

Rows: **284**; columns: **2**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_entry_code | smallint(6) | 0 | 0.0000% | 0 | 272 | False | [0, 1, 4] |
| c_entry_type | varchar(255) | 0 | 0.0000% | 0 | 29 | False | ["00", "01", "99"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_entry_code | c_entry_type |
| --- | --- |
| 0 | 00 |
| 1 | 01 |
| 4 | 99 |
| 5 | 90 |
| 7 | 12 |
