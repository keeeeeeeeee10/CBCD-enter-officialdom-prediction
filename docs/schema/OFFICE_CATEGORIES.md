# OFFICE_CATEGORIES

Rows: **15**; columns: **4**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_office_category_id | smallint(6) | 0 | 0.0000% | 0 | 15 | False | [0, 1, 2] |
| c_category_desc | varchar(255) | 0 | 0.0000% | 0 | 15 | False | ["unknown", "Classification title", "Commission"] |
| c_category_desc_chn | varchar(255) | 0 | 0.0000% | 0 | 15 | False | ["未詳", "階官", "差遣"] |
| c_notes | varchar(255) | 2 | 13.3333% | 0 | 10 | False | ["from Kracke, \"Translation of Sung Civil Service Titles\"", "Used in the Song before 1080, from Kracke, \"Translation of Sung Civil Service Titles\"", "12 ho… |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_office_category_id | c_category_desc | c_category_desc_chn | c_notes |
| --- | --- | --- | --- |
| 0 | unknown | 未詳 |  |
| 1 | Classification title | 階官 | from Kracke, "Translation of Sung Civil Service Titles" |
| 2 | Commission | 差遣 | Used in the Song before 1080, from Kracke, "Translation of Sung Civil Service Titles" |
| 3 | Complimentary censorial title | 憲官 | from Kracke, "Translation of Sung Civil Service Titles" |
| 4 | Dignitary | 勳 | 12 honorific titles, from Kracke, "Translation of Sung Civil Service Titles" |
