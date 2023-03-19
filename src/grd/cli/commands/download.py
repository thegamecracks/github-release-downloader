import sys

import click

from .main import main
from ..state import CLIState, pass_state

__all__ = ("download",)


@main.command()
@click.argument("owner")
@click.argument("repo")
@click.option(
    "-r",
    "--release",
    "tag",
    help="Find a release with the given tag name",
)
@pass_state
def download(ctx: CLIState, owner: str, repo: str, tag: str | None):
    """Download the first asset from a release in the given repository.

    The -r/--release option can be used to download assets from a specific
    release. Note that you must provide the *tag name*, not the title of
    the release itself. If the option is not specified, the latest release
    will be used.

    """
    from ...client import ReleaseClient, create_client

    with ctx.begin() as session:
        user = ctx.get_user(session)
        auth = ctx.ask_for_auth(user)
        cache = ctx.get_response_cache(user)

    with create_client(auth) as client:
        requester = ReleaseClient(client=client, cache=cache)

        if tag is not None:
            release = requester.get_release_by_tag(owner, repo, tag)
        else:
            release = requester.get_latest_release(owner, repo)

        if not release.assets:
            sys.exit("no assets available")

        asset = release.assets[0]
        with open(asset.name, "xb") as f:
            print(f"Downloading {asset.name}")
            requester.download_asset_to(f, owner, repo, asset.id)
