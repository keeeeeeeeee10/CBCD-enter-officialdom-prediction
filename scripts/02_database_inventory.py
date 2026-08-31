#!/usr/bin/env python3
"""Inventory every user table and view without loading their contents into pandas."""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import configured_path, load_config
from src.db import columns, connect_readonly, object_names, quote_identifier
from src.utils import atomic_write_text, markdown_table, setup_logging


def main() -> int:
    config = load_config()
    tables_dir = configured_path(config, "paths", "tables")
    schema_dir = configured_path(config, "paths", "schema_docs")
    logger = setup_logging("inventory", configured_path(config, "paths", "logs") / "database_inventory.log")
    database = configured_path(config, "database", "working_db")
    if not database.exists():
        raise FileNotFoundError(f"Working database does not exist: {database}")

    inventory = []
    with connect_readonly(database, config["database"]["busy_timeout_ms"]) as connection:
        objects = object_names(connection)
        logger.info("Found %d user tables/views", len(objects))
        for index, (name, kind) in enumerate(objects, 1):
            start = time.monotonic()
            row_count = connection.execute(
                f"SELECT COUNT(*) FROM {quote_identifier(name)}"
            ).fetchone()[0]
            n_columns = len(columns(connection, name))
            elapsed = time.monotonic() - start
            inventory.append(
                {
                    "table_name": name,
                    "type": kind,
                    "row_count": row_count,
                    "n_columns": n_columns,
                    "count_seconds": round(elapsed, 3),
                }
            )
            logger.info("[%d/%d] %-32s %-5s rows=%d columns=%d", index, len(objects), name, kind, row_count, n_columns)

    inventory.sort(key=lambda row: (-row["row_count"], row["type"], row["table_name"]))
    csv_path = tables_dir / "database_inventory.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(inventory[0]))
        writer.writeheader()
        writer.writerows(inventory)

    table_count = sum(row["type"] == "table" for row in inventory)
    view_count = sum(row["type"] == "view" for row in inventory)
    markdown = [
        "# CBDB database inventory",
        "",
        f"Database: `{database.relative_to(PROJECT_ROOT)}`",
        "",
        f"User tables: **{table_count}**; views: **{view_count}**. SQLite internal objects are excluded.",
        "",
        "Counts are executed with `SELECT COUNT(*)` inside SQLite; table contents are not loaded into pandas.",
        "",
        markdown_table(
            ["object", "type", "rows", "columns", "count seconds"],
            ([row["table_name"], row["type"], row["row_count"], row["n_columns"], row["count_seconds"]] for row in inventory),
        ),
        "",
    ]
    atomic_write_text(schema_dir / "database_inventory.md", "\n".join(markdown))

    views = sorted((row for row in inventory if row["type"] == "view"), key=lambda row: row["table_name"])
    with (schema_dir / "views.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "row_count", "n_columns"])
        writer.writeheader()
        for row in views:
            writer.writerow({key: row[{"name": "table_name"}.get(key, key)] for key in writer.fieldnames})
    required = {"View_PeopleData", "View_EntryData"}
    observed = {row["table_name"] for row in views}
    missing = sorted(required - observed)
    if missing:
        raise RuntimeError(f"Required official views are missing: {missing}")
    logger.info("Inventory written to %s; required official views confirmed", csv_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

