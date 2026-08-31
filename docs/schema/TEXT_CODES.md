# TEXT_CODES

Rows: **62,362**; columns: **24**.

Person identifier fields observed: none.

## Column audit

| column | SQLite type | NULL | NULL rate | empty | distinct | sampled | examples |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c_textid | INTEGER(11) | 0 | 0.0000% | 0 | 62362 | False | [0, 2031, 2032] |
| c_title_chn | varchar(255) | 0 | 0.0000% | 0 | 59386 | False | ["未知", "愛日齋叢鈔", "楓窗小牘"] |
| c_title | varchar(255) | 21 | 0.0337% | 0 | 59256 | False | ["Weizhi", "ai ri zhai cong chao", "Fengchuang xiaodu"] |
| c_title_trans | varchar(255) | 57868 | 92.7937% | 4238 | 224 | False | ["unkonwn", "(Handbook on Lichees)", "(Diary of a Trip to the Taiwan Sulphur Mines)"] |
| c_text_type_id | varchar(128) | 33264 | 53.3402% | 3528 | 78 | False | ["02", "0", "01021302"] |
| c_text_year | smallint(6) | 55511 | 89.0141% | 0 | 1051 | False | [0, 1279, 1126] |
| c_text_nh_code | smallint(6) | 32549 | 52.1936% | 0 | 50 | False | [0, 532, 545] |
| c_text_nh_year | smallint(6) | 61525 | 98.6578% | 0 | 39 | False | [0, 1, 4] |
| c_text_range_code | smallint(6) | 61780 | 99.0667% | 0 | 4 | False | [2, 0, 1] |
| c_bibl_cat_code | smallint(6) | 2340 | 3.7523% | 0 | 95 | False | [0, 147, 1] |
| c_extant | smallint(6) | 12315 | 19.7476% | 0 | 4 | False | [0, 1, 2] |
| c_text_country | smallint(6) | 13650 | 21.8883% | 0 | 11 | False | [0, 1, 5] |
| c_text_dy | smallint(6) | 6528 | 10.4679% | 0 | 47 | False | [0, 15, 20] |
| c_source | INTEGER(11) | 3140 | 5.0351% | 0 | 93 | False | [7596, 0, 27147] |
| c_pages | varchar(255) | 14602 | 23.4149% | 4279 | 9562 | False | ["17782", "12940", "12840"] |
| c_url_api | varchar(255) | 58075 | 93.1256% | 4278 | 10 | False | ["https://mhdb.mh.sinica.edu.tw/mingqing/mqww/search/details-poet.php?poetID=", "https://newarchive.ihp.sinica.edu.tw/sncaccgi/sncacFtp?ACTION=TQ,sncacFtpqf,SN… |
| c_url_api_coda | varchar(255) | 62361 | 99.9984% | 0 | 1 | False | [",2nd,search_simple"] |
| c_url_homepage | varchar(255) | 58073 | 93.1224% | 4278 | 11 | False | ["https://mhdb.mh.sinica.edu.tw/mingqing/mqww/", "https://newarchive.ihp.sinica.edu.tw/sncaccgi/sncacFtp?ID=241&SECU=872177956&PAGE=main@@7296748", "https://hi… |
| c_notes | TEXT | 45388 | 72.7815% | 2769 | 12227 | False | ["三十二卷。", "四十卷。", "宋人傳記資料索引1717頁。姚闢參與。一百卷。"] |
| c_title_alt_chn | varchar(255) | 55977 | 89.7614% | 4277 | 242 | False | ["後村大全集", "林登州集", "于忠肅集"] |
| c_created_by | varchar(255) | 200 | 0.3207% | 7 | 141 | False | ["TTS", "PKB", "BDSYX"] |
| c_modified_by | varchar(255) | 56581 | 90.7299% | 4278 | 60 | False | ["FCF", "HUWHS", "BDLJ"] |
| c_created_date | TEXT | 2075 | 3.3273% | 0 | 631 | False | ["2007-04-17 00:00:00", "2020-10-15 00:00:00", "2007-04-20 00:00:00"] |
| c_modified_date | TEXT | 60859 | 97.5899% | 0 | 514 | False | ["2007-06-27 00:00:00", "2013-12-16 00:00:00", "2008-01-13 00:00:00"] |

Distinct counts marked `True` are computed from a deterministic rowid sample; NULL/empty counts remain exact.

## Join-key evidence

No declared or conservatively inferred join key was recorded for this table.

## First five rows

| c_textid | c_title_chn | c_title | c_title_trans | c_text_type_id | c_text_year | c_text_nh_code | c_text_nh_year | c_text_range_code | c_bibl_cat_code | c_extant | c_text_country | c_text_dy | c_source | c_pages | c_url_api | c_url_api_coda | c_url_homepage | c_notes | c_title_alt_chn | c_created_by | c_modified_by | c_created_date | c_modified_date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 未知 | Weizhi | unkonwn |  | 0 | 0 | 0 |  | 0 | 0 | 0 | 0 |  |  |  |  |  |  |  | TTS | FCF | 2007-04-17 00:00:00 | 2007-06-27 00:00:00 |
| 2031 | 愛日齋叢鈔 | ai ri zhai cong chao |  |  | 1279 | 0 |  |  | 147 | 1 | 1 | 15 | 7596 | 17782 |  |  |  |  |  | TTS | HUWHS | 2007-04-17 00:00:00 | 2013-12-16 00:00:00 |
| 2032 | 楓窗小牘 | Fengchuang xiaodu |  |  | 1279 | 0 |  |  | 0 | 1 | 1 | 0 | 0 |  |  |  |  |  |  | TTS |  | 2007-04-17 00:00:00 |  |
| 2033 | 宋大詔令集 | Song Dazhaoling ji |  |  | 1126 | 0 |  |  | 0 | 1 | 1 | 0 | 0 |  |  |  |  |  |  | TTS |  | 2007-04-17 00:00:00 |  |
| 2034 | 國朝諸臣奏議 | Guochao Zhuchen zouyi |  |  | 1196 | 0 |  |  | 0 | 1 | 1 | 0 | 0 |  |  |  |  |  |  | TTS |  | 2007-04-17 00:00:00 |  |
