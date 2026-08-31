# CBDB table relationships

`declared foreign key` means SQLite exposes a constraint through `PRAGMA foreign_key_list`. `inferred join key` means a conservative semantic/name match whose observed values were validated; it is not represented as a database constraint.

## Required person-level paths

- `BIOG_MAIN.c_personid` → `ENTRY_DATA.c_personid` (Target V1 source; reverse presentation of the validated child-to-parent join)
- `BIOG_MAIN.c_personid` → `KIN_DATA.c_personid`
- `BIOG_MAIN.c_personid` → `ASSOC_DATA.c_personid`
- `BIOG_MAIN.c_personid` → `BIOG_ADDR_DATA.c_personid`
- `BIOG_MAIN.c_personid` → `STATUS_DATA.c_personid`
- `BIOG_MAIN.c_personid` → `POSTING_DATA.c_personid` / `POSTED_TO_OFFICE_DATA.c_personid`

These are one-to-many paths. Each child must be aggregated to one person before joining; joining raw child tables together would create a Cartesian-like fan-out.

## Machine-audited relationships

| source | target | basis | matched/non-NULL | match rate |
| --- | --- | --- | --- | --- |
| BIOG_MAIN.c_index_addr_id | ADDR_CODES.c_addr_id | inferred join key | 392883/392883 | 100.0000% |
| BIOG_MAIN.c_dy | DYNASTIES.c_dy | inferred join key | 659540/659540 | 100.0000% |
| ENTRY_DATA.c_personid | BIOG_MAIN.c_personid | inferred join key | 264775/264775 | 100.0000% |
| ENTRY_DATA.c_entry_code | ENTRY_CODES.c_entry_code | inferred join key | 264775/264775 | 100.0000% |
| ENTRY_DATA.c_kin_code | KINSHIP_CODES.c_kincode | inferred join key | 264775/264775 | 100.0000% |
| ENTRY_DATA.c_kin_id | BIOG_MAIN.c_personid | inferred join key | 264775/264775 | 100.0000% |
| ENTRY_DATA.c_assoc_code | ASSOC_CODES.c_assoc_code | inferred join key | 264775/264775 | 100.0000% |
| ENTRY_DATA.c_assoc_id | BIOG_MAIN.c_personid | inferred join key | 264775/264775 | 100.0000% |
| ENTRY_DATA.c_entry_dy | DYNASTIES.c_dy | inferred join key | 0/0 |  |
| ENTRY_DATA.c_entry_addr_id | ADDR_CODES.c_addr_id | inferred join key | 15218/15222 | 99.9737% |
| KIN_DATA.c_personid | BIOG_MAIN.c_personid | inferred join key | 561461/561461 | 100.0000% |
| KIN_DATA.c_kin_id | BIOG_MAIN.c_personid | inferred join key | 561461/561461 | 100.0000% |
| KIN_DATA.c_kin_code | KINSHIP_CODES.c_kincode | inferred join key | 561461/561461 | 100.0000% |
| ASSOC_DATA.c_assoc_code | ASSOC_CODES.c_assoc_code | inferred join key | 189970/189970 | 100.0000% |
| ASSOC_DATA.c_personid | BIOG_MAIN.c_personid | inferred join key | 189970/189970 | 100.0000% |
| ASSOC_DATA.c_kin_code | KINSHIP_CODES.c_kincode | inferred join key | 189970/189970 | 100.0000% |
| ASSOC_DATA.c_kin_id | BIOG_MAIN.c_personid | inferred join key | 189970/189970 | 100.0000% |
| ASSOC_DATA.c_assoc_id | BIOG_MAIN.c_personid | inferred join key | 189970/189970 | 100.0000% |
| ASSOC_DATA.c_assoc_kin_code | KINSHIP_CODES.c_kincode | inferred join key | 189970/189970 | 100.0000% |
| ASSOC_DATA.c_assoc_kin_id | BIOG_MAIN.c_personid | inferred join key | 189970/189970 | 100.0000% |
| ASSOC_DATA.c_tertiary_personid | BIOG_MAIN.c_personid | inferred join key | 140496/140496 | 100.0000% |
| ASSOC_DATA.c_addr_id | ADDR_CODES.c_addr_id | inferred join key | 156671/156671 | 100.0000% |
| ASSOC_DATA.c_assoc_claimer_id | BIOG_MAIN.c_personid | inferred join key | 135803/135803 | 100.0000% |
| STATUS_DATA.c_personid | BIOG_MAIN.c_personid | inferred join key | 73250/73250 | 100.0000% |
| STATUS_DATA.c_status_code | STATUS_CODES.c_status_code | inferred join key | 73250/73250 | 100.0000% |
| BIOG_ADDR_DATA.c_personid | BIOG_MAIN.c_personid | inferred join key | 460772/460772 | 100.0000% |
| BIOG_ADDR_DATA.c_addr_id | ADDR_CODES.c_addr_id | inferred join key | 460772/460772 | 100.0000% |
| BIOG_ADDR_DATA.c_natal | ADDR_CODES.c_addr_id | inferred join key | 71244/71244 | 100.0000% |
| BIOG_INST_DATA.c_personid | BIOG_MAIN.c_personid | inferred join key | 567/567 | 100.0000% |
| BIOG_INST_DATA.c_bi_role_code | BIOG_INST_CODES.c_bi_role_code | inferred join key | 567/567 | 100.0000% |
| BIOG_TEXT_DATA.c_textid | TEXT_CODES.c_textid | inferred join key | 53289/53289 | 100.0000% |
| BIOG_TEXT_DATA.c_personid | BIOG_MAIN.c_personid | inferred join key | 53289/53289 | 100.0000% |
| BIOG_TEXT_DATA.c_role_id | TEXT_ROLE_CODES.c_role_id | inferred join key | 53289/53289 | 100.0000% |
| POSTING_DATA.c_personid | BIOG_MAIN.c_personid | inferred join key | 590835/590835 | 100.0000% |
| POSTED_TO_OFFICE_DATA.c_personid | BIOG_MAIN.c_personid | inferred join key | 590866/590866 | 100.0000% |
| POSTED_TO_OFFICE_DATA.c_office_id | OFFICE_CODES.c_office_id | inferred join key | 590866/590866 | 100.0000% |
| POSTED_TO_OFFICE_DATA.c_posting_id | POSTING_DATA.c_posting_id | inferred join key | 590866/590866 | 100.0000% |
| POSTED_TO_OFFICE_DATA.c_office_id_backup | OFFICE_CODES.c_office_id | inferred join key | 12112/15431 | 78.4913% |
| POSTED_TO_OFFICE_DATA.c_dy | DYNASTIES.c_dy | inferred join key | 589186/589186 | 100.0000% |
| ADDRESSES.c_addr_id | ADDR_CODES.c_addr_id | inferred join key | 64279/64279 | 100.0000% |
