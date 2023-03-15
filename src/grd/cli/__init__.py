from __future__ import annotations

import datetime
import sys

import click

from .click_types import TimedeltaType
from .utils import ask_for_auth


@click.group(
    context_settings={
        "help_option_names": ["-h", "--help"],
    },
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity of the program.",
)
def main(verbose: int):
    from ..database import setup_database

    if verbose:
        import logging

        logging.basicConfig(
            format="%(levelname)s:%(name)s:%(message)s",
            level=logging.DEBUG,
        )

    setup_database()


@main.command()
def auth():
    """Update GitHub username and token authentication."""
    from ..database import data_session, get_user

    with data_session.begin() as session:
        user = get_user(session)

        click.echo(
            f"GitHub Username: {user.github_username or '<unset>'}\n"
            f"GitHub Token: {'*****' if user.github_token else '<unset>'}"
        )

        ask_for_auth(user, only_missing=False)


@main.group()
def cache() -> None:
    """Manage the response cache."""


@cache.command(name="clear")
def cache_clear() -> None:
    """Manually clear the response cache.

    This may be needed if there were release updates for a repository
    that was recently fetched.

    """
    from ..database import ResponseCache, data_session, get_user

    with data_session.begin() as session:
        user = get_user(session)
        cache = ResponseCache(data_session, expires_after=user.cache_expiry)
        cache.clear(expired=False)


@cache.command(name="expire")
@click.argument("duration", required=False, type=TimedeltaType())
@click.option("-u", "--unset", is_flag=True)
def cache_expire(duration: datetime.timedelta | None, unset: bool):
    """Sets the automatic cache expiration to the given duration.

    \b
    Examples:
        grd cache expire          # display the current duration
        grd cache expire 1d       # set the expiration to 1 day
        grd cache expire --unset  # disable time-based expiration
                                  # (not recommended)

    """
    from ..database import data_session, get_user

    with data_session.begin() as session:
        user = get_user(session)

        if unset:
            user.cache_expiry = None
        elif duration is not None:
            user.cache_expiry = duration
        elif user.cache_expiry is not None:
            click.echo(f"Response cache expires after: {user.cache_expiry}")
        else:
            click.echo("Response cache expiration is turned off")


@main.command()
@click.argument("owner")
@click.argument("repo")
def download(owner: str, repo: str):
    """Download the first asset from the latest release in the given repository."""
    from ..client import ReleaseClient, create_client
    from ..database import ResponseCache, data_session, get_user

    with data_session.begin() as session:
        user = get_user(session)
        auth = ask_for_auth(user)
        cache = ResponseCache(data_session, expires_after=user.cache_expiry)

    with create_client(auth) as client:
        requester = ReleaseClient(client=client, cache=cache)

        release = requester.get_release(owner, repo)
        if not release.assets:
            sys.exit("no assets available")

        asset = release.assets[0]
        with open(asset.name, "xb") as f:
            print(f"Downloading {asset.name}")
            requester.download_asset_to(f, owner, repo, asset.id)
