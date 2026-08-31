# KIN_DATA

Rows: **561,461**; columns: **11**.

Person identifier fields observed: `c_personid`, `c_kin_id`.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_personid | INTEGER(11) | 0 | 0.0000% | 0 | 126866 | True | [699773, 699900, 701278] |
| c_kin_id | INTEGER(11) | 0 | 0.0000% | 0 | 128295 | True | [425868, 699898, 701277] |
| c_kin_code | smallint(6) | 0 | 0.0000% | 0 | 392 | True | [-10000, 0, 2] |
| c_source | INTEGER(11) | 14 | 0.0025% | 0 | 395 | True | [38541, 0, 32038] |
| c_pages | varchar(255) | 139622 | 24.8676% | 7205 | 18784 | True | ["lgid=630781", "lgid=630791", "lgid=630833"] |
| c_notes | TEXT | 434547 | 77.3958% | 16059 | 21746 | True | ["張守作「樞密院檢詳文字魯公(詹)墓誌銘」謂：「余兄之子許妻公之子。」", "張耒中表", "YP NewEpitaphID=3040"] |
| c_autogen_notes | TEXT | 528088 | 94.0560% | 18707 | 4905 | True | ["Auto-generated from PersonID = 0204208, KinCode = 0126", "明大理卿粲裔孫", "Auto-generated from PersonID = 0134213, KinCode = 0285"] |
| c_created_by | varchar(255) | 1 | 0.0002% | 0 | 174 | True | ["任思宇", "TTS", "BDDWJ"] |
| c_modified_by | varchar(255) | 533530 | 95.0253% | 19171 | 140 | True | ["任思宇", "HVDCS", "BDDWJ"] |
| c_created_date | TEXT | 2 | 0.0004% | 0 | 4785 | True | ["2026-04-01 19:25:25", "2026-04-06 21:09:22", "2026-06-01 10:42:42"] |
| c_modified_date | TEXT | 552701 | 98.4398% | 0 | 1151 | True | ["2026-04-06 21:18:40", "2010-07-18 00:00:00", "2010-07-12 00:00:00"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

| source key | target | basis | matched/non-NULL | match rate |
| --- | --- | --- | --- | --- |
| c_personid | BIOG_MAIN.c_personid | inferred join key | 561461/561461 | 100.0000% |
| c_kin_id | BIOG_MAIN.c_personid | inferred join key | 561461/561461 | 100.0000% |
| c_kin_code | KINSHIP_CODES.c_kincode | inferred join key | 561461/561461 | 100.0000% |

## First five rows

| c_personid | c_kin_id | c_kin_code | c_source | c_pages | c_notes | c_autogen_notes | c_created_by | c_modified_by | c_created_date | c_modified_date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 59224 | 86216 | -10000 | 62087 |  |  |  | load |  | 2023-03-11 00:00:00 |  |
| 118006 | 126426 | -10000 | 62087 |  |  |  | load |  | 2023-03-11 00:00:00 |  |
| 699773 | 425868 | -10000 | 38541 | lgid=630781 |  |  | 任思宇 |  | 2026-04-01 19:25:25 |  |
| 696115 | 696114 | -10000 | 68002 | lgid=294326 |  |  | 劉慧楠 | 劉慧楠 | 2025-11-05 00:00:00 | 2025-11-05 00:00:00 |
| 698146 | 698145 | -10000 | 57941 | lgid=1160956 |  |  | 陶恒 |  | 2026-01-14 19:52:24 |  |
