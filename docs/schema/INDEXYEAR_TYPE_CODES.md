# INDEXYEAR_TYPE_CODES

Rows: **31**; columns: **4**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_index_year_type_code | varchar(191) | 0 | 0.0000% | 0 | 31 | False | ["00", "01", "02"] |
| c_index_year_type_desc | varchar(255) | 0 | 0.0000% | 0 | 31 | False | ["Unknown", "Based on Birth Year", "Based on Death Year - Death Age + 1"] |
| c_index_year_type_hz | varchar(255) | 0 | 0.0000% | 0 | 31 | False | ["未詳", "據生年", "據卒年 - 享年 + 1"] |
| c_notes | varchar(255) | 2 | 6.4516% | 0 | 20 | False | ["not derived:  no rule", "old Rule 2", "old Rule 4W"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_index_year_type_code | c_index_year_type_desc | c_index_year_type_hz | c_notes |
| --- | --- | --- | --- |
| 00 | Unknown | 未詳 |  |
| 01 | Based on Birth Year | 據生年 | not derived:  no rule |
| 02 | Based on Death Year - Death Age + 1 | 據卒年 - 享年 + 1 | old Rule 2 |
| 03 | Based on Husband's Birth Year + 3 | 據其夫生年 + 3 | old Rule 4W |
| 04 | Based on Husband's Index Year + 3 | 據其夫指數年 + 3 | this is for the looping routine to catch all otherwise unspecified derived index years |
