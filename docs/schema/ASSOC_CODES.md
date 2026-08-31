# ASSOC_CODES

Rows: **498**; columns: **8**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_assoc_code | smallint(6) | 0 | 0.0000% | 0 | 498 | False | [-1, 0, 4] |
| c_assoc_pair | smallint(6) | 0 | 0.0000% | 0 | 498 | False | [-1, 0, 5] |
| c_assoc_pair2 | smallint(6) | 498 | 100.0000% | 0 | 0 | False | [] |
| c_assoc_desc | varchar(255) | 0 | 0.0000% | 0 | 498 | False | ["[Missing Data]", "[Undefined]", "Patron of (= Client was)"] |
| c_assoc_desc_chn | varchar(255) | 0 | 0.0000% | 0 | 493 | False | ["[缺乏信息]", "未詳", "是Y的恩主"] |
| c_assoc_role_type | varchar(255) | 2 | 0.4016% | 0 | 3 | False | ["A", "P", "M"] |
| c_sortorder | smallint(6) | 172 | 34.5382% | 0 | 321 | False | [1, 98, 99] |
| c_example | varchar(255) | 472 | 94.7791% | 0 | 19 | False | ["INCLUDES 先廟記", "以醫術事真宗藩邸。", "王埜：王子文詩序(後村大全集94/15)"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_assoc_code | c_assoc_pair | c_assoc_pair2 | c_assoc_desc | c_assoc_desc_chn | c_assoc_role_type | c_sortorder | c_example |
| --- | --- | --- | --- | --- | --- | --- | --- |
| -1 | -1 |  | [Missing Data] | [缺乏信息] |  |  |  |
| 0 | 0 |  | [Undefined] | 未詳 |  | 1 |  |
| 4 | 5 |  | Patron of (= Client was) | 是Y的恩主 | A | 98 |  |
| 5 | 4 |  | Patron was (= Client of) | 恩主是Y | P | 99 |  |
| 7 | 8 |  | Coalition member of | 黨羽為Y | P | 92 |  |
