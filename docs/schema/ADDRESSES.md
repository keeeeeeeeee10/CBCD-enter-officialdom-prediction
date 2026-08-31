# ADDRESSES

Rows: **64,279**; columns: **25**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_addr_id | INTEGER | 0 | 0.0000% | 0 | 29990 | False | [1, 2, 3] |
| c_name | TEXT | 0 | 0.0000% | 0 | 14972 | False | ["People's Republic of China", "Beijing Shengshi", "Tianjin Shengshi"] |
| c_name_chn | TEXT | 0 | 0.0000% | 0 | 14406 | False | ["中華人民共和國", "北京省市", "天津省市"] |
| c_admin_type | TEXT | 0 | 0.0000% | 0 | 239 | False | ["State", "Shengshi", "Sheng"] |
| c_firstyear | INTEGER | 0 | 0.0000% | 0 | 840 | False | [1949, 1115, 1138] |
| c_lastyear | INTEGER | 0 | 0.0000% | 0 | 700 | False | [2005, 1234, 1140] |
| c_belongs_firstyear | INTEGER | 0 | 0.0000% | 0 | 891 | False | [1949, 1115, 1138] |
| c_belongs_lastyear | INTEGER | 0 | 0.0000% | 0 | 786 | False | [2005, 1234, 1137] |
| x_coord | REAL | 24816 | 38.6067% | 0 | 7226 | False | [123.188324, 120.7971, 115.31562] |
| y_coord | REAL | 24816 | 38.6067% | 0 | 7254 | False | [41.270794, 41.768, 38.947723] |
| belongs1_ID | INTEGER | 389 | 0.6052% | 0 | 4853 | False | [1, 2, 3] |
| belongs1_Name | TEXT | 389 | 0.6052% | 0 | 2408 | False | ["People's Republic of China", "Beijing Shengshi", "Tianjin Shengshi"] |
| belongs1_Name_chn | TEXT | 389 | 0.6052% | 0 | 2708 | False | ["中華人民共和國", "北京省市", "天津省市"] |
| belongs2_ID | INTEGER | 12976 | 20.1870% | 0 | 565 | False | [1, 28, 5] |
| belongs2_Name | TEXT | 12976 | 20.1870% | 0 | 497 | False | ["People's Republic of China", "Gansu Sheng", "Shanxi Sheng"] |
| belongs2_Name_chn | TEXT | 12976 | 20.1870% | 0 | 484 | False | ["中華人民共和國", "甘肅省", "山西省"] |
| belongs3_ID | INTEGER | 34329 | 53.4062% | 0 | 163 | False | [1, 2814, 2842] |
| belongs3_Name | TEXT | 34329 | 53.4062% | 0 | 158 | False | ["People's Republic of China", "Jin Dynasty", "Xianping Lu"] |
| belongs3_Name_chn | TEXT | 34329 | 53.4062% | 0 | 159 | False | ["中華人民共和國", "金朝", "咸平路"] |
| belongs4_ID | INTEGER | 51421 | 79.9966% | 0 | 57 | False | [2814, 2842, 2943] |
| belongs4_Name | TEXT | 51421 | 79.9966% | 0 | 56 | False | ["Jin Dynasty", "Xianping Lu", "Xijing Lu"] |
| belongs4_Name_chn | TEXT | 51421 | 79.9966% | 0 | 57 | False | ["金朝", "咸平路", "西京路"] |
| belongs5_ID | INTEGER | 61699 | 95.9862% | 0 | 16 | False | [2814, 4329, 16776] |
| belongs5_Name | TEXT | 61699 | 95.9862% | 0 | 16 | False | ["Jin Dynasty", "Ming Dynasty", "Yuan Dynasty"] |
| belongs5_Name_chn | TEXT | 61699 | 95.9862% | 0 | 16 | False | ["金朝", "明朝", "元朝"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

| source key | target | basis | matched/non-NULL | match rate |
| --- | --- | --- | --- | --- |
| c_addr_id | ADDR_CODES.c_addr_id | inferred join key | 64279/64279 | 100.0000% |

## First five rows

| c_addr_id | c_name | c_name_chn | c_admin_type | c_firstyear | c_lastyear | c_belongs_firstyear | c_belongs_lastyear | x_coord | y_coord | belongs1_ID | belongs1_Name | belongs1_Name_chn | belongs2_ID | belongs2_Name | belongs2_Name_chn | belongs3_ID | belongs3_Name | belongs3_Name_chn | belongs4_ID | belongs4_Name | belongs4_Name_chn | belongs5_ID | belongs5_Name | belongs5_Name_chn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | People's Republic of China | 中華人民共和國 | State | 1949 | 2005 | 1949 | 2005 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| 2 | Beijing Shengshi | 北京省市 | Shengshi | 1949 | 2005 | 1949 | 2005 |  |  | 1 | People's Republic of China | 中華人民共和國 |  |  |  |  |  |  |  |  |  |  |  |  |
| 3 | Tianjin Shengshi | 天津省市 | Shengshi | 1949 | 2005 | 1949 | 2005 |  |  | 1 | People's Republic of China | 中華人民共和國 |  |  |  |  |  |  |  |  |  |  |  |  |
| 4 | Hebei Sheng | 河北省 | Sheng | 1949 | 2005 | 1949 | 2005 |  |  | 1 | People's Republic of China | 中華人民共和國 |  |  |  |  |  |  |  |  |  |  |  |  |
| 5 | Shanxi Sheng | 山西省 | Sheng | 1949 | 2005 | 1949 | 2005 |  |  | 1 | People's Republic of China | 中華人民共和國 |  |  |  |  |  |  |  |  |  |  |  |  |
