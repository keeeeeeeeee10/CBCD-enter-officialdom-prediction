#!/usr/bin/env python3
"""Conditionally run the one-shot locked source-group confirmation."""

from __future__ import annotations

import json

from src.phase3 import run_source_confirmation


if __name__ == "__main__":
    print(json.dumps(run_source_confirmation(), ensure_ascii=False, indent=2))
