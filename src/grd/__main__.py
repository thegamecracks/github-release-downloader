import logging
import sys

import httpx

from .client import ReleaseRequester

AUTH = (
    "<USERNAME>",
    "<GITHUB PERSONAL ACCESS TOKEN>",
)
BASE = "https://api.github.com"
HEADERS = {
    "X-GitHub-Api-Version": "2022-11-28",
}

OWNER = "<USERNAME>"
REPO = "<REPOSITORY>"

logging.basicConfig(
    format="%(levelname)s:%(name)s:%(message)s",
    level=logging.DEBUG,
)

with httpx.Client(auth=AUTH, base_url=BASE, headers=HEADERS) as client:
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
