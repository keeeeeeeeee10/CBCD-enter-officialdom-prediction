# ASSOC_DATA

Rows: **189,970**; columns: **42**.

Person identifier fields observed: `c_personid`, `c_kin_id`, `c_assoc_id`, `c_assoc_kin_id`, `c_tertiary_personid`.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_assoc_code | smallint(6) | 0 | 0.0000% | 0 | 484 | False | [0, 4, 5] |
| c_personid | INTEGER(11) | 0 | 0.0000% | 0 | 44761 | False | [696877, 3624, 10589] |
| c_kin_code | smallint(6) | 0 | 0.0000% | 0 | 51 | False | [0, 75, 134] |
| c_kin_id | INTEGER(11) | 0 | 0.0000% | 0 | 4678 | False | [591, 10585, 30628] |
| c_assoc_id | INTEGER(11) | 0 | 0.0000% | 0 | 44763 | False | [591, 10585, 30628] |
| c_assoc_kin_code | smallint(6) | 0 | 0.0000% | 0 | 35 | False | [0, 75, 134] |
| c_assoc_kin_id | INTEGER(11) | 0 | 0.0000% | 0 | 4653 | False | [591, 10585, 30628] |
| c_tertiary_personid | INTEGER(11) | 49474 | 26.0431% | 0 | 11 | False | [0, 10200, 562987] |
| c_tertiary_type_notes | TEXT | 189267 | 99.6299% | 699 | 3 | False | ["吾友龔君立道篤意於學，從先生游者六年，聞微言要指必書於策，積之爲五卷，以示余。", "lgid=73638，其父嘗以事當法坤元號泣向帥前請以已官贖父罪"] |
| c_assoc_count | smallint(6) | 0 | 0.0000% | 0 | 56 | False | [1, 2, 0] |
| c_sequence | smallint(6) | 60183 | 31.6803% | 0 | 23 | False | [0, 1, 2] |
| c_assoc_first_year | smallint(6) | 0 | 0.0000% | 0 | 953 | False | [-9999, 1196, -1] |
| c_assoc_last_year | smallint(6) | 189916 | 99.9716% | 0 | 18 | False | [1358, 1558, 1174] |
| c_source | INTEGER(11) | 154 | 0.0811% | 0 | 862 | False | [64847, 0, 39136] |
| c_pages | varchar(255) | 34763 | 18.2992% | 1334 | 25344 | False | ["北宋卷 156 蘇通墓誌", "lgid=152149", "lgid=356638"] |
| c_notes | TEXT | 140624 | 74.0243% | 0 | 19158 | False | ["孫奇逢祠堂碑記撰文者", "總里萬承恩之負其闔戸租也，代輸百金以釋之。", "劾執政沈一貫"] |
| c_assoc_fy_nh_code | smallint(6) | 66570 | 35.0424% | 0 | 142 | False | [0, 524, 535] |
| c_assoc_fy_nh_year | smallint(6) | 144885 | 76.2673% | 0 | 42 | False | [0, 2, 4] |
| c_assoc_fy_range | smallint(6) | 146043 | 76.8769% | 0 | 5 | False | [0, 2, 1] |
| c_assoc_ly_nh_code | smallint(6) | 189912 | 99.9695% | 0 | 16 | False | [0, 636, 650] |
| c_assoc_ly_nh_year | smallint(6) | 189914 | 99.9705% | 0 | 12 | False | [18, 37, 1] |
| c_assoc_ly_range | smallint(6) | 189926 | 99.9768% | 0 | 2 | False | [0, -1] |
| c_addr_id | INTEGER(11) | 33299 | 17.5286% | 0 | 169 | False | [0, 15926, 18339] |
| c_litgenre_code | smallint(6) | 185166 | 97.4712% | 0 | 1 | False | [0] |
| c_occasion_code | smallint(6) | 68430 | 36.0215% | 0 | 10 | False | [0, 2, 1] |
| c_topic_code | smallint(6) | 68405 | 36.0083% | 0 | 15 | False | [0, 3, 4] |
| c_inst_code | smallint(6) | 134 | 0.0705% | 0 | 4 | False | [0, 611, 3052] |
| c_inst_name_code | smallint(6) | 134 | 0.0705% | 0 | 4 | False | [0, 283, 1982] |
| c_text_title | varchar(255) | 0 | 0.0000% | 0 | 57028 | False | ["[n/a]", "封秀國公 升之深狡多智數 初附王安石 既為相 時為小異", "除太學官 建炎初官給事中 以秦檜用事致仕 檜卒 起吏部侍郎、參知政事"] |
| c_assoc_claimer_id | INTEGER(11) | 54167 | 28.5134% | 0 | 10 | False | [0, 28192, 35109] |
| c_assoc_fy_intercalary | smallint(6) | 50631 | 26.6521% | 0 | 2 | False | [0, 1] |
| c_assoc_fy_month | smallint(6) | 184686 | 97.2185% | 0 | 14 | False | [12, 0, 8] |
| c_assoc_fy_day | smallint(6) | 184893 | 97.3275% | 0 | 28 | False | [13, 0, 4] |
| c_assoc_fy_day_gz | smallint(6) | 185037 | 97.4033% | 0 | 35 | False | [0, 32, 37] |
| c_assoc_ly_intercalary | smallint(6) | 183899 | 96.8042% | 0 | 1 | False | [0] |
| c_assoc_ly_month | smallint(6) | 189964 | 99.9968% | 0 | 3 | False | [8, 9, 12] |
| c_assoc_ly_day | smallint(6) | 189968 | 99.9989% | 0 | 1 | False | [3] |
| c_assoc_ly_day_gz | smallint(6) | 189970 | 100.0000% | 0 | 0 | False | [] |
| c_created_by | varchar(255) | 1 | 0.0005% | 143 | 169 | False | ["赵天祎", "TTS", "劉慧楠"] |
| c_modified_by | varchar(255) | 152503 | 80.2774% | 32664 | 141 | False | ["徐骏", "LiuBangdong", "張軒銘"] |
| c_created_date | TEXT | 144 | 0.0758% | 0 | 3734 | False | ["2025-12-07 00:00:00", "2007-03-12 00:00:00", "2025-12-09 00:00:00"] |
| c_modified_date | TEXT | 185167 | 97.4717% | 0 | 1132 | False | ["2026-04-11 15:45:44", "2025-12-06 00:00:00", "2025-12-13 00:00:00"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

| source key | target | basis | matched/non-NULL | match rate |
| --- | --- | --- | --- | --- |
| c_assoc_code | ASSOC_CODES.c_assoc_code | inferred join key | 189970/189970 | 100.0000% |
| c_personid | BIOG_MAIN.c_personid | inferred join key | 189970/189970 | 100.0000% |
| c_kin_code | KINSHIP_CODES.c_kincode | inferred join key | 189970/189970 | 100.0000% |
| c_kin_id | BIOG_MAIN.c_personid | inferred join key | 189970/189970 | 100.0000% |
| c_assoc_id | BIOG_MAIN.c_personid | inferred join key | 189970/189970 | 100.0000% |
| c_assoc_kin_code | KINSHIP_CODES.c_kincode | inferred join key | 189970/189970 | 100.0000% |
| c_assoc_kin_id | BIOG_MAIN.c_personid | inferred join key | 189970/189970 | 100.0000% |
| c_tertiary_personid | BIOG_MAIN.c_personid | inferred join key | 140496/140496 | 100.0000% |
| c_addr_id | ADDR_CODES.c_addr_id | inferred join key | 156671/156671 | 100.0000% |
| c_assoc_claimer_id | BIOG_MAIN.c_personid | inferred join key | 135803/135803 | 100.0000% |

## First five rows

| c_assoc_code | c_personid | c_kin_code | c_kin_id | c_assoc_id | c_assoc_kin_code | c_assoc_kin_id | c_tertiary_personid | c_tertiary_type_notes | c_assoc_count | c_sequence | c_assoc_first_year | c_assoc_last_year | c_source | c_pages | c_notes | c_assoc_fy_nh_code | c_assoc_fy_nh_year | c_assoc_fy_range | c_assoc_ly_nh_code | c_assoc_ly_nh_year | c_assoc_ly_range | c_addr_id | c_litgenre_code | c_occasion_code | c_topic_code | c_inst_code | c_inst_name_code | c_text_title | c_assoc_claimer_id | c_assoc_fy_intercalary | c_assoc_fy_month | c_assoc_fy_day | c_assoc_fy_day_gz | c_assoc_ly_intercalary | c_assoc_ly_month | c_assoc_ly_day | c_assoc_ly_day_gz | c_created_by | c_modified_by | c_created_date | c_modified_date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 696877 | 0 | 591 | 591 | 0 | 591 | 0 |  | 1 |  | -9999 |  | 64847 | 北宋卷 156 蘇通墓誌 |  |  |  |  |  |  |  | 0 |  |  |  | 0 | 0 | [n/a] | 0 | 0 |  |  |  | 0 |  |  |  | 赵天祎 | 徐骏 | 2025-12-07 00:00:00 | 2026-04-11 15:45:44 |
| 0 | 3624 | 0 | 10585 | 10585 | 0 | 10585 | 0 |  | 1 | 0 | 1196 |  | 0 |  |  | 0 | 0 | 0 |  |  |  | 0 |  | 0 | 0 | 0 | 0 | [n/a] | 0 | 0 |  |  |  | 0 |  |  |  | TTS | LiuBangdong | 2007-03-12 00:00:00 | 2025-12-06 00:00:00 |
| 0 | 10589 | 0 | 10585 | 10585 | 0 | 10585 | 0 |  | 1 | 0 | 1196 |  | 0 |  |  | 0 | 0 | 0 |  |  |  | 0 |  | 0 | 0 | 0 | 0 | [n/a] | 0 | 0 |  |  |  | 0 |  |  |  | TTS | LiuBangdong | 2007-03-12 00:00:00 | 2025-12-06 00:00:00 |
| 0 | 30284 | 0 | 30628 | 30628 | 0 | 30628 | 0 |  | 1 |  | -9999 |  | 39136 | lgid=152149 |  |  |  |  |  |  |  | 0 |  |  |  | 0 | 0 | [n/a] | 0 | 0 |  |  |  | 0 |  |  |  | 劉慧楠 |  | 2025-12-09 00:00:00 |  |
| 0 | 30849 | 0 | 30628 | 30628 | 0 | 30628 | 0 |  | 1 |  | -9999 |  | 39136 | lgid=152149 |  |  |  |  |  |  |  | 0 |  |  |  | 0 | 0 | [n/a] | 0 | 0 |  |  |  | 0 |  |  |  | 劉慧楠 |  | 2025-12-09 00:00:00 |  |
