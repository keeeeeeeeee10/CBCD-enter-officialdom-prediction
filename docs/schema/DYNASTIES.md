# DYNASTIES

Rows: **85**; columns: **6**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_dy | smallint(6) | 0 | 0.0000% | 0 | 85 | False | [0, 1, 2] |
| c_dynasty | varchar(255) | 0 | 0.0000% | 0 | 84 | False | ["unknown", "Pre-Han", "QinHan"] |
| c_dynasty_chn | varchar(255) | 0 | 0.0000% | 0 | 85 | False | ["未詳", "漢前", "秦漢"] |
| c_start | smallint(6) | 0 | 0.0000% | 0 | 61 | False | [0, -1100, -221] |
| c_end | smallint(6) | 0 | 0.0000% | 0 | 69 | False | [0, -206, 220] |
| c_sort | smallint(6) | 0 | 0.0000% | 0 | 85 | False | [0, 1, 2] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_dy | c_dynasty | c_dynasty_chn | c_start | c_end | c_sort |
| --- | --- | --- | --- | --- | --- |
| 0 | unknown | 未詳 | 0 | 0 | 0 |
| 1 | Pre-Han | 漢前 | -1100 | -206 | 1 |
| 2 | QinHan | 秦漢 | -221 | 220 | 2 |
| 3 | SanGuo | 三國 | 220 | 265 | 8 |
| 4 | NanBei Chao | 南北朝 | 420 | 589 | 15 |
