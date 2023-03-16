from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import create_engine as sa_create_engine, event
from sqlalchemy.orm import sessionmaker as sa_sessionmaker

from . import engine_path
from .models import Base

if TYPE_CHECKING:
    from alembic.config import Config
    from sqlalchemy import Connection, Engine


# Listeners to apply various improvements to sqlite3 connections
# https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#foreign-key-support
# https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#serializable-isolation-savepoints-transactional-ddl
def _setup_sqlite_events(engine: Engine) -> None:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(conn: sqlite3.Connection, record):
        conn.isolation_level = None
        conn.execute("PRAGMA foreign_keys = on")
        conn.execute("PRAGMA journal_mode = wal")

    @event.listens_for(engine, "begin")
    def do_begin(conn: Connection):
        conn.exec_driver_sql("BEGIN")


def create_engine(*args, **kwargs) -> Engine:
    """A wrapper over :py:func:`sqlalchemy.create_engine()` which handles
    extra configuration based on the dialect.
    """
    engine = sa_create_engine(*args, **kwargs)
    if engine.dialect.name == "sqlite":
        _setup_sqlite_events(engine)
    return engine


class SQLiteEngineManager:
    def __init__(self, path: Path):
        self.path = path
        self.engine = create_engine(f"sqlite+pysqlite:///{path}")
        self.sessionmaker = sa_sessionmaker(self.engine)

    def database_exists(self) -> bool:
        """Checks if the database exists on disk.

        After calling :py:meth:`run_migrations()`, this method should return True.

        """
        return self.path.is_file()

    def run_migrations(self) -> None:
        """Setup the database by running any necessary migrations."""
        from alembic import command

        config = self._get_alembic_config()

        if not self.database_exists():
            # Create the database and tell alembic we're on the latest revision
            engine_path.parent.mkdir(parents=True, exist_ok=True)
            Base.metadata.create_all(self.engine)
            command.stamp(config, "head")
        else:
            command.upgrade(config, "head")

    @staticmethod
    def _get_alembic_config() -> Config:
        from alembic.config import Config

        # Ideally we'd use importlib.resources, but alembic inherently depends
        # on the filesystem anyway
        package = Path(__file__).parent.parent

        cfg = Config(package / "alembic.ini")
        cfg.set_main_option("script_location", str(package / "alembic"))

        return cfg


engine_manager = SQLiteEngineManager(engine_path)
engine = engine_manager.engine
sessionmaker = engine_manager.sessionmaker
