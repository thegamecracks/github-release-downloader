from __future__ import annotations

import contextlib

import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING, Iterator

from sqlalchemy import create_engine as sa_create_engine, event
from sqlalchemy.orm import sessionmaker as sa_sessionmaker

from . import engine_path
from .models import Base

if TYPE_CHECKING:
    from alembic.config import Config
    from sqlalchemy import Connection, Engine
    from sqlalchemy.engine.interfaces import DBAPICursor


# Listeners to apply various improvements to sqlite3 connections
# https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#foreign-key-support
# https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#serializable-isolation-savepoints-transactional-ddl
def _setup_sqlite_events(engine: Engine) -> None:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(conn: sqlite3.Connection, record):
        conn.isolation_level = None
        conn.execute("PRAGMA foreign_keys = on")

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


class SQLiteEncryptionManager:
    def __init__(self, engine: Engine, *, password: str | None = None):
        assert engine.dialect.name == "sqlite"
        self.engine = engine
        self.password = password
        self._setup_decrypt_hook()

    def decrypt_connection(self, conn: Connection, password: str) -> bool:
        """Decrypts the connection using the given password.

        :returns: True if the database was successfully decrypted, False otherwise.

        """
        escaped_password = self._escape_string(password)
        with self._raw_cursor(conn) as c:
            c.execute(f"PRAGMA key = '{escaped_password}'")
        return not self.is_encrypted(conn)

    def change_password(self, conn: Connection, new_password: str) -> None:
        """Changes the database password.

        The provided connection *must not* be in a transaction in order
        for this method to work.

        :raises sqlite3.DatabaseError: Database is encrypted or malformed.

        """
        if conn.in_transaction():
            raise RuntimeError(
                "Password cannot be changed while a transaction is active"
            )

        escaped_password = self._escape_string(new_password)
        is_encrypting = escaped_password != ""

        with self._raw_cursor(conn) as c:
            if is_encrypting:
                # Encryption requires a rollback journal
                c.execute("PRAGMA journal_mode = delete")

            c.execute(f"PRAGMA rekey = '{escaped_password}'")

    def is_encrypted(self, conn: Connection) -> bool:
        """Checks if the database is encrypted.

        The provided connection must come from the engine stored in this class.

        """
        self._check_same_engine(conn)
        try:
            with self._raw_cursor(conn) as c:
                c.execute("SELECT * FROM sqlite_schema")
        except sqlite3.DatabaseError:
            return True
        return False

    def supports_encryption(self, conn: Connection) -> bool:
        """Checks if the connection supports encryption.

        This method should only be called when the database has not yet been
        decrypted. If the database was decrypted, this method *will* cause
        the connection to go back into an encrypted state.

        The provided connection must come from the engine stored in this class.

        """
        self._check_same_engine(conn)
        # sqlcipher and SQLiteMultipleCiphers should return an ("ok",) row
        with self._raw_cursor(conn) as c:
            c.execute("PRAGMA key = ''")
            return c.fetchone() is not None

    def _setup_decrypt_hook(self) -> None:
        event.listen(self.engine, "engine_connect", self._decrypt_hook)

    def _decrypt_hook(self, conn: Connection) -> None:
        if not self.is_encrypted(conn):
            # Nothing to do
            return
        elif not self.supports_encryption(conn):
            # Can't decrypt database
            return
        elif self.password is None:
            # Missing password
            return
        else:
            self.decrypt_connection(conn, self.password)

    def _check_same_engine(self, conn: Connection):
        if conn.engine is not self.engine:
            raise ValueError("Connection is from a different engine")

    @contextlib.contextmanager
    def _raw_cursor(self, conn: Connection) -> Iterator[DBAPICursor]:
        """Returns a cursor directly from the DBAPI connection.

        This is useful for avoiding sqlalchemy's autobegin behaviour
        which cannot be disabled.

        """
        dbapi_conn = conn.connection.dbapi_connection
        assert dbapi_conn is not None
        c = dbapi_conn.cursor()
        try:
            yield c
        finally:
            c.close()

    @staticmethod
    def _escape_string(s: str) -> str:
        return s.replace("'", "''")


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
sqlite_encrypter = SQLiteEncryptionManager(engine_manager.engine)
engine = engine_manager.engine
sessionmaker = engine_manager.sessionmaker
