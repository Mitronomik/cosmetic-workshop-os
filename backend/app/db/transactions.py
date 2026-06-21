from collections.abc import Iterator
from contextlib import contextmanager
import sqlite3

from app.db.config import DatabaseConfig
from app.db.connection import connect


@contextmanager
def transaction(config: DatabaseConfig | None = None) -> Iterator[sqlite3.Connection]:
    """Open a SQLite transaction for service-level atomic writes."""
    connection = connect(config)
    try:
        connection.execute("BEGIN")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
