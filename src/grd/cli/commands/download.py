import sys

import click

from .main import main
from ..state import CLIState, pass_state

__all__ = ("download",)


@main.command()
@click.argument("owner")
@click.argument("repo")
@pass_state
def download(ctx: CLIState, owner: str, repo: str):
    """Download the first asset from the latest release in the given repository."""
    from ...client import ReleaseClient, create_client

    with ctx.begin() as session:
        user = ctx.get_user(session)
        auth = ctx.ask_for_auth(user)
        cache = ctx.get_response_cache(session)

    with create_client(auth) as client:
        requester = ReleaseClient(client=client, cache=cache)

        release = requester.get_release(owner, repo)
        if not release.assets:
            sys.exit("no assets available")

        asset = release.assets[0]
        with open(asset.name, "xb") as f:
            print(f"Downloading {asset.name}")
            requester.download_asset_to(f, owner, repo, asset.id)
