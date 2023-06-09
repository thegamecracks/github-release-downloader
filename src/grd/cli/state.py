from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Literal

import click

if TYPE_CHECKING:
    from typing import ContextManager

    from sqlalchemy.orm import Session

    from ..database.cache import ResponseCache
    from ..database.models import User


class CLIState:
    def __init__(
        self,
        *,
        user_id: int = 1,
    ) -> None:
        self.user_id = user_id

        self.has_setup_database = False

        self._response_cache: ResponseCache | None = None

    def begin(self) -> ContextManager[Session]:
        """Starts an ORM session with the database.

        This method implicitly calls :py:meth:`setup_database()`.

        """
        self.setup_database()

        from ..database.engine import sessionmaker

        return sessionmaker.begin()

    def get_auth(self, user: User | None = None) -> str | None:
        """Retrieves the current user's API authentication credentials.

        Unlike :py:meth:`ask_for_auth()`, this method will not prompt
        to fill in credentials and instead displays a warning if
        insufficient credentials are available.

        """
        if user is None:
            with self.begin() as session:
                token = self.get_user(session).github_token
        else:
            self._check_user(user)
            token = user.github_token

        # NOTE: Token might be an empty string
        if token is not None and token:
            return token

        return None

    def get_response_cache(self, user: User | None = None) -> ResponseCache:
        """Gets a response cache instance.

        This method implicitly calls :py:meth:`setup_database()`.

        :param user:
            The user to take configuration values from. When providing this,
            the user ID must be the same as the :py:attr:`user_id` provided
            during class construction.
            If None, a session will be temporarily created to retrieve
            the current user.

        """
        if self._response_cache is not None:
            return self._response_cache

        self.setup_database()

        from ..client.cache import bucket_predicate
        from ..database.cache import ResponseCache
        from ..database.engine import sessionmaker

        if user is None:
            with self.begin() as session:
                user = self.get_user(session)
                cache_expiry = user.cache_expiry
        else:
            self._check_user(user)
            cache_expiry = user.cache_expiry

        self._response_cache = ResponseCache(
            sessionmaker,
            bucket_predicate=bucket_predicate,
            expires_after=cache_expiry,
        )
        return self._response_cache

    def get_user(self, session: Session) -> User:
        """Gets the current user from the session."""
        from ..database.models import User

        user = session.get(User, self.user_id)
        if user is None:
            user = User(id=self.user_id)
            session.add(user)

        return user

    def is_database_encrypted(self) -> bool:
        """Checks if the database is encrypted.

        If the database file does not exist, this returns False.

        If the database was decrypted before, this may also return False.
        As such, this method should not be relied upon after
        :py:meth:`setup_database()` is called.

        """
        from ..database.engine import engine_manager, sqlite_encrypter

        if not engine_manager.database_exists():
            return False

        with sqlite_encrypter.engine.connect() as conn:
            return sqlite_encrypter.is_encrypted(conn)

    def setup_database(self) -> None:
        """Sets up the database for the first time.

        This method is idempotent.

        """
        if self.has_setup_database:
            return

        if self.is_database_encrypted():
            self._decrypt_database()

        from ..database.engine import engine_manager

        engine_manager.run_migrations()

        self.has_setup_database = True

        # Remove any expired responses
        cache = self.get_response_cache()
        cache.clear(expired=True)

    def supports_encryption(self) -> bool:
        """Checks if the connection supports encryption.

        This method should only be called when the database has not yet been
        decrypted. If the database was decrypted, this method *will* cause
        the connection to go back into an encrypted state.

        """
        from ..database.engine import sqlite_encrypter

        with sqlite_encrypter.engine.connect() as conn:
            return sqlite_encrypter.supports_encryption(conn)

    def _check_user(self, user: User | None) -> Literal[True]:
        if user is not None and user.id != self.user_id:
            raise ValueError(
                f"Received user with ID {user.id} but expected ID {self.user_id}"
            )
        return True

    def _decrypt_database(self) -> None:
        from ..database.engine import sqlite_encrypter

        if not self.supports_encryption():
            sys.exit(
                "Database may be encrypted or malformed. If it is encrypted, "
                "the current SQLite library does not support decryption."
            )

        with sqlite_encrypter.engine.connect() as conn:
            from InquirerPy import inquirer

            password = inquirer.secret("Password to unlock database:").execute()
            if not sqlite_encrypter.decrypt_connection(conn, password):
                sys.exit("Invalid password. Database may be malformed?")


pass_state = click.make_pass_decorator(CLIState, ensure=True)
