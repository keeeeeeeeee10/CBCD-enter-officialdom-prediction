# STATUS_CODES

Rows: **285**; columns: **3**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_status_code | smallint(6) | 0 | 0.0000% | 0 | 285 | False | [-1, 0, 2] |
| c_status_desc | varchar(255) | 0 | 0.0000% | 0 | 285 | False | ["[Missing Data]", "[Unknown]", "army officer"] |
| c_status_desc_chn | varchar(255) | 0 | 0.0000% | 0 | 285 | False | ["[Missing Data]", "[未詳]", "武將"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_status_code | c_status_desc | c_status_desc_chn |
| --- | --- | --- |
| -1 | [Missing Data] | [Missing Data] |
| 0 | [Unknown] | [未詳] |
| 2 | army officer | 武將 |
| 3 | artisan | 工匠 |
| 4 | astronomer | 天文學家（星象家） |
