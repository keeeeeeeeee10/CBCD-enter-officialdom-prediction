# ADDR_CODES

Rows: **30,100**; columns: **12**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_addr_id | INTEGER(11) | 0 | 0.0000% | 0 | 30100 | False | [-1, 0, 1] |
| c_name | varchar(255) | 0 | 0.0000% | 0 | 15042 | False | ["[Missing Data]", "[Unknown]", "People's Republic of China"] |
| c_name_chn | varchar(255) | 0 | 0.0000% | 0 | 14472 | False | ["[信息缺乏]", "[未詳]", "中華人民共和國"] |
| c_firstyear | smallint(6) | 110 | 0.3654% | 0 | 840 | False | [1949, 1115, 1138] |
| c_lastyear | smallint(6) | 110 | 0.3654% | 0 | 700 | False | [2005, 1234, 1140] |
| c_admin_type | varchar(255) | 0 | 0.0000% | 0 | 239 | False | ["[Unknown]", "State", "Shengshi"] |
| c_admin_cat_code | smallint(6) | 0 | 0.0000% | 0 | 211 | False | [0, 150, 138] |
| x_coord | REAL | 14297 | 47.4983% | 0 | 7238 | False | [123.188324, 120.7971, 115.31562] |
| y_coord | REAL | 14297 | 47.4983% | 0 | 7266 | False | [41.270794, 41.768, 38.947723] |
| CHGIS_PT_ID | INTEGER(11) | 19104 | 63.4684% | 0 | 5884 | False | [44747, 120482, 115584] |
| c_notes | TEXT | 5410 | 17.9734% | 19462 | 539 | False | ["XY coordinates are approximations based on centroids of approximate polygons", "中國-遼寧省-朝陽市-朝陽縣", "蒙古-肯特省(Khentii)-(Moron)"] |
| c_alt_names | varchar(255) | 8647 | 28.7276% | 19937 | 982 | False | ["本谿市", "鷄西市", "商丘地區"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_addr_id | c_name | c_name_chn | c_firstyear | c_lastyear | c_admin_type | c_admin_cat_code | x_coord | y_coord | CHGIS_PT_ID | c_notes | c_alt_names |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| -1 | [Missing Data] | [信息缺乏] |  |  | [Unknown] | 0 |  |  |  |  |  |
| 0 | [Unknown] | [未詳] |  |  | [Unknown] | 0 |  |  |  |  |  |
| 1 | People's Republic of China | 中華人民共和國 | 1949 | 2005 | State | 150 |  |  |  |  |  |
| 2 | Beijing Shengshi | 北京省市 | 1949 | 2005 | Shengshi | 138 |  |  |  |  |  |
| 3 | Tianjin Shengshi | 天津省市 | 1949 | 2005 | Shengshi | 138 |  |  |  |  |  |
