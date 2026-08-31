# PARENTAL_STATUS_CODES

Rows: **7**; columns: **3**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_parental_status_code | smallint(6) | 0 | 0.0000% | 0 | 7 | False | [0, 1, 2] |
| c_parental_status_desc | varchar(255) | 0 | 0.0000% | 0 | 7 | False | ["[Unknown]", "Both parent alive", "Both parent died"] |
| c_parental_status_desc_chn | varchar(255) | 0 | 0.0000% | 0 | 7 | False | ["[未詳]", "具慶;雙侍;重侍", "永感"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_parental_status_code | c_parental_status_desc | c_parental_status_desc_chn |
| --- | --- | --- |
| 0 | [Unknown] | [未詳] |
| 1 | Both parent alive | 具慶;雙侍;重侍 |
| 2 | Both parent died | 永感 |
| 3 | Only one is alive | 偏侍 |
| 4 | Only the father is alive | 嚴侍 |
