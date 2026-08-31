# BIOG_MAIN

Rows: **661,124**; columns: **55**.

Person identifier fields observed: `c_personid`.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_personid | INTEGER(11) | 0 | 0.0000% | 0 | 165281 | True | [3, 7, 11] |
| c_name | varchar(255) | 0 | 0.0000% | 0 | 116150 | True | ["An Tao", "Chai Tianyin", "Chao Gongwu"] |
| c_name_chn | varchar(255) | 0 | 0.0000% | 0 | 144434 | True | ["安燾", "柴天因", "晁公武"] |
| c_index_year | smallint(6) | 353125 | 53.4128% | 0 | 1612 | True | [1065, 1070, 1105] |
| c_index_year_type_code | varchar(255) | 1 | 0.0002% | 353124 | 101 | True | ["2912", "05", "01"] |
| c_index_year_source_id | INTEGER(11) | 514363 | 77.8013% | 0 | 23379 | True | [3001, 3047, 8058] |
| c_female | smallint(6) | 24237 | 3.6660% | 0 | 2 | True | [0, 1] |
| c_index_addr_id | INTEGER(11) | 268241 | 40.5735% | 0 | 6062 | True | [100658, 12889, 11478] |
| c_index_addr_type_code | smallint(6) | 268242 | 40.5736% | 0 | 7 | True | [1, 2, 6] |
| c_ethnicity_code | smallint(6) | 246122 | 37.2278% | 0 | 118 | True | [0, 1, 318] |
| c_household_status_code | smallint(6) | 243251 | 36.7936% | 0 | 27 | True | [0, 4, 1] |
| c_tribe | varchar(255) | 607312 | 91.8605% | 53812 | 1 | True | [] |
| c_birthyear | smallint(6) | 574560 | 86.9065% | 0 | 1389 | True | [0, 1105, 1081] |
| c_by_nh_code | smallint(6) | 247558 | 37.4450% | 0 | 188 | True | [520, 0, 534] |
| c_by_nh_year | smallint(6) | 617475 | 93.3978% | 0 | 62 | True | [1, 4, 3] |
| c_by_range | smallint(6) | 657458 | 99.4455% | 0 | 5 | True | [0, 2, 1] |
| c_deathyear | smallint(6) | 563007 | 85.1591% | 0 | 1521 | True | [0, 1180, 1133] |
| c_dy_nh_code | smallint(6) | 246826 | 37.3343% | 0 | 187 | True | [0, 544, 541] |
| c_dy_nh_year | smallint(6) | 628499 | 95.0652% | 0 | 65 | True | [7, 3, 2] |
| c_dy_range | smallint(6) | 636830 | 96.3253% | 0 | 5 | True | [-1, 0, 2] |
| c_death_age | smallint(6) | 597682 | 90.4039% | 0 | 111 | True | [75, 0, 76] |
| c_death_age_range | smallint(6) | 630098 | 95.3071% | 0 | 5 | True | [-1, 0, 2] |
| c_fl_earliest_year | smallint(6) | 639366 | 96.7089% | 0 | 711 | True | [1029, 1131, 976] |
| c_fl_ey_nh_code | smallint(6) | 248503 | 37.5880% | 0 | 167 | True | [0, 518, 508] |
| c_fl_ey_nh_year | smallint(6) | 648034 | 98.0200% | 0 | 40 | True | [7, 1, 3] |
| c_fl_ey_notes | TEXT | 588098 | 88.9543% | 53403 | 3182 | True | ["天聖七年為比部員外郎。", "於明州任官", "興元府掾（拜命 太平興國初）"] |
| c_fl_latest_year | smallint(6) | 650170 | 98.3431% | 0 | 623 | True | [1040, 1132, 972] |
| c_fl_ly_nh_code | smallint(6) | 248546 | 37.5945% | 0 | 156 | True | [0, 522, 507] |
| c_fl_ly_nh_year | smallint(6) | 655212 | 99.1058% | 0 | 37 | True | [1, 5, 31] |
| c_fl_ly_notes | TEXT | 598439 | 90.5184% | 53407 | 1097 | True | ["景祐三年以主客郎中知潭州，加金部郎中，在任五年。", "於明州任官", "知禮部貢舉（拜命 開寳5）"] |
| c_surname | varchar(255) | 11208 | 1.6953% | 1308 | 871 | True | ["An", "Chai", "Chao"] |
| c_surname_chn | varchar(255) | 11236 | 1.6995% | 1285 | 1766 | True | ["安", "柴", "晁"] |
| c_mingzi | varchar(255) | 1543 | 0.2334% | 0 | 39335 | True | ["Tao", "Tianyin", "Gongwu"] |
| c_mingzi_chn | varchar(255) | 1916 | 0.2898% | 0 | 72370 | True | ["燾", "天因", "公武"] |
| c_dy | smallint(6) | 1584 | 0.2396% | 0 | 70 | True | [15, 6, 11] |
| c_choronym_code | smallint(6) | 242707 | 36.7113% | 0 | 152 | True | [0, 45, 55] |
| c_notes | TEXT | 375594 | 56.8114% | 53339 | 50655 | True | ["An(1) Tao [3] Yuanyou coalition. Rihua's son [3001]. Tao's son, Fu [3000], was killed by Jurchen when they sacked the capital in 1126. XCB, 275.2a, 281.9b, 2… |
| c_by_intercalary | smallint(6) | 211902 | 32.0518% | 0 | 2 | True | [0, 1] |
| c_dy_intercalary | smallint(6) | 211900 | 32.0515% | 0 | 2 | True | [0, 1] |
| c_by_month | smallint(6) | 648833 | 98.1409% | 0 | 13 | True | [9, 2, 8] |
| c_dy_month | smallint(6) | 659201 | 99.7091% | 0 | 13 | True | [6, 2, 9] |
| c_by_day | smallint(6) | 649019 | 98.1690% | 0 | 32 | True | [15, 17, 11] |
| c_dy_day | smallint(6) | 659733 | 99.7896% | 0 | 32 | True | [26, 9, 8] |
| c_by_day_gz | smallint(6) | 660817 | 99.9536% | 0 | 16 | True | [53, 41, 55] |
| c_dy_day_gz | smallint(6) | 660665 | 99.9306% | 0 | 34 | True | [53, 18, 6] |
| c_surname_proper | varchar(255) | 602657 | 91.1564% | 53715 | 366 | True | ["Ricci", "Zhu", "Gordon"] |
| c_mingzi_proper | varchar(255) | 602668 | 91.1581% | 53716 | 899 | True | ["Matteo", "Chang", "Charles George"] |
| c_name_proper | varchar(255) | 566208 | 85.6432% | 90116 | 1169 | True | ["Ricci, Matteo", "Zhu Chang", "Charles George Gordon"] |
| c_surname_rm | varchar(255) | 607364 | 91.8684% | 53716 | 8 | True | ["Gioroi", "Uksun", "Aisin Gioro"] |
| c_mingzi_rm | varchar(255) | 602689 | 91.1613% | 53716 | 934 | True | ["Bazaoma Yelishu", "El Temur", "Majartai"] |
| c_name_rm | varchar(255) | 565270 | 85.5014% | 91201 | 916 | True | ["Bazaoma Yelishu", "El Temur", "Majartai"] |
| c_created_by | varchar(255) | 5006 | 0.7572% | 2 | 169 | True | ["TTS", "BDLIUJIANG", "Ho Ho Hin"] |
| c_modified_by | varchar(255) | 544006 | 82.2850% | 53675 | 168 | True | ["BDNWH", "Wenjie Hu", "BDGLW"] |
| c_created_date | TEXT | 5008 | 0.7575% | 0 | 3537 | True | ["2007-03-12 00:00:00", "2007-05-25 00:00:00", "2022-12-20 00:00:00"] |
| c_modified_date | TEXT | 597679 | 90.4035% | 0 | 4161 | True | ["2008-10-18 00:00:00", "2019-05-25 00:00:00", "2008-11-15 00:00:00"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

| source key | target | basis | matched/non-NULL | match rate |
| --- | --- | --- | --- | --- |
| c_index_addr_id | ADDR_CODES.c_addr_id | inferred join key | 392883/392883 | 100.0000% |
| c_dy | DYNASTIES.c_dy | inferred join key | 659540/659540 | 100.0000% |

## First five rows

| c_personid | c_name | c_name_chn | c_index_year | c_index_year_type_code | c_index_year_source_id | c_female | c_index_addr_id | c_index_addr_type_code | c_ethnicity_code | c_household_status_code | c_tribe | c_birthyear | c_by_nh_code | c_by_nh_year | c_by_range | c_deathyear | c_dy_nh_code | c_dy_nh_year | c_dy_range | c_death_age | c_death_age_range | c_fl_earliest_year | c_fl_ey_nh_code | c_fl_ey_nh_year | c_fl_ey_notes | c_fl_latest_year | c_fl_ly_nh_code | c_fl_ly_nh_year | c_fl_ly_notes | c_surname | c_surname_chn | c_mingzi | c_mingzi_chn | c_dy | c_choronym_code | c_notes | c_by_intercalary | c_dy_intercalary | c_by_month | c_dy_month | c_by_day | c_dy_day | c_by_day_gz | c_dy_day_gz | c_surname_proper | c_mingzi_proper | c_name_proper | c_surname_rm | c_mingzi_rm | c_name_rm | c_created_by | c_modified_by | c_created_date | c_modified_date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Weixiang | 未詳 |  |  |  |  |  |  |  |  |  |  | 0 | 0 | 0 |  | 0 | 0 | 0 |  | 0 | 0 | 0 | 0 |  | 0 | 0 | 0 |  |  |  | Weixiang | 未詳 |  |  |  | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | TTS | Hongsu Wang | 2007-03-12 00:00:00 | 2026-03-26 10:34:41 |
| 1 | An Dun | 安惇 | 1042 | 01 |  | 0 | 101117 | 1 | 0 | 0 |  | 1042 | 523 | 2 |  | 1104 | 534 | 3 |  | 63 | -1 |  | 0 |  |  |  | 0 |  |  | An | 安 | Dun | 惇 | 15 | 0 | An(1) Dun [1] Fang's [2] father. XCB, 362.14b, SS; 471.21a, 22a. DDSL, 97.6b. CBD, 1, 548-9. | 0 | 0 |  |  |  |  |  |  |  |  |   |  |  |   | TTS | 相璇 | 2007-03-12 00:00:00 | 2020-10-10 00:00:00 |
| 2 | An Fang | 安邡 | 1072 | 11 | 1 | 0 | 100430 | 1 | 0 | 0 |  | 0 | 0 |  |  | 0 | 0 |  |  | 0 |  |  | 0 |  |  |  | 0 |  |  | An | 安 | Fang | 邡 | 15 | 0 | An(1) Fang [2] Dun's [1] son. XNYL, 94.9a, 104.12a.[待考。《宋史·安惇傳》云，惇二子郊、邦。] | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | TTS |  | 2007-03-12 00:00:00 |  |
| 3 | An Tao | 安燾 | 1065 | 2912 | 3001 | 0 | 100658 | 1 | 0 | 0 |  |  | 520 | 1 |  |  | 0 |  |  | 75 |  |  | 0 |  |  |  | 0 |  |  | An | 安 | Tao | 燾 | 15 | 0 | An(1) Tao [3] Yuanyou coalition. Rihua's son [3001]. Tao's son, Fu [3000], was killed by Jurchen when they sacked the capital in 1126. XCB, 275.2a, 281.9b, 282… | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | TTS | BDNWH | 2007-03-12 00:00:00 | 2008-10-18 00:00:00 |
| 4 | Zha Dao | 查道 | 955 | 01 |  | 0 | 12853 | 1 | 0 | 0 |  | 955 | 478 | 13 | 0 | 1018 | 516 | 2 |  | 64 |  |  | 0 |  |  |  | 0 |  |  | Zha | 查 | Dao | 道 | 15 | 0 | Zha Dao  His father, Yuanfang [3002], served in the administration of the Southern Tang ruler, Li Yu [3551], and was one of his ambassadors to Song in 969. XCB… | 0 | 0 |  |  |  |  |  |  |  |  |  |  |  |  | TTS | BDLYH | 2007-03-12 00:00:00 | 2008-01-21 00:00:00 |
