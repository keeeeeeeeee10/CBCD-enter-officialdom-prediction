# BIOG_INST_CODES

Rows: **26**; columns: **4**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_bi_role_code | smallint(6) | 0 | 0.0000% | 0 | 26 | False | [0, 1, 2] |
| c_bi_role_desc | varchar(255) | 0 | 0.0000% | 0 | 26 | False | ["[Unknown]", "author of inscription for", "requested of inscription for"] |
| c_bi_role_chn | varchar(255) | 0 | 0.0000% | 0 | 26 | False | ["[角色未詳]", "為…做記/碑文", "為…求記/碑文"] |
| c_notes | varchar(255) | 24 | 92.3077% | 0 | 2 | False | ["sacrificed to at temple", "memorial arch commemorates"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_bi_role_code | c_bi_role_desc | c_bi_role_chn | c_notes |
| --- | --- | --- | --- |
| 0 | [Unknown] | [角色未詳] |  |
| 1 | author of inscription for | 為…做記/碑文 |  |
| 2 | requested of inscription for | 為…求記/碑文 |  |
| 3 | requested a honor for | ***為…求 (title) placques 匾額 |  |
| 4 | gave a name to | 為...命名 |  |
