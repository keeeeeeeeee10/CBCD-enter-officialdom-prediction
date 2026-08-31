# Index-year provenance audit

The real schema is `BIOG_MAIN.c_index_year`, `c_index_year_type_code`, and `c_index_year_source_id`, decoded by `INDEXYEAR_TYPE_CODES`. Observed type values include official two-character codes and concatenated chains such as `2912` and `0512`; every observed chain is parsed component by component.

Only exact provenance `01` (directly based on the focal person's birth year) is classified SAFE. UNKNOWN is never promoted to SAFE. Kin/recursive chains without explicit career outcomes are CONDITIONAL; any chain using examinations/entry, death, or descendant information is UNSAFE.

## Person-level classification

| class | people | share |
| --- | --- | --- |
| UNKNOWN | 353125 | 53.41% |
| UNSAFE | 159087 | 24.06% |
| CONDITIONAL | 88772 | 13.43% |
| SAFE | 60140 | 9.10% |

`c_index_year_source_id` is nonzero for **146,761** people. Match counts to `BIOG_MAIN` are reported per provenance value; it is an upstream source-person identifier, not a calendar year.

## Provenance explicitly dependent on ENTRY information

| observed code | components | description | people | ENTRY positives | class |
| --- | --- | --- | --- | --- | --- |
| 05 | 05 | Based on jinshi year -30 | 64125 | 64125 | UNSAFE |
| 06 | 06 | Based on Husband's jinshi year -27 | 5057 | 10 | UNSAFE |
| 07 | 07 | Based on juren year - 27 | 3296 | 3296 | UNSAFE |
| 0512 | 05;12 | Based on jinshi year -30 -> Based on Father's Index Year + 30 | 1234 | 316 | UNSAFE |
| 0528 | 05;28 | Based on jinshi year -30 -> Based on Grandfather's Index Year + 60 | 303 | 122 | UNSAFE |
| 0712 | 07;12 | Based on juren year - 27 -> Based on Father's Index Year + 30 | 242 | 105 | UNSAFE |
| 051212 | 05;12;12 | Based on jinshi year -30 -> Based on Father's Index Year + 30 -> Based on Father's Index Year + 30 | 77 | 20 | UNSAFE |
| 08 | 08 | Based on Husband's juren year -24 | 49 | 0 | UNSAFE |
| 0728 | 07;28 | Based on juren year - 27 -> Based on Grandfather's Index Year + 60 | 39 | 15 | UNSAFE |
| 051204 | 05;12;04 | Based on jinshi year -30 -> Based on Father's Index Year + 30 -> Based on Husband's Index Year + 3 | 19 | 1 | UNSAFE |
| 09 | 09 | Based on Xiucai year -21 | 17 | 17 | UNSAFE |
| 052812 | 05;28;12 | Based on jinshi year -30 -> Based on Grandfather's Index Year + 60 -> Based on Father's Index Year + 30 | 15 | 5 | UNSAFE |
| 051228 | 05;12;28 | Based on jinshi year -30 -> Based on Father's Index Year + 30 -> Based on Grandfather's Index Year + 60 | 12 | 5 | UNSAFE |
| 071212 | 07;12;12 | Based on juren year - 27 -> Based on Father's Index Year + 30 -> Based on Father's Index Year + 30 | 10 | 5 | UNSAFE |
| 071204 | 07;12;04 | Based on juren year - 27 -> Based on Father's Index Year + 30 -> Based on Husband's Index Year + 3 | 5 | 0 | UNSAFE |
| 071228 | 07;12;28 | Based on juren year - 27 -> Based on Father's Index Year + 30 -> Based on Grandfather's Index Year + 60 | 5 | 2 | UNSAFE |
| 0912 | 09;12 | Based on Xiucai year -21 -> Based on Father's Index Year + 30 | 4 | 2 | UNSAFE |
| 10 | 10 | Based on Husband's Xiucai year - 18 | 3 | 0 | UNSAFE |
| 051218 | 05;12;18 | Based on jinshi year -30 -> Based on Father's Index Year + 30 -> Based on Husband's Index Year + 3 (Concubine) | 3 | 0 | UNSAFE |
| 071218 | 07;12;18 | Based on juren year - 27 -> Based on Father's Index Year + 30 -> Based on Husband's Index Year + 3 (Concubine) | 2 | 0 | UNSAFE |
| 05121228 | 05;12;12;28 | Based on jinshi year -30 -> Based on Father's Index Year + 30 -> Based on Father's Index Year + 30 -> Based on Grandfather's Index Year + 60 | 1 | 0 | UNSAFE |
| 05122804 | 05;12;28;04 | Based on jinshi year -30 -> Based on Father's Index Year + 30 -> Based on Grandfather's Index Year + 60 -> Based on Husband's Index Year + 3 | 1 | 0 | UNSAFE |
| 05122818 | 05;12;28;18 | Based on jinshi year -30 -> Based on Father's Index Year + 30 -> Based on Grandfather's Index Year + 60 -> Based on Husband's Index Year + 3 (Concubine) | 1 | 0 | UNSAFE |
| 052804 | 05;28;04 | Based on jinshi year -30 -> Based on Grandfather's Index Year + 60 -> Based on Husband's Index Year + 3 | 1 | 0 | UNSAFE |
| 052828 | 05;28;28 | Based on jinshi year -30 -> Based on Grandfather's Index Year + 60 -> Based on Grandfather's Index Year + 60 | 1 | 0 | UNSAFE |
| 072812 | 07;28;12 | Based on juren year - 27 -> Based on Grandfather's Index Year + 60 -> Based on Father's Index Year + 30 | 1 | 1 | UNSAFE |

Official components `05`/`06`/`07`/`08`/`09`/`10` use jinshi, juren or xiucai years (including a husband's examination year). This creates the path `ENTRY information → index_year → predict ENTRY` and is direct derived-target leakage.

The safe person-level field is written separately as `safe_index_year`; raw `index_year` is preserved. Invalid year sentinels and values outside the configured historical range are never copied into the safe field.
