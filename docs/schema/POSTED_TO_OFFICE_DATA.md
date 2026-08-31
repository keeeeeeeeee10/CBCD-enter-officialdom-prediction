# POSTED_TO_OFFICE_DATA

Rows: **590,866**; columns: **34**.

Person identifier fields observed: `c_personid`.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_personid | INTEGER(11) | 0 | 0.0000% | 0 | 141909 | True | [105278, 106175, 109230] |
| c_office_id | INTEGER(11) | 0 | 0.0000% | 0 | 8879 | True | [0, 3, 8] |
| c_posting_id | INTEGER(11) | 0 | 0.0000% | 0 | 196952 | True | [6, 9, 12] |
| c_sequence | smallint(6) | 229966 | 38.9202% | 0 | 118 | True | [2, 3, 1] |
| c_firstyear | smallint(6) | 162660 | 27.5291% | 0 | 1313 | True | [0, 1302, 977] |
| c_fy_nh_code | smallint(6) | 307843 | 52.1003% | 0 | 231 | True | [0, 625, 508] |
| c_fy_nh_year | smallint(6) | 366700 | 62.0614% | 0 | 65 | True | [0, 2, 7] |
| c_fy_range | smallint(6) | 401290 | 67.9156% | 0 | 6 | True | [0, 2, -1] |
| c_lastyear | smallint(6) | 313987 | 53.1401% | 0 | 1042 | True | [0, 1159, 1079] |
| c_ly_nh_code | smallint(6) | 362665 | 61.3786% | 0 | 174 | True | [0, 541, 543] |
| c_ly_nh_year | smallint(6) | 413370 | 69.9600% | 0 | 53 | True | [0, 29, 1] |
| c_ly_range | smallint(6) | 412283 | 69.7761% | 0 | 6 | True | [0, 2, 1] |
| c_appt_code | smallint(6) | 0 | 0.0000% | 0 | 101 | True | [1, 22, 3] |
| c_assume_office_code | smallint(6) | 536793 | 90.8485% | 0 | 6 | True | [0, 1, 5] |
| c_inst_code | smallint(6) | 197212 | 33.3768% | 0 | 3 | True | [0, 3898, 3902] |
| c_inst_name_code | smallint(6) | 197212 | 33.3768% | 0 | 3 | True | [0, 2517, 2520] |
| c_source | INTEGER(11) | 48 | 0.0081% | 0 | 527 | True | [9599, 7596, 0] |
| c_pages | varchar(255) | 41160 | 6.9660% | 764 | 92911 | True | ["5507", "6467", "9791"] |
| c_notes | TEXT | 309202 | 52.3303% | 1876 | 41459 | True | ["徵之為齋長", "徵授武職", "大德間徵拜博士，不就"] |
| c_office_id_backup | INTEGER(11) | 575435 | 97.3884% | 0 | 467 | True | [0, 3, 8] |
| c_office_category_id | smallint(6) | 373266 | 63.1727% | 0 | 15 | True | [0, 6, 10] |
| c_fy_intercalary | smallint(6) | 342594 | 57.9817% | 0 | 2 | True | [0, 1] |
| c_fy_month | smallint(6) | 584718 | 98.9595% | 0 | 15 | True | [0, 10, 8] |
| c_ly_intercalary | smallint(6) | 342594 | 57.9817% | 0 | 2 | True | [0, 1] |
| c_ly_month | smallint(6) | 585693 | 99.1245% | 0 | 13 | True | [0, 12, 11] |
| c_fy_day | smallint(6) | 585929 | 99.1644% | 0 | 30 | True | [0, 27, 16] |
| c_ly_day | smallint(6) | 586058 | 99.1863% | 0 | 22 | True | [0, 2, 29] |
| c_fy_day_gz | smallint(6) | 585931 | 99.1648% | 0 | 39 | True | [0, 18, 8] |
| c_ly_day_gz | smallint(6) | 586079 | 99.1898% | 0 | 23 | True | [0, 32, 1] |
| c_dy | smallint(6) | 1680 | 0.2843% | 0 | 26 | True | [0, 6, 15] |
| c_created_by | varchar(255) | 0 | 0.0000% | 0 | 149 | True | ["load", "TTS", "BDZHOUJIA"] |
| c_modified_by | varchar(255) | 522170 | 88.3737% | 54521 | 126 | True | ["BDGLW", "BDGSX", "BDLIUJIANG"] |
| c_created_date | TEXT | 0 | 0.0000% | 0 | 3483 | True | ["2013-09-23 00:00:00", "2007-03-12 00:00:00", "2007-03-24 00:00:00"] |
| c_modified_date | TEXT | 576692 | 97.6011% | 0 | 1443 | True | ["2008-03-01 00:00:00", "2008-06-14 00:00:00", "2007-05-19 00:00:00"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

| source key | target | basis | matched/non-NULL | match rate |
| --- | --- | --- | --- | --- |
| c_personid | BIOG_MAIN.c_personid | inferred join key | 590866/590866 | 100.0000% |
| c_office_id | OFFICE_CODES.c_office_id | inferred join key | 590866/590866 | 100.0000% |
| c_posting_id | POSTING_DATA.c_posting_id | inferred join key | 590866/590866 | 100.0000% |
| c_office_id_backup | OFFICE_CODES.c_office_id | inferred join key | 12112/15431 | 78.4913% |
| c_dy | DYNASTIES.c_dy | inferred join key | 589186/589186 | 100.0000% |

## First five rows

| c_personid | c_office_id | c_posting_id | c_sequence | c_firstyear | c_fy_nh_code | c_fy_nh_year | c_fy_range | c_lastyear | c_ly_nh_code | c_ly_nh_year | c_ly_range | c_appt_code | c_assume_office_code | c_inst_code | c_inst_name_code | c_source | c_pages | c_notes | c_office_id_backup | c_office_category_id | c_fy_intercalary | c_fy_month | c_ly_intercalary | c_ly_month | c_fy_day | c_ly_day | c_fy_day_gz | c_ly_day_gz | c_dy | c_created_by | c_modified_by | c_created_date | c_modified_date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 104772 | 0 | 4 | 7 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 9599 | 4949 | 徵為樞密院同知 |  | 0 | 0 |  | 0 |  |  |  |  |  | 0 | load |  | 2013-09-23 00:00:00 |  |
| 104979 | 0 | 5 | 1 | 1368 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 9599 | 5183 | 明初徵拜燕王傅 |  | 0 | 0 |  | 0 |  |  |  |  |  | 0 | load |  | 2013-09-23 00:00:00 |  |
| 105278 | 0 | 6 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 9599 | 5507 | 徵之為齋長 |  | 0 | 0 |  | 0 |  |  |  |  |  | 0 | load |  | 2013-09-23 00:00:00 |  |
| 106107 | 0 | 7 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 9599 | 6396 | 徵為國子助教、陝西提學 |  | 0 | 0 |  | 0 |  |  |  |  |  | 0 | load |  | 2013-09-23 00:00:00 |  |
| 106107 | 0 | 8 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 9599 | 6396 | 徵為國子助教、陝西提學 |  | 0 | 0 |  | 0 |  |  |  |  |  | 0 | load |  | 2013-09-23 00:00:00 |  |
