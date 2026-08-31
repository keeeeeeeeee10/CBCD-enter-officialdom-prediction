# BIOG_ADDR_DATA

Rows: **460,772**; columns: **29**.

Person identifier fields observed: `c_personid`.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_personid | INTEGER(11) | 0 | 0.0000% | 0 | 152246 | True | [3, 5, 6] |
| c_addr_id | INTEGER(11) | 0 | 0.0000% | 0 | 7075 | True | [100658, 100395, 100449] |
| c_addr_type | smallint(6) | 0 | 0.0000% | 0 | 21 | True | [1, 5, 9] |
| c_sequence | smallint(6) | 0 | 0.0000% | 0 | 33 | True | [0, 1, 9] |
| c_firstyear | smallint(6) | 410445 | 89.0777% | 0 | 629 | True | [0, 1083, 1071] |
| c_lastyear | smallint(6) | 416965 | 90.4927% | 0 | 199 | True | [0, 1086, 737] |
| c_source | INTEGER(11) | 920 | 0.1997% | 0 | 286 | True | [7596, 0, 24309] |
| c_pages | varchar(255) | 1584 | 0.3438% | 1459 | 65224 | True | ["3024", "0000", "8909"] |
| c_notes | TEXT | 251430 | 54.5671% | 7125 | 22847 | True | ["開封人(宋人傳記資料索引(電子版))。", "曹州濟陰人(宋人傳記資料索引(電子版))。", "鉅野人(宋人傳記資料索引(電子版))。"] |
| c_fy_nh_code | smallint(6) | 178952 | 38.8374% | 0 | 123 | True | [0, 529, 518] |
| c_ly_nh_code | smallint(6) | 179669 | 38.9930% | 0 | 45 | True | [0, 530, 375] |
| c_fy_nh_year | smallint(6) | 450863 | 97.8495% | 0 | 38 | True | [6, 0, 1] |
| c_ly_nh_year | smallint(6) | 452637 | 98.2345% | 0 | 26 | True | [0, 1, 25] |
| c_fy_range | smallint(6) | 452761 | 98.2614% | 0 | 5 | True | [0, 2, 1] |
| c_ly_range | smallint(6) | 453041 | 98.3222% | 0 | 5 | True | [0, 2, -1] |
| c_natal | INTEGER(11) | 389528 | 84.5381% | 0 | 2 | True | [0, 1] |
| c_fy_intercalary | smallint(6) | 148276 | 32.1799% | 0 | 2 | True | [0, 1] |
| c_ly_intercalary | smallint(6) | 148276 | 32.1799% | 0 | 2 | True | [0, 1] |
| c_fy_month | smallint(6) | 449687 | 97.5943% | 0 | 13 | True | [8, 0, 12] |
| c_ly_month | smallint(6) | 452425 | 98.1885% | 0 | 13 | True | [0, 4, 10] |
| c_fy_day | smallint(6) | 450037 | 97.6702% | 0 | 33 | True | [0, 11, 9] |
| c_ly_day | smallint(6) | 452542 | 98.2139% | 0 | 33 | True | [0, 21, 11] |
| c_fy_day_gz | smallint(6) | 453960 | 98.5216% | 0 | 26 | True | [21, 0, 49] |
| c_ly_day_gz | smallint(6) | 454090 | 98.5498% | 0 | 9 | True | [0, 15, 11] |
| c_created_by | varchar(255) | 0 | 0.0000% | 0 | 149 | True | ["TTS", "BDZWZ", "load"] |
| c_modified_by | varchar(255) | 444282 | 96.4212% | 11606 | 120 | True | ["BDZWZ", "BDGLW", "Qi Xinghai"] |
| c_delete | smallint(6) | 454116 | 98.5555% | 0 | 1 | True | [0] |
| c_created_date | TEXT | 0 | 0.0000% | 0 | 3833 | True | ["2007-03-12 00:00:00", "2008-06-18 00:00:00", "2010-10-29 00:00:00"] |
| c_modified_date | TEXT | 455888 | 98.9400% | 0 | 777 | True | ["2008-05-31 00:00:00", "2008-05-24 00:00:00", "2026-06-06 14:38:53"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

| source key | target | basis | matched/non-NULL | match rate |
| --- | --- | --- | --- | --- |
| c_personid | BIOG_MAIN.c_personid | inferred join key | 460772/460772 | 100.0000% |
| c_addr_id | ADDR_CODES.c_addr_id | inferred join key | 460772/460772 | 100.0000% |
| c_natal | ADDR_CODES.c_addr_id | inferred join key | 71244/71244 | 100.0000% |

## First five rows

| c_personid | c_addr_id | c_addr_type | c_sequence | c_firstyear | c_lastyear | c_source | c_pages | c_notes | c_fy_nh_code | c_ly_nh_code | c_fy_nh_year | c_ly_nh_year | c_fy_range | c_ly_range | c_natal | c_fy_intercalary | c_ly_intercalary | c_fy_month | c_ly_month | c_fy_day | c_ly_day | c_fy_day_gz | c_ly_day_gz | c_created_by | c_modified_by | c_delete | c_created_date | c_modified_date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 101117 | 1 | 0 |  |  | 2229 | 卷四百七十 |  |  |  |  |  |  |  | 0 | 0 | 0 |  |  |  |  |  |  | Hongsu Wang |  |  | 2026-04-08 22:19:39 |  |
| 2 | 100430 | 1 | 0 | 0 | 0 | 0 | 0000 |  | 0 | 0 |  |  |  |  | 0 | 0 | 0 |  |  |  |  |  |  | TTS |  |  | 2007-03-12 00:00:00 |  |
| 3 | 100658 | 1 | 0 | 0 | 0 | 7596 | 3024 | 開封人(宋人傳記資料索引(電子版))。 | 0 | 0 |  |  |  |  | 0 | 0 | 0 |  |  |  |  |  |  | TTS |  |  | 2007-03-12 00:00:00 |  |
| 4 | 12509 | 1 | 0 | 0 | 0 | 0 | 0000 |  | 0 | 0 |  |  |  |  | 0 | 0 | 0 |  |  |  |  |  |  | TTS |  |  | 2007-03-12 00:00:00 |  |
| 4 | 12853 | 1 | 1 |  |  | 7596 | 8501 | 歙州休寧人(宋人傳記資料索引(電子版))。 | 0 | 0 |  |  |  |  |  | 0 | 0 |  |  |  |  |  |  | BDLYH |  |  | 2008-01-21 00:00:00 |  |
