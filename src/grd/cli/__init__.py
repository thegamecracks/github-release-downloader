from __future__ import annotations

import datetime

import sys

import click

from .utils import ask_for_auth, get_user

CACHE_EXPIRY = datetime.timedelta(days=1)


@click.group()
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity of the program.",
)
@click.pass_context
def main(ctx: click.Context, verbose: int):
    if verbose:
        import logging

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
    from ..client import ReleaseClient, create_client
    from ..database import ResponseCache, data_session

    with data_session.begin() as session:
        user = get_user(session)
        auth = ask_for_auth(user)

    with create_client(auth) as client:
        cache = ResponseCache(data_session)
        requester = ReleaseClient(
            client=client,
            cache=cache,
            cache_expiry=CACHE_EXPIRY,
        )

        release = requester.get_release(owner, repo)
        if not release.assets:
            sys.exit("no assets available")

        asset = release.assets[0]
        with open(asset.name, "xb") as f:
            print(f"Downloading {asset.name}")
            requester.download_asset_to(f, owner, repo, asset.id)
