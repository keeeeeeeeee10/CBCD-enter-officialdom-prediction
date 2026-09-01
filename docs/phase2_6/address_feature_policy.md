# Phase 2.6 Address Feature Policy

`addr_type_name` is not treated as pure geography. It records how CBDB describes an address (for example household, birth, ancestral, banner, or another address-record type), so Phase 2.6 assigns it to **documentation-linked address semantics**.

The staged address audit separates:

1. address observability (`has_geography`, valid coordinates);
2. historical administrative geography (province/circuit, prefecture, county);
3. continuous physical location (latitude, longitude, dynasty-capital distance);
4. address-record semantics (`addr_type_name`);
5. train-only unsupervised regional density.

The supervised local ENTRY prior remains a separate sensitivity and is not part of pure geography. H_STRUCT excludes `addr_type_name` and the supervised prior. These are prediction associations with ENTRY record presence, not causal geographic effects.
