from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import Connection, Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker as sa_sessionmaker

from .cache import ResponseCache
from .models import Base, Response, User
from ..dirs import dirs

if TYPE_CHECKING:
    from alembic.config import Config

USER_ID = 1


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


def get_user(session: Session) -> User:
    """Gets the current user from the session."""
    user = session.get(User, USER_ID)
    if user is None:
        user = User(id=USER_ID)
        session.add(user)

    return user


def _get_alembic_config() -> Config:
    from alembic.config import Config

    # Ideally we'd use importlib.resources, but alembic inherently depends
    # on the filesystem anyway
    package = Path(__file__).parent.parent

    cfg = Config(package / "alembic.ini")
    cfg.set_main_option("script_location", str(package / "alembic"))

    return cfg


def setup_database():
    from alembic import command

    # Handle database migrations
    config = _get_alembic_config()

    if not engine_path.is_file():
        # Create the database and tell alembic we're on the latest revision
        engine_path.parent.mkdir(parents=True, exist_ok=True)
        Base.metadata.create_all(engine)
        command.stamp(config, "head")
    else:
        command.upgrade(config, "head")

    # Remove any expired responses
    with sessionmaker.begin() as session:
        user = get_user(session)
        cache = ResponseCache(sessionmaker, expires_after=user.cache_expiry)

    cache.clear(expired=True)


engine_path = Path(f"{dirs.user_data_dir}/data.db")
engine = create_engine(f"sqlite+pysqlite:///{engine_path}")
sessionmaker = sa_sessionmaker(engine)
