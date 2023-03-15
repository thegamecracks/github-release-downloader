import sys

import click

from .main import main
from ..state import CLIState, pass_state
from ..utils import ask_for_auth

__all__ = ("download",)


@main.command()
@click.argument("owner")
@click.argument("repo")
@pass_state
def download(ctx: CLIState, owner: str, repo: str):
    """Download the first asset from the latest release in the given repository."""
    from ...client import ReleaseClient, create_client
    from ...database import ResponseCache, sessionmaker, get_user

    ctx.setup_database()

    with sessionmaker.begin() as session:
        user = get_user(session)
        auth = ask_for_auth(user)
        cache = ResponseCache(sessionmaker, expires_after=user.cache_expiry)

    with create_client(auth) as client:
        requester = ReleaseClient(client=client, cache=cache)

        release = requester.get_release(owner, repo)
        if not release.assets:
            sys.exit("no assets available")

        asset = release.assets[0]
        with open(asset.name, "xb") as f:
            print(f"Downloading {asset.name}")
            requester.download_asset_to(f, owner, repo, asset.id)
