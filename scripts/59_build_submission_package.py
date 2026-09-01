#!/usr/bin/env python3
"""Build and independently validate the final reproducible submission ZIP."""

from __future__ import annotations

import json

from src.phase3 import PHASE3_TABLES, ROOT, write_json
from src.phase3_packaging import build_zip, submission_entries


def main() -> None:
    result = build_zip(ROOT / "submission/cbdb_final_submission.zip", submission_entries())
    write_json(PHASE3_TABLES / "submission_package_status.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
