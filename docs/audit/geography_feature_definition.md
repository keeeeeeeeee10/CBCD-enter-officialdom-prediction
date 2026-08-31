# Geography feature definition

`primary_background_address` is selected only from official background-like address types: Basic Affiliation, Birth Address, Household Registration, Household Address, Ancestral Address, Actual Residence, Alternate Basic Affiliation, and Qing Banner background. Death, burial, exile, travel, migration-route, and other later-life types are excluded.

Selection is deterministic: official address-type priority first; then agreement with `BIOG_MAIN.c_index_addr_id`, natal flag, relation-table source, sequence, and address ID. The official Basic Affiliation is preferred because CBDB defines it as the single judgment-based index affiliation. We do not select an arbitrary first address.

For the time-varying `ADDRESSES` hierarchy, a valid SAFE birth year is the reference year; otherwise the dynasty midpoint is used as an approximation. The matching interval is preferred, followed by the nearest interval, hierarchy completeness, coordinate availability, and narrower interval. County/prefecture/province fields preserve historical hierarchy IDs and are not mapped to modern provinces.

Capital distance uses Haversine kilometers. Multi-capital Song and Ming entries use SAFE birth year when available; otherwise a documented dynasty-level canonical capital is used. Missing or invalid coordinates remain missing. `local_cbdb_person_count` is a non-target count at the selected address and `local_address_density=log(1+count)`. `local_entry_prior` is deliberately absent here and is derived train-only/OOF inside the model pipeline.

Selected background geography for **391,620** people (59.24%); valid coordinates for **382,294** people (57.82%).

Top selected address types:

- Basic Affiliation: 378,526
- Household address: 7,397
- Eight Banner Qing Dynasty: 4,182
- Ancestral Address: 815
- Birth Address: 345
- Actual Residence: 334
- Household Registration Address: 19
- Alternate basic affiliation: 2
