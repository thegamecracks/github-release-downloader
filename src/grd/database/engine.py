from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import Connection, Engine, create_engine, event
from sqlalchemy.orm import sessionmaker as sa_sessionmaker

from . import engine_path
from .models import Base

if TYPE_CHECKING:
    from alembic.config import Config


# Apply various improvements to sqlite3 connections
# https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#foreign-key-support
# https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#serializable-isolation-savepoints-transactional-ddl
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(conn: sqlite3.Connection, record):
    conn.isolation_level = None
    conn.execute("PRAGMA foreign_keys = on")
    conn.execute("PRAGMA journal_mode = wal")


@event.listens_for(Engine, "begin")
def do_begin(conn: Connection):
    conn.exec_driver_sql("BEGIN")


def _get_alembic_config() -> Config:
    from alembic.config import Config

    # Ideally we'd use importlib.resources, but alembic inherently depends
    # on the filesystem anyway
    package = Path(__file__).parent.parent

    cfg = Config(package / "alembic.ini")
    cfg.set_main_option("script_location", str(package / "alembic"))

    return cfg


def run_migrations():
    from alembic import command

    from .engine import engine

    config = _get_alembic_config()

    if not engine_path.is_file():
        # Create the database and tell alembic we're on the latest revision
        engine_path.parent.mkdir(parents=True, exist_ok=True)
        Base.metadata.create_all(engine)
        command.stamp(config, "head")
    else:
        command.upgrade(config, "head")


engine = create_engine(f"sqlite+pysqlite:///{engine_path}")
sessionmaker = sa_sessionmaker(engine)
