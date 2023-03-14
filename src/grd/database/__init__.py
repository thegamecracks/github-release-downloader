import sqlite3
from pathlib import Path

from sqlalchemy import Connection, Engine, create_engine, event
from sqlalchemy.orm import sessionmaker

from .cache import ResponseCache
from .models import Base, Response, User
from ..dirs import dirs


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


def setup_database():
    import importlib.resources

    from alembic.config import Config
    from alembic import command

    # Handle database migrations
    alembic_cfg_resource = importlib.resources.files("grd").joinpath("alembic.ini")
    with importlib.resources.as_file(alembic_cfg_resource) as path:
        alembic_cfg = Config(path)

        if not data_engine_path.is_file():
            # Create the database and tell alembic we're on the latest revision
            data_engine_path.parent.mkdir(parents=True, exist_ok=True)
            Base.metadata.create_all(data_engine)
            command.stamp(alembic_cfg, "head")
        else:
            command.upgrade(alembic_cfg, "head")


data_engine_path = Path(f"{dirs.user_data_dir}/data.db")
data_engine = create_engine(f"sqlite+pysqlite:///{data_engine_path}")
data_session = sessionmaker(data_engine)
