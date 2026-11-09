"""
PostgreSQL access. A connection *pool* keeps a few connections open and lends
them to requests, which is much faster than connecting for every request.
All times are handled in UTC so "this month" means the same thing everywhere.
"""
from contextlib import contextmanager
from pathlib import Path

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import settings

_pool: ConnectionPool | None = None


def _configure(conn):
    conn.execute("SET TIME ZONE 'UTC'")
    conn.commit()


def pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(settings.database_url, min_size=1, max_size=10, open=True,
                               configure=_configure, kwargs={"row_factory": dict_row})
    return _pool


@contextmanager
def connection():
    """Use as:  with connection() as conn: conn.execute(...)  (commits on success)."""
    with pool().connection() as conn:
        yield conn


def init_schema() -> None:
    sql = (Path(__file__).parent / "schema.sql").read_text()
    with connection() as conn:
        # Several API workers start at the same moment. A *transaction-level* advisory lock makes
        # them take turns, and is only released when the tables are committed, so the next
        # worker sees them. (A session-level lock released before COMMIT caused a race:
        # "relation customers already exists".)
        conn.execute("SELECT pg_advisory_xact_lock(424242)")
        conn.execute(sql)


def close() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None
