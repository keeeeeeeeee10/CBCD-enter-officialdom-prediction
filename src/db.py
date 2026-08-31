"""SQLite access helpers that keep large CBDB tables inside SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Iterable


def quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def connect_readonly(path: Path, busy_timeout_ms: int = 60_000) -> sqlite3.Connection:
    uri = f"file:{path.resolve().as_posix()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True, timeout=busy_timeout_ms / 1000)
    connection.row_factory = sqlite3.Row
    connection.execute(f"PRAGMA busy_timeout={int(busy_timeout_ms)}")
    connection.execute("PRAGMA query_only=ON")
    return connection


def connect_writable(path: Path, busy_timeout_ms: int = 60_000) -> sqlite3.Connection:
    connection = sqlite3.connect(path, timeout=busy_timeout_ms / 1000)
    connection.row_factory = sqlite3.Row
    connection.execute(f"PRAGMA busy_timeout={int(busy_timeout_ms)}")
    return connection


def object_names(connection: sqlite3.Connection, kinds: Iterable[str] = ("table", "view")) -> list[tuple[str, str]]:
    placeholders = ",".join("?" for _ in kinds)
    query = f"""
        SELECT name, type
        FROM sqlite_master
        WHERE type IN ({placeholders}) AND name NOT LIKE 'sqlite_%'
        ORDER BY type, name
    """
    return [(row["name"], row["type"]) for row in connection.execute(query, tuple(kinds))]


def table_exists(connection: sqlite3.Connection, name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE lower(name)=lower(?) AND type IN ('table','view')",
        (name,),
    ).fetchone()
    return row is not None


def actual_object_name(connection: sqlite3.Connection, name: str) -> str | None:
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE lower(name)=lower(?) AND type IN ('table','view')",
        (name,),
    ).fetchone()
    return row[0] if row else None


def columns(connection: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(f"PRAGMA table_info({quote_identifier(table)})")]


def column_names(connection: sqlite3.Connection, table: str) -> list[str]:
    return [column["name"] for column in columns(connection, table)]


def find_column(connection: sqlite3.Connection, table: str, candidates: Iterable[str]) -> str | None:
    lookup = {name.lower(): name for name in column_names(connection, table)}
    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]
    return None


def scalar(connection: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> Any:
    row = connection.execute(query, params).fetchone()
    return None if row is None else row[0]

