from __future__ import annotations

import sys
import textwrap
from typing import TYPE_CHECKING

import click

from .main import main
from ..errors import wrap_httpx_errors
from ..state import CLIState, pass_state
from ..streams import stream_progress

if TYPE_CHECKING:
    from ...client.models import ReleaseAsset

__all__ = ("download",)


def _find_asset(assets: list[ReleaseAsset], name: str) -> ReleaseAsset:
    for a in assets:
        if a.name == name:
            return a

    asset_names = textwrap.indent("\n".join(a.name for a in assets), "    ")
    sys.exit(
        f'Could not find any asset named "{name}"\n'
        "Available assets:\n"
        f"{asset_names}"
    )


def _select_asset(assets: list[ReleaseAsset]) -> ReleaseAsset:
    from InquirerPy import inquirer
    from InquirerPy.base.control import Choice

    assert len(assets) > 0

    return inquirer.select(
        "Select an asset to download:",
        [Choice(name=a.name, value=a) for a in assets],
    ).execute()


@main.command()
@click.argument("owner")
@click.argument("repo")
@click.option(
    "-r",
    "--release",
    "tag",
    help="Find a release with the given tag name",
)
@click.option(
    "-f",
    "--file",
    help="Immediately download the given filename",
)
@pass_state
@wrap_httpx_errors
def download(
    ctx: CLIState,
    owner: str,
    repo: str,
    tag: str | None,
    file: str | None,
):
    """Download the first asset from a release in the given repository.

    The -r/--release option can be used to download assets from a specific
    release. Note that you must provide the *tag name*, not the title of
    the release itself. If the option is not specified, the latest release
    will be used.

    """
    from ...client.base import BaseClient
    from ...client.http import create_client

    with ctx.begin() as session:
        user = ctx.get_user(session)
        token = ctx.get_auth(user)
        cache = ctx.get_response_cache(user)

    with cache.bucket(), create_client(token=token) as client:
        base = BaseClient(client=client, cache=cache)
        requester = base.get_release_client()

        if tag is not None:
            release = requester.get_release_by_tag(owner, repo, tag)
        else:
            release = requester.get_latest_release(owner, repo)

        if not release.assets:
            sys.exit("This release does not have any assets.")
        elif file is not None:
            asset = _find_asset(release.assets, file)
        else:
            asset = _select_asset(release.assets)

        with (
            open(asset.name, "xb") as f,
            requester.stream_asset(owner, repo, asset.id) as stream,
        ):
            for data in stream_progress(stream):
                f.write(data)
