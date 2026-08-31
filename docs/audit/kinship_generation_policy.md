# Kinship generation and core-family policy

The real database tables are `KINSHIP_CODES` (488 official codes) and `KIN_DATA`. Classification first uses `c_upstep`, `c_dwnstep`, `c_marstep`, and `c_colstep`; standardized official relation symbols identify the requested specific relations. Chinese/English labels are secondary evidence, mainly for conservative non-blood exclusions.

## Generation taxonomy

| class | official codes | KIN_DATA records |
| --- | --- | --- |
| descendant | 150 | 178056 |
| same_generation | 55 | 122044 |
| parent_generation | 28 | 120919 |
| spouse | 13 | 59414 |
| ancestor | 93 | 54936 |
| affinal | 138 | 23346 |
| unknown | 11 | 2746 |

## Specifically identified relations

| relation | official codes | KIN_DATA records |
| --- | --- | --- |
| son | 38 | 112628 |
| father | 1 | 91998 |
| older_sibling | 7 | 58093 |
| younger_sibling | 7 | 58087 |
| paternal_grandfather | 1 | 29095 |
| mother | 1 | 18907 |
| daughter | 21 | 6114 |
| paternal_grandmother | 1 | 789 |
| maternal_grandfather | 1 | 314 |
| maternal_grandmother | 1 | 21 |

## Frozen core graph rule

Core blood-family edges include direct biological parent/child, grandparent/grandchild, and identifiable full/half sibling relations. Official step/adoptive/betrothed markers, all marriage/affinal relations, distant kin, unknown `99/100` direction steps, invalid identifiers, self-loops, and endpoints absent from `BIOG_MAIN` are excluded from components.

The normalized edge table retains **281,447** unique unordered person pairs, of which **203,286** are core blood-family edges. It excluded **2** rows during identifier cleaning before endpoint/self-loop checks and **0** rows with an endpoint outside the modeling population. Reciprocal source rows are collapsed while the selected original direction, code, and official step fields are retained.

Descendants are classified but excluded from Strict Temporal Family features in the first specification. Same-generation relatives remain CONDITIONAL. Spouse and affinal relations never enter the first core-family component graph.
