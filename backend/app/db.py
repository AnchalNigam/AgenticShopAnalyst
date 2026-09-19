"""PostgreSQL connection pool and database service layer for AgenticShop."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
import psycopg
from psycopg_pool import ConnectionPool

# Locate project root and load .env
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

_pool: ConnectionPool | None = None


def get_database_url() -> str:
    """Retrieve DATABASE_URL from environment variables."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set.")
    return database_url


def init_pool(min_size: int = 1, max_size: int = 10) -> ConnectionPool:
    """Initialize the PostgreSQL connection pool."""
    global _pool
    if _pool is None or _pool.closed:
        _pool = ConnectionPool(
            conninfo=get_database_url(),
            min_size=min_size,
            max_size=max_size,
            open=True,
            timeout=10.0,
        )
    return _pool


def close_pool() -> None:
    """Close all connections in the pool cleanly."""
    global _pool
    if _pool is not None and not _pool.closed:
        _pool.close()
        _pool = None


def get_pool() -> ConnectionPool:
    """Return the active connection pool, initializing it if necessary."""
    global _pool
    if _pool is None or _pool.closed:
        return init_pool()
    return _pool


@contextmanager
def get_db_connection() -> Generator[psycopg.Connection, None, None]:
    """Borrow a connection from the pool and automatically return it when done."""
    pool = get_pool()
    with pool.connection() as conn:
        yield conn


def check_db_health() -> bool:
    """Check whether the PostgreSQL database is reachable and accepting queries."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                row = cur.fetchone()
                return bool(row and row[0] == 1)
    except Exception:
        return False


def get_table_counts() -> dict[str, int]:
    """Return row counts for all core business tables."""
    tables = ("customers", "products", "orders", "order_items", "refunds")
    counts: dict[str, int] = {}
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for table in tables:
                cur.execute(f"SELECT COUNT(*) FROM {table};")
                row = cur.fetchone()
                counts[table] = row[0] if row else 0
    return counts
