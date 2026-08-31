# ENTRY_CODES

Rows: **273**; columns: **3**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_entry_code | smallint(6) | 0 | 0.0000% | 0 | 273 | False | [-1, 0, 1] |
| c_entry_desc | varchar(255) | 0 | 0.0000% | 0 | 272 | False | ["[Missing Data]", "not available or applicable", "abdication of previous emperor"] |
| c_entry_desc_chn | varchar(255) | 0 | 0.0000% | 0 | 273 | False | ["[Missing Data]", "未知", "前帝遜位"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_entry_code | c_entry_desc | c_entry_desc_chn |
| --- | --- | --- |
| -1 | [Missing Data] | [Missing Data] |
| 0 | not available or applicable | 未知 |
| 1 | abdication of previous emperor | 前帝遜位 |
| 4 | To be Deleted: betrothal | 臨時保留，待考。 |
| 5 | promotion from clerical positions | 胥吏出職 |
