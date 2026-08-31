# ETHNICITY_TRIBE_CODES

Rows: **498**; columns: **11**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_ethnicity_code | smallint(6) | 0 | 0.0000% | 0 | 498 | False | [0, 1, 3] |
| c_group_code | smallint(6) | 0 | 0.0000% | 0 | 170 | False | [0, 1, 2] |
| c_subgroup_code | smallint(6) | 3 | 0.6024% | 0 | 41 | False | [0, 1, 3] |
| c_altname_code | smallint(6) | 3 | 0.6024% | 0 | 8 | False | [0, 1, 2] |
| c_name_chn | varchar(255) | 0 | 0.0000% | 0 | 494 | False | ["未詳", "漢", "吐蕃"] |
| c_name | varchar(255) | 0 | 0.0000% | 0 | 463 | False | ["unknown", "Han", "tu bo"] |
| c_ethno_legal_cat | varchar(255) | 355 | 71.2851% | 0 | 5 | False | ["Semuren", "Kitan", "Mongol"] |
| c_romanized | varchar(255) | 292 | 58.6345% | 0 | 131 | False | ["Turk", "Kitan", "Uyghur"] |
| c_surname | varchar(255) | 446 | 89.5582% | 0 | 1 | False | ["S"] |
| c_notes | TEXT | 216 | 43.3735% | 0 | 219 | False | ["本西羌屬，蓋百有五十種（新唐書）；本漢西羌之地，或云南涼禿髮利鹿孤之後，其子孫以禿髮為國號，語訛為吐蕃（舊五代史）；本漢西羌之地，其種落莫知所出．或云南涼禿髮利鹿孤之後，其子孫以禿髮為國號，語訛故謂之吐蕃（宋史）", "突厥阿史那氏，蓋古匈奴北部也．居金山之陽，臣于蠕蠕，種裔繁衍．至吐門，遂彊大{A14B}{A1… |
| c_sortorder | smallint(6) | 1 | 0.2008% | 0 | 497 | False | [1, 2, 3] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_ethnicity_code | c_group_code | c_subgroup_code | c_altname_code | c_name_chn | c_name | c_ethno_legal_cat | c_romanized | c_surname | c_notes | c_sortorder |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 0 | 0 | 0 | 未詳 | unknown |  |  |  |  | 1 |
| 1 | 1 | 1 | 1 | 漢 | Han |  |  |  |  | 2 |
| 3 | 2 | 1 | 1 | 吐蕃 | tu bo |  |  |  | 本西羌屬，蓋百有五十種（新唐書）；本漢西羌之地，或云南涼禿髮利鹿孤之後，其子孫以禿髮為國號，語訛為吐蕃（舊五代史）；本漢西羌之地，其種落莫知所出．或云南涼禿髮利鹿孤之後，其子孫以禿髮為國號，語訛故謂之吐蕃（宋史） | 3 |
| 4 | 4 | 1 | 1 | 突厥 | tu jue |  | Turk |  | 突厥阿史那氏，蓋古匈奴北部也．居金山之陽，臣于蠕蠕，種裔繁衍．至吐門，遂彊大{A14B}{A14B}隋大業之亂，始畢可汗咄吉嗣立，華人多往依之，契丹、室韋、吐谷渾、高昌皆役屬（新唐書） | 34 |
| 5 | 5 | 1 | 1 | 契丹 | qi dan |  | Kitan |  | "本東胡種，其先為匈奴所破，保鮮卑山．{A14B}{A14B}逃潢水之南，黃龍之北．至元魏，自號曰契丹{A14B}{A14B}其君大賀氏，有勝兵四萬，析八部，臣于突厥（新唐書）；古匈奴之種也（舊五代史）；契丹自後魏以來，名見中國．或曰與庫莫奚同類而異種{A14B}{A14B}得鮮卑之故地，故又以為鮮卑之遺種{A14B… | 36 |
