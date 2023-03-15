from __future__ import annotations

from typing import TYPE_CHECKING, Literal, overload

import click

if TYPE_CHECKING:
    from typing import ContextManager

    from sqlalchemy.orm import Session

    from ..database import ResponseCache, User


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

        This method will set up the database if necessary.

        """
        self.setup_database()

        from ..database import sessionmaker

        return sessionmaker.begin()

    def get_response_cache(self, session: Session) -> ResponseCache:
        """Gets a response cache instance.

        This method will set up the database if necessary.

        :param session:
            The session that will be passed to :py:meth:`get_user()`.
            Once this returns, the session may be closed.

        """
        if self._response_cache is not None:
            return self._response_cache

        self.setup_database()

        from ..database import sessionmaker

        user = self.get_user(session)
        self._response_cache = ResponseCache(
            sessionmaker,
            expires_after=user.cache_expiry,
        )
        return self._response_cache

    def get_user(self, session: Session) -> User:
        """Gets the current user from the session."""
        user = session.get(User, self.user_id)
        if user is None:
            user = User(id=self.user_id)
            session.add(user)

        return user

    def setup_database(self) -> None:
        """Sets up the database for the first time.

        This method is idempotent.

        """
        if self.has_setup_database:
            return

        from ..database import run_migrations, sessionmaker

        run_migrations()

        # Remove any expired responses
        with sessionmaker.begin() as session:
            cache = self.get_response_cache(session)
            cache.clear(expired=True)

        self.has_setup_database = True


pass_state = click.make_pass_decorator(CLIState, ensure=True)
