# STATUS_TYPES

Rows: **14**; columns: **4**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_status_type_code | varchar(255) | 0 | 0.0000% | 0 | 14 | False | ["00", "01", "02"] |
| c_status_type_desc | varchar(255) | 0 | 0.0000% | 0 | 14 | False | ["[Unknown]", "Occupation", "Scholarship"] |
| c_status_type_chn | varchar(255) | 0 | 0.0000% | 0 | 14 | False | ["[未詳]", "事業", "學術"] |
| c_status_type_parent_code | varchar(255) | 13 | 92.8571% | 0 | 1 | False | ["02"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_status_type_code | c_status_type_desc | c_status_type_chn | c_status_type_parent_code |
| --- | --- | --- | --- |
| 00 | [Unknown] | [未詳] |  |
| 01 | Occupation | 事業 |  |
| 02 | Scholarship | 學術 |  |
| 0201 | Neo-Confucian | 理學 | 02 |
| 03 | Military Distinction | 武功 |  |
