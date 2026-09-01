# Reproducibility

Run `bash scripts/run_phase3.sh` from the project root after the frozen Phase 1--2.6 artifacts are present. The runner validates known hashes and SQLite `PRAGMA quick_check`, audits sources, regenerates Phase 3 tables/figures/LaTeX, compiles both PDFs, checks citations and pagination, runs tests, and creates validated archives.

The canonical seed is 42. Phase 3 performs no hyperparameter search, new-model tuning, GNN, or PageRank run. The full SQLite files and 661,124-row feature master are excluded from archives; `scripts/01_download_cbdb.py` obtains the official release and verifies its declared SHA256.
