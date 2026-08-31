# OFFICE_CODES

Rows: **34,119**; columns: **11**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_office_id | INTEGER(11) | 0 | 0.0000% | 0 | 34119 | False | [0, 3, 7] |
| c_dy | smallint(6) | 0 | 0.0000% | 0 | 11 | False | [15, 6, 18] |
| c_office_pinyin | varchar(255) | 0 | 0.0000% | 0 | 28694 | False | ["unknown", "ti ju", "cui kan yuan"] |
| c_office_chn | varchar(255) | 0 | 0.0000% | 0 | 29406 | False | ["未詳", "提舉", "三司推勘院"] |
| c_office_pinyin_alt | varchar(255) | 27695 | 81.1718% | 1631 | 4241 | False | ["san si gou yuan;dou gou yuan", "li qian", "san si mo kan si;mo kan si;mo kan;du mo kan"] |
| c_office_chn_alt | varchar(255) | 27593 | 80.8728% | 1630 | 4354 | False | ["三司勾院;都勾院", "理欠", "三司磨勘司;磨勘司;磨勘;都磨勘"] |
| c_office_trans | varchar(255) | 11551 | 33.8550% | 1659 | 5081 | False | ["Supervisor (Hucker)", "Investigations Office of the State Finance Commission", "Comptroller"] |
| c_office_trans_alt | varchar(255) | 30849 | 90.4159% | 1660 | 17 | False | ["Vice Grand Councilor", "Administrator", "Junior Master"] |
| c_source | INTEGER(11) | 28270 | 82.8571% | 0 | 34 | False | [8947, 4802, 18417] |
| c_pages | varchar(255) | 30145 | 88.3525% | 1660 | 6 | False | ["卷四十五", "卷四十六", "卷四十七"] |
| c_notes | TEXT | 30393 | 89.0794% | 1 | 1654 | False | ["参見san si tui guan （三司推官）", "參見 huang he san men fa yun shi （黃河三門發運使）", "參見 zhou yi bo shi（周易博士）, chun qiu bo shi（春秋博士）, guang wen bo shi（廣文博士）, guo zi bo shi… |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_office_id | c_dy | c_office_pinyin | c_office_chn | c_office_pinyin_alt | c_office_chn_alt | c_office_trans | c_office_trans_alt | c_source | c_pages | c_notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 15 | unknown | 未詳 |  |  |  |  |  |  |  |
| 3 | 15 | ti ju | 提舉 |  |  | Supervisor (Hucker) |  |  |  |  |
| 7 | 15 | cui kan yuan | 三司推勘院 |  |  | Investigations Office of the State Finance Commission |  |  |  |  |
| 8 | 15 | cui qian si | 催欠司 |  |  | Comptroller |  |  |  |  |
| 9 | 15 | san si du gou yuan | 三司都勾院 | san si gou yuan;dou gou yuan | 三司勾院;都勾院 | General Comptroller‘s Office of the State Finance Commission (Hucker) |  |  |  |  |
