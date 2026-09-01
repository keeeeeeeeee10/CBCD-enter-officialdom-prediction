# Source-holdout feasibility audit

**Status:** `SOURCE_GROUP_CONFIRMATION_NOT_FEASIBLE`

## Audited schema

The read-only SQLite schema contains `BIOG_SOURCE_DATA`, linking `c_personid` to
`c_textid`.  The explicit `c_main_source` flag identifies primary-source rows;
`TEXT_CODES` supplies titles and text/bibliographic type fields, with
`TEXT_BIBLCAT_CODES` as a category lookup.  There is no sequence field;
`c_pages` is a locator, not an ordering rule.

Because some people have multiple rows marked as primary, groups are connected
components of the person--source bipartite graph restricted to
`c_main_source=1`.  This target-independent rule neither selects a minimum/first
source per person nor allows a marked primary source to cross partitions.

## Prespecified gate

- Eligible linked people: **452,035**
- Coverage of the 661,124-person feature master: **68.37%**
- Connected source groups: **145**
- Largest group: **448,632** people (**99.25%**)
- Primary-source edges: **500,639**
- Target used to define groups or assign partitions: **No**
- Model performance used to choose the split: **No**

Failed criteria:

- `largest_group_at_most_20_percent`

## Decision

No source-group model is run because the prespecified gate failed.  This audit concerns source-group distribution shift only.  Even a
successful result would not constitute external ground-truth validation of the
latent historical state $T$.
