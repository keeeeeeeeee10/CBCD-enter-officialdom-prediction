# SOCIAL_INSTITUTION_NAME_CODES

Rows: **2,603**; columns: **3**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_inst_name_code | smallint(6) | 0 | 0.0000% | 0 | 2603 | False | [0, 1, 2] |
| c_inst_name_hz | varchar(255) | 0 | 0.0000% | 0 | 2602 | False | ["[未詳]", "安定書院", "安定寺"] |
| c_inst_name_py | varchar(255) | 0 | 0.0000% | 1 | 2492 | False | ["[Unknown]", "Anding shuyuan", "Andingsi"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_inst_name_code | c_inst_name_hz | c_inst_name_py |
| --- | --- | --- |
| 0 | [未詳] | [Unknown] |
| 1 | 安定書院 | Anding shuyuan |
| 2 | 安定寺 | Andingsi |
| 3 | 安國禪寺 | Anguochansi |
| 4 | 安湖書院 | Anhu shuyuan |
