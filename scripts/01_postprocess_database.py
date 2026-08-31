#!/usr/bin/env python3
"""Apply official convenience views and optionally build ADDRESSES on the working copy."""

from __future__ import annotations

import argparse
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import configured_path, load_config, project_path
from src.db import connect_readonly, scalar
from src.utils import atomic_write_text, setup_logging


def run_views(official_script: Path, database: Path, log_path: Path, logger) -> None:
    if shutil.which("sqlite3"):
        result = subprocess.run(
            ["bash", str(official_script), str(database)],
            cwd=PROJECT_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        atomic_write_text(log_path, result.stdout)
        for line in result.stdout.splitlines():
            logger.info("official views | %s", line)
        if result.returncode:
            raise RuntimeError(f"Official create_views.sh failed with exit code {result.returncode}; see {log_path}")
        return

    logger.warning("sqlite3 CLI is unavailable; executing SQL blocks extracted verbatim from official create_views.sh")
    script = official_script.read_text(encoding="utf-8")
    blocks = re.findall(r"<<'SQL'\n(.*?)\nSQL", script, flags=re.DOTALL)
    if not blocks:
        raise RuntimeError("No official SQL blocks could be parsed from create_views.sh")
    messages = ["sqlite3 CLI missing; used Python sqlite3 to execute official SQL heredoc blocks."]
    with sqlite3.connect(database) as connection:
        for index, sql in enumerate(blocks, 1):
            connection.executescript(sql)
            messages.append(f"Executed official SQL block {index}/{len(blocks)}")
    atomic_write_text(log_path, "\n".join(messages) + "\n")


def run_addresses(official_script: Path, database: Path, log_path: Path, rebuild: bool, logger) -> None:
    with connect_readonly(database) as connection:
        exists = scalar(connection, "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='ADDRESSES'")
        rows = scalar(connection, "SELECT COUNT(*) FROM ADDRESSES") if exists else 0
    if exists and rows and not rebuild:
        message = f"SKIP ADDRESSES: existing official-derived table has {rows} rows. Use --rebuild-addresses to regenerate."
        logger.info(message)
        if not log_path.exists():
            atomic_write_text(log_path, message + "\n")
        return

    result = subprocess.run(
        [sys.executable, str(official_script), "--db", str(database)],
        cwd=PROJECT_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    atomic_write_text(log_path, result.stdout)
    if result.returncode:
        logger.warning("Optional ADDRESSES build failed with exit code %d; full error is in %s", result.returncode, log_path)
        return
    logger.info("Official ADDRESSES build succeeded; full log: %s", log_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild-addresses", action="store_true")
    args = parser.parse_args()
    config = load_config()
    logger = setup_logging("postprocess", configured_path(config, "paths", "logs") / "database_postprocess.log")
    repo = project_path(config, config["database"]["official_repo"])
    views_script = repo / "scripts" / "create_views.sh"
    addresses_script = repo / "scripts" / "create_addresses_table.py"
    database = configured_path(config, "database", "working_db")
    if not database.exists():
        raise FileNotFoundError(f"Working database does not exist: {database}")
    if not views_script.exists() or not addresses_script.exists():
        raise FileNotFoundError("Official post-processing scripts are missing under external/cbdb_sqlite/scripts")

    run_views(views_script, database, configured_path(config, "paths", "logs") / "create_views.log", logger)
    run_addresses(
        addresses_script,
        database,
        configured_path(config, "paths", "logs") / "create_addresses.log",
        args.rebuild_addresses,
        logger,
    )
    with connect_readonly(database) as connection:
        view_count = scalar(connection, "SELECT COUNT(*) FROM sqlite_master WHERE type='view' AND name NOT LIKE 'sqlite_%'")
        required = scalar(connection, "SELECT COUNT(*) FROM sqlite_master WHERE type='view' AND name IN ('View_PeopleData','View_EntryData')")
        address_rows = scalar(connection, "SELECT COUNT(*) FROM ADDRESSES") if scalar(connection, "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='ADDRESSES'") else None
    if required != 2:
        raise RuntimeError("Required official views View_PeopleData/View_EntryData were not both created")
    logger.info("Post-process result: views=%s, ADDRESSES rows=%s", view_count, address_rows if address_rows is not None else "unavailable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

