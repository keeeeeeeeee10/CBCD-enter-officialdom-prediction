#!/usr/bin/env python3
"""Build and independently validate the bounded final review bundle."""

from __future__ import annotations

import json

from src.phase3 import PHASE3_TABLES, ROOT, write_json
from src.phase3_packaging import build_zip, review_entries


def main() -> None:
    result = build_zip(
        ROOT / "review_bundles/cbdb_final_paper_review_bundle.zip",
        review_entries(),
    )
    write_json(PHASE3_TABLES / "review_package_status.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
