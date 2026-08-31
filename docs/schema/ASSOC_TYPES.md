# ASSOC_TYPES

Rows: **45**; columns: **7**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_assoc_type_code | varchar(255) | 0 | 0.0000% | 0 | 45 | False | ["01", "0101", "0102"] |
| c_assoc_type_desc | varchar(255) | 0 | 0.0000% | 0 | 43 | False | ["Associations (General)", "Association through common membership", "Social Interactions"] |
| c_assoc_type_desc_chn | varchar(255) | 0 | 0.0000% | 0 | 43 | False | ["社會關係（籠統）", "同為……之成員", "社會交際"] |
| c_assoc_type_parent_id | varchar(255) | 0 | 0.0000% | 0 | 11 | False | ["0", "01", "02"] |
| c_assoc_type_level | smallint(6) | 0 | 0.0000% | 0 | 2 | False | [0, 1] |
| c_assoc_type_sortorder | smallint(6) | 0 | 0.0000% | 0 | 36 | False | [1, 2, 3] |
| c_assoc_type_short_desc | varchar(255) | 0 | 0.0000% | 0 | 36 | False | ["Association", "Membership", "Social Interaction"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_assoc_type_code | c_assoc_type_desc | c_assoc_type_desc_chn | c_assoc_type_parent_id | c_assoc_type_level | c_assoc_type_sortorder | c_assoc_type_short_desc |
| --- | --- | --- | --- | --- | --- | --- |
| 01 | Associations (General) | 社會關係（籠統） | 0 | 0 | 1 | Association |
| 0101 | Associations (General) | 社會關係（籠統） | 01 | 1 | 1 | Association |
| 0102 | Association through common membership | 同為……之成員 | 01 | 1 | 2 | Membership |
| 0103 | Social Interactions | 社會交際 | 01 | 1 | 3 | Social Interaction |
| 02 | Scholarship | 學術關係類 | 0 | 0 | 2 | Scholarship |
