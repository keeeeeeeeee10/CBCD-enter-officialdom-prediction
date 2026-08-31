# TEXT_ROLE_CODES

Rows: **12**; columns: **3**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_role_id | smallint(6) | 0 | 0.0000% | 0 | 12 | False | [0, 1, 2] |
| c_role_desc | varchar(255) | 0 | 0.0000% | 0 | 12 | False | ["unknown", "author", "editor"] |
| c_role_desc_chn | varchar(255) | 0 | 0.0000% | 0 | 12 | False | ["未詳", "撰著者", "編輯者"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_role_id | c_role_desc | c_role_desc_chn |
| --- | --- | --- |
| 0 | unknown | 未詳 |
| 1 | author | 撰著者 |
| 2 | editor | 編輯者 |
| 3 | compiler | 編纂者 |
| 4 | publisher | 出版者 |
