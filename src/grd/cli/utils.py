from __future__ import annotations

from typing import TYPE_CHECKING, Literal, overload

if TYPE_CHECKING:
    from ..database import User


@overload
def ask_for_auth(
    user: User, *, only_missing: Literal[False]
) -> tuple[str | None, str | None]:
    ...


@overload
def ask_for_auth(user: User, *, only_missing: Literal[True] = True) -> tuple[str, str]:
    ...


def ask_for_auth(user: User, *, only_missing: bool = True) -> tuple:
    """Prompts the user for credentials.

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

    if needs_token or inquirer.confirm("Do you want to update your token?").execute():
        token = inquirer.secret("Token:", mandatory=needs_token).execute()
        user.github_token = token

    return user.github_username, user.github_token
