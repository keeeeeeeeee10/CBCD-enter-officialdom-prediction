# APPOINTMENT_CODES

Rows: **116**; columns: **6**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_appt_code | smallint(6) | 0 | 0.0000% | 0 | 116 | False | [0, 1, 2] |
| c_appt_desc_chn | varchar(255) | 0 | 0.0000% | 0 | 114 | False | ["未詳", "正授", "權"] |
| c_appt_desc | varchar(255) | 62 | 53.4483% | 0 | 52 | False | ["Unknown", "Regular Appointment", "Provisional Appointment"] |
| c_appt_desc_chn_alt | varchar(255) | 110 | 94.8276% | 0 | 6 | False | ["署理", "兼理;兼署;兼署", "候選"] |
| c_appt_desc_alt | varchar(255) | 114 | 98.2759% | 0 | 2 | False | ["Acting", "nominal office"] |
| c_notes | TEXT | 114 | 98.2759% | 0 | 2 | False | ["龔延明《宋代官制辭典》（增訂本）“借補”條：帥府主將自行辟置的官屬、未及申稟朝廷者，帶“借補”二字，以與真命除授之官相區別。苗書梅《宋代官員選任和管理制度》認為，借補是宋朝在戰爭爆發的緊急時期，允許諸軍將帥或者諸路監司郡守等用白帖臨時為忠義有功之人補官的一種權宜制度。", "“帶行”跟“行”還是不一樣，“帶行”集… |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_appt_code | c_appt_desc_chn | c_appt_desc | c_appt_desc_chn_alt | c_appt_desc_alt | c_notes |
| --- | --- | --- | --- | --- | --- |
| 0 | 未詳 | Unknown |  |  |  |
| 1 | 正授 | Regular Appointment |  |  |  |
| 2 | 權 | Provisional Appointment |  |  |  |
| 3 | 行 | Lower Acting Appointment |  |  |  |
| 4 | 守 | Higher Acting Appointment |  |  |  |
