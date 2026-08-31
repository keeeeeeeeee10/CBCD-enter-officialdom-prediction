# BIOG_TEXT_DATA

Rows: **53,289**; columns: **14**.

Person identifier fields observed: `c_personid`.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_textid | INTEGER(11) | 0 | 0.0000% | 0 | 50712 | False | [2031, 2032, 2033] |
| c_personid | INTEGER(11) | 0 | 0.0000% | 0 | 18082 | False | [0, 4, 6] |
| c_role_id | smallint(6) | 0 | 0.0000% | 0 | 12 | False | [0, 1, 3] |
| c_year | smallint(6) | 25303 | 47.4826% | 0 | 2 | False | [-1, 0] |
| c_nh_code | smallint(6) | 25303 | 47.4826% | 0 | 1 | False | [0] |
| c_nh_year | smallint(6) | 25303 | 47.4826% | 0 | 2 | False | [-1, 0] |
| c_range_code | smallint(6) | 25303 | 47.4826% | 0 | 1 | False | [0] |
| c_source | INTEGER(11) | 28214 | 52.9453% | 0 | 119 | False | [63342, 70614, 40328] |
| c_pages | varchar(255) | 2182 | 4.0947% | 65 | 2938 | False | ["0000000", "53", "86"] |
| c_notes | TEXT | 50586 | 94.9277% | 2446 | 193 | False | ["國史實錄院", "詳定所", "禮部太常寺"] |
| c_created_by | varchar(255) | 0 | 0.0000% | 0 | 97 | False | ["TTS", "HUCW", "load"] |
| c_modified_by | varchar(255) | 49750 | 93.3589% | 2450 | 66 | False | ["HUWHS", "Wenjie Hu", "BDLYH"] |
| c_created_date | TEXT | 0 | 0.0000% | 0 | 2262 | False | ["2007-03-12 00:00:00", "2014-03-27 00:00:00", "2014-04-17 00:00:00"] |
| c_modified_date | TEXT | 52200 | 97.9564% | 0 | 476 | False | ["2014-01-06 00:00:00", "2019-06-13 00:00:00", "2007-12-21 00:00:00"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

| source key | target | basis | matched/non-NULL | match rate |
| --- | --- | --- | --- | --- |
| c_textid | TEXT_CODES.c_textid | inferred join key | 53289/53289 | 100.0000% |
| c_personid | BIOG_MAIN.c_personid | inferred join key | 53289/53289 | 100.0000% |
| c_role_id | TEXT_ROLE_CODES.c_role_id | inferred join key | 53289/53289 | 100.0000% |

## First five rows

| c_textid | c_personid | c_role_id | c_year | c_nh_code | c_nh_year | c_range_code | c_source | c_pages | c_notes | c_created_by | c_modified_by | c_created_date | c_modified_date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2031 | 0 | 0 | -1 | 0 | -1 | 0 |  | 0000000 |  | TTS | HUWHS | 2007-03-12 00:00:00 | 2014-01-06 00:00:00 |
| 2032 | 0 | 0 | -1 | 0 | -1 | 0 |  | 0000000 |  | TTS |  | 2007-03-12 00:00:00 |  |
| 2033 | 0 | 0 | -1 | 0 | -1 | 0 |  | 0000000 |  | TTS |  | 2007-03-12 00:00:00 |  |
| 2035 | 0 | 0 | -1 | 0 | -1 | 0 |  | 0000000 |  | TTS |  | 2007-03-12 00:00:00 |  |
| 2064 | 0 | 0 | -1 | 0 | -1 | 0 |  | 0000000 |  | TTS |  | 2007-03-12 00:00:00 |  |
