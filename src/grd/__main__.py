import logging
import sys

from .client import ReleaseRequester, create_client

AUTH = (
    "<USERNAME>",
    "<GITHUB PERSONAL ACCESS TOKEN>",
)

OWNER = "<USERNAME>"
REPO = "<REPOSITORY>"

logging.basicConfig(
    format="%(levelname)s:%(name)s:%(message)s",
    level=logging.DEBUG,
)

with create_client(AUTH) as client:
    requester = ReleaseRequester(client, OWNER, REPO)

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
