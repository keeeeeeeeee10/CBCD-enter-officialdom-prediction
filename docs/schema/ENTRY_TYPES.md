# ENTRY_TYPES

Rows: **29**; columns: **6**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_entry_type | varchar(255) | 0 | 0.0000% | 0 | 29 | False | ["00", "01", "02"] |
| c_entry_type_desc | varchar(255) | 0 | 0.0000% | 0 | 29 | False | ["Unknown Method of Entry", "Palace", "Kinship"] |
| c_entry_type_desc_chn | varchar(255) | 0 | 0.0000% | 0 | 29 | False | ["未知入仕途徑", "宮廷門", "血親門"] |
| c_entry_type_parent_id | varchar(255) | 0 | 0.0000% | 0 | 4 | False | ["0", "04", "0401"] |
| c_entry_type_level | smallint(6) | 1 | 3.4483% | 0 | 3 | False | [0, 1, 2] |
| c_entry_type_sortorder | smallint(6) | 3 | 10.3448% | 0 | 24 | False | [1, 2, 3] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_entry_type | c_entry_type_desc | c_entry_type_desc_chn | c_entry_type_parent_id | c_entry_type_level | c_entry_type_sortorder |
| --- | --- | --- | --- | --- | --- |
| 00 | Unknown Method of Entry | 未知入仕途徑 | 0 | 0 | 1 |
| 01 | Palace | 宮廷門 | 0 | 0 | 2 |
| 02 | Kinship | 血親門 | 0 | 0 | 3 |
| 03 | Marriage | 姻親門 | 0 | 0 | 4 |
| 04 | Examination | 科舉門 | 0 | 0 | 5 |
