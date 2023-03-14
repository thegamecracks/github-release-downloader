from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Literal, overload

import click

# Expensive imports
if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from ..database import User

USER_ID = 1


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


def get_user(session: Session) -> User:
    """
    Gets the user entry from the current session, inserting a default
    row if it does not already exist.
    """
    from ..database import User

    user = session.get(User, USER_ID)
    if user is None:
        user = User(id=USER_ID)
        session.add(user)

    return user


@click.group()
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increases verbosity of the program.",
)
@click.pass_context
def main(ctx: click.Context, verbose: int):
    if verbose:
        logging.basicConfig(
            format="%(levelname)s:%(name)s:%(message)s",
            level=logging.DEBUG,
        )


@main.command()
@click.option(
    "--prompt-missing",
    help="Only prompt for unset options",
    is_flag=True,
)
def auth(prompt_missing: bool):
    """Update GitHub username and token authentication."""
    from ..database import data_session

    with data_session.begin() as session:
        user = get_user(session)

        click.echo(
            f"GitHub Username: {user.github_username or '<unset>'}\n"
            f"GitHub Token: {'*****' if user.github_token else '<unset>'}"
        )

        ask_for_auth(user, only_missing=False)


@main.command()
@click.argument("owner")
@click.argument("repo")
def download(owner: str, repo: str):
    """Download the first asset from the latest release in the given repository."""
    from ..client import ReleaseRequester, create_client
    from ..database import data_session

    with data_session.begin() as session:
        user = get_user(session)

        auth = ask_for_auth(user)

    with create_client(auth) as client:
        requester = ReleaseRequester(client, owner, repo)

        release = requester.get_release()
        release_id = release["id"]
        assets = requester.get_release_assets(release_id)
        if not assets:
            sys.exit("no assets available")

        asset = assets[0]
        asset_name = asset["name"]
        with open(asset_name, "xb") as f:
            print(f"Downloading {asset_name}")
            requester.download_asset_to(f, asset["id"])
