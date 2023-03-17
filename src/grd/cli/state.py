from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Literal, overload

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

    @overload
    def ask_for_auth(
        self, user: User, *, only_missing: Literal[False]
    ) -> tuple[str | None, str | None]:
        ...

    @overload
    def ask_for_auth(
        self, user: User, *, only_missing: Literal[True] = True
    ) -> tuple[str, str]:
        ...

    def ask_for_auth(self, user: User, *, only_missing: bool = True) -> tuple:
        """Prompts the user for credentials.

        :param user: The user to update credentials for.
        :param only_missing: If True, only asks for missing credentials.

        """
        needs_username = only_missing and not user.github_username
        needs_token = only_missing and not user.github_token

        if only_missing and not needs_username and not needs_token:
            return user.github_username, user.github_token

        from InquirerPy import inquirer

        if (
            needs_username
            or inquirer.confirm("Do you want to update your username?").execute()
        ):
            username = inquirer.text("Username:", mandatory=needs_username).execute()
            user.github_username = username

        if (
            needs_token
            or inquirer.confirm("Do you want to update your token?").execute()
        ):
            token = inquirer.secret("Token:", mandatory=needs_token).execute()
            user.github_token = token

        return user.github_username, user.github_token

    def begin(self) -> ContextManager[Session]:
        """Starts an ORM session with the database.

        This method implicitly calls :py:meth:`setup_database()`.

        """
        self.setup_database()

        from ..database.engine import sessionmaker

        return sessionmaker.begin()

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

        from ..database.cache import ResponseCache
        from ..database.engine import sessionmaker

        if user is None:
            with self.begin() as session:
                user = self.get_user(session)
                cache_expiry = user.cache_expiry
        elif user.id == self.user_id:
            cache_expiry = user.cache_expiry
        else:
            raise ValueError(
                f"Received user with ID {user.id} but expected ID {self.user_id}"
            )

        self._response_cache = ResponseCache(sessionmaker, expires_after=cache_expiry)
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

    def _decrypt_database(self) -> None:
        from ..database.engine import sqlite_encrypter

        with sqlite_encrypter.engine.connect() as conn:
            if not sqlite_encrypter.supports_encryption(conn):
                sys.exit(
                    "Database may be encrypted, but the underlying SQLite library "
                    "does not support encryption."
                )

            from InquirerPy import inquirer

            password = inquirer.secret("Database password:").execute()
            if not sqlite_encrypter.decrypt_connection(conn, password):
                sys.exit("Invalid password. Database may be malformed?")


pass_state = click.make_pass_decorator(CLIState, ensure=True)
