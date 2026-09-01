#!/usr/bin/env python3
"""Build target-independent source groups and apply the prespecified gate."""

from __future__ import annotations

import json

from src.phase3 import build_source_groups


if __name__ == "__main__":
    print(json.dumps(build_source_groups(), ensure_ascii=False, indent=2))
