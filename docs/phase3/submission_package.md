# Submission and review packages

`scripts/59_build_submission_package.py` creates the reproducible author submission. `scripts/60_package_final_review.py` creates the bounded human-review archive. Both contain a CSV/Markdown payload manifest and are validated by ZIP CRC plus per-file SHA256. Database files, the virtual environment, full feature master, caches, temporary LaTeX files, raw prediction matrices, and old review archives are excluded.
