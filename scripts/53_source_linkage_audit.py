#!/usr/bin/env python3
"""Run the frozen precheck and audit source linkage in the read-only CBDB."""

from __future__ import annotations

import argparse
import json

from src.phase3 import frozen_precheck, source_linkage_audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-precheck", action="store_true")
    args = parser.parse_args()
    if not args.skip_precheck:
        precheck = frozen_precheck()
        print(f"Frozen precheck: {precheck['status']} ({len(precheck['frozen_files'])} files)")
    audit = source_linkage_audit()
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
