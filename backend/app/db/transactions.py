from collections.abc import Iterator
from contextlib import contextmanager
import sqlite3

from app.db.config import DatabaseConfig
from app.db.connection import connect


@contextmanager
def transaction(config: DatabaseConfig | None = None) -> Iterator[sqlite3.Connection]:
    """Open a SQLite transaction for service-level atomic writes.

    BEGIN IMMEDIATE takes SQLite's reserved write lock before service code runs,
    so production can re-check readiness and then write stock movements without
    another writer changing inventory between those steps.
    """
    connection = connect(config)
    try:
        connection.execute("BEGIN IMMEDIATE")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
