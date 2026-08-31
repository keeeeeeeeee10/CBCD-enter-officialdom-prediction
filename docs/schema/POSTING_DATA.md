# POSTING_DATA

Rows: **590,835**; columns: **6**.

Person identifier fields observed: `c_personid`.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_personid | INTEGER(11) | 0 | 0.0000% | 0 | 144327 | True | [105278, 106175, 109230] |
| c_posting_id | INTEGER(11) | 0 | 0.0000% | 0 | 196945 | True | [6, 9, 12] |
| c_created_by | varchar(255) | 584218 | 98.8801% | 0 | 25 | True | ["陶恒", "李睿诗", "劉慧楠"] |
| c_created_date | TEXT | 584218 | 98.8801% | 0 | 2206 | True | ["2025-12-05 13:25:06", "2025-12-05 13:35:05", "2025-12-05 17:00:13"] |
| c_modified_by | varchar(255) | 589650 | 99.7994% | 0 | 24 | True | ["Ho Ho Hin", "刘昱宏", "李格非"] |
| c_modified_date | TEXT | 589650 | 99.7994% | 0 | 401 | True | ["2025-12-07 20:31:47", "2026-06-13 15:40:57", "2026-04-11 13:46:00"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

| source key | target | basis | matched/non-NULL | match rate |
| --- | --- | --- | --- | --- |
| c_personid | BIOG_MAIN.c_personid | inferred join key | 590835/590835 | 100.0000% |

## First five rows

| c_personid | c_posting_id | c_created_by | c_created_date | c_modified_by | c_modified_date |
| --- | --- | --- | --- | --- | --- |
| 104772 | 4 |  |  |  |  |
| 104979 | 5 |  |  |  |  |
| 105278 | 6 |  |  |  |  |
| 106107 | 7 |  |  |  |  |
| 106107 | 8 |  |  |  |  |
