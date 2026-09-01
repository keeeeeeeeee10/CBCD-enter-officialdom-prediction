# Release validation note

Status: **PUBLIC PAYLOAD PASS**

The two frozen manuscript PDFs retain their canonical SHA-256 values. The public repository contains an explicit lightweight allowlist and excludes SQLite databases, raw CBDB data, models, full splits, row-level predictions, large feature matrices, release archives, logs, and caches.

The historical `release_validation_report.json` is intentionally not published. It embedded absolute local paths and outer ZIP metadata from an earlier deterministic package build, whereas the final submission ZIP is stored outside Git with its own sidecar hash. Excluding that stale, self-referential report avoids claiming that its archived ZIP hash describes the current external archive.

Run `python scripts/verify_public_release.py` for the non-experimental public-tree checks. The complete Phase 3.1.1 audit status remains recorded in the other documents in this directory; those full-checkout audits require private frozen artifacts that are not redistributed here.
