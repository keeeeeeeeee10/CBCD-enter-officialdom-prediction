# Sentinel and field-aware missingness policy

CBDB sentinel handling is field-specific. Raw database columns and Phase 1 files are never overwritten, and global operations such as `df.replace(0, np.nan)` are prohibited.

| Field semantic | Derived treatment | Rationale |
| --- | --- | --- |
| Calendar years | `0`, `-1`, `-999`, `-9999`, values below -1200 or above 2100 → missing | Explicit Phase 1.5 time policy; retain raw companion columns |
| Person/kin/association IDs used as graph nodes | `0`, `-1`, `-999`, `-9999`, `-10000` → invalid ID | Never create person 0 or unknown-person nodes |
| Address/office/institution relation IDs | Zero/negative sentinels excluded from edges, but raw value retained | Code tables may contain an Unknown row, which is not a substantive place/office edge |
| Code-table categories | Keep mapped 0/−1 as explicit Unknown/Missing categories when the code table defines them | Categorical semantics differ from identifier semantics |
| Counts and presence flags | Zero remains zero | It represents observed absence in the selected table, not missing numeric data |
| `BIOG_MAIN.c_female` | 0 remains the database's male code; NULL is unknown | Zero is substantive here |

The shared `src/cleaning.py` helpers require callers to declare year or identifier semantics. Ambiguous fields remain raw until their code table and empirical distribution are audited.
