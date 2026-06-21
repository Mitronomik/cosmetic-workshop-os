from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
import sqlite3

from app.db.config import DatabaseConfig, get_database_config


def ensure_database_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def connect(config: DatabaseConfig | None = None) -> sqlite3.Connection:
    database_config = config or get_database_config()
    ensure_database_parent(database_config.path)
    connection = sqlite3.connect(database_config.path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def session(config: DatabaseConfig | None = None) -> Iterator[sqlite3.Connection]:
    connection = connect(config)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
