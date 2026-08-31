# ASSUME_OFFICE_CODES

Rows: **6**; columns: **3**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_assume_office_code | smallint(6) | 0 | 0.0000% | 0 | 6 | False | [0, 1, 2] |
| c_assume_office_desc_chn | varchar(255) | 0 | 0.0000% | 0 | 6 | False | ["未詳", "赴任", "辭不就"] |
| c_assume_office_desc | varchar(255) | 0 | 0.0000% | 0 | 6 | False | ["Unknown", "Assumed the office", "Declined the office"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_assume_office_code | c_assume_office_desc_chn | c_assume_office_desc |
| --- | --- | --- |
| 0 | 未詳 | Unknown |
| 1 | 赴任 | Assumed the office |
| 2 | 辭不就 | Declined the office |
| 3 | 未赴任而卒 | Died before assuming the office |
| 4 | 未赴任而改命 | Appointment changed before assuming the office |
