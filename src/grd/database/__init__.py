import sqlite3
from pathlib import Path

from sqlalchemy import Connection, Engine, create_engine, event
from sqlalchemy.orm import sessionmaker

from .cache import ResponseCache
from .models import Base, Response, User
from ..appdirs import dirs


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


Path(dirs.user_data_dir).mkdir(parents=True, exist_ok=True)
data_engine = create_engine(f"sqlite+pysqlite:///{dirs.user_data_dir}/data.db")
data_session = sessionmaker(data_engine)
Base.metadata.create_all(data_engine)
