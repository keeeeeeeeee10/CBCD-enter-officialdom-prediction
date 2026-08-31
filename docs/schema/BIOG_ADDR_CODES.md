# BIOG_ADDR_CODES

Rows: **22**; columns: **6**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_addr_type | smallint(6) | 0 | 0.0000% | 0 | 22 | False | [-1, 0, 1] |
| c_addr_desc | varchar(255) | 0 | 0.0000% | 0 | 22 | False | ["[Missing Data]", "unknown", "Basic Affiliation"] |
| c_addr_desc_chn | varchar(255) | 0 | 0.0000% | 0 | 22 | False | ["[缺乏信息]", "未詳", "籍貫(基本地址)"] |
| c_addr_note | varchar(255) | 9 | 40.9091% | 0 | 12 | False | ["This field is different from the other fields. It assigns a person to a single place for indexing purposes. This field requires judgment based on information… |
| c_index_addr_rank | smallint(6) | 0 | 0.0000% | 0 | 10 | False | [100, 1, 5] |
| c_index_addr_default_rank | smallint(6) | 0 | 0.0000% | 0 | 10 | False | [100, 1, 5] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_addr_type | c_addr_desc | c_addr_desc_chn | c_addr_note | c_index_addr_rank | c_index_addr_default_rank |
| --- | --- | --- | --- | --- | --- |
| -1 | [Missing Data] | [缺乏信息] |  | 100 | 100 |
| 0 | unknown | 未詳 |  | 100 | 100 |
| 1 | Basic Affiliation | 籍貫(基本地址) | This field is different from the other fields. It assigns a person to a single place for indexing purposes. This field requires judgment based on information i… | 1 | 1 |
| 2 | Moved to | 遷住地 | multiple entries possible | 5 | 5 |
| 3 | Former Address | 前住地 | This field is used for the address which people left when they migrated to another place. It is only used for the person or generation that migrates. It may be… | 100 | 100 |
