import json
import logging
import textwrap

import httpx
from tqdm import tqdm

__version__ = "0.1.0"

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


def stream_progress(response):
    progress = tqdm(
        total=int(response.headers["Content-Length"]),
        unit="B",
        unit_scale=True,
    )
    n_bytes = response.num_bytes_downloaded
    for data in response.iter_bytes():
        progress.update(response.num_bytes_downloaded - n_bytes)
        n_bytes = response.num_bytes_downloaded
        yield data


class ReleaseRequester:
    JSON_HEADERS = {"Accept": "application/vnd.github+json"}

    def __init__(self, client, owner, repo):
        self.client = client
        self.owner = owner
        self.repo = repo

    def get_release(self):
        response = self.client.get(
            f"/repos/{self.owner}/{self.repo}/releases/latest",
            headers=self.JSON_HEADERS,
        )
        return self._as_json(response)

    def get_release_assets(self, release_id):
        response = self.client.get(
            f"/repos/{self.owner}/{self.repo}/releases/{release_id}/assets",
            headers=self.JSON_HEADERS,
        )
        return self._as_json(response)

    def download_asset_to(self, file, asset_id):
        url = f"/repos/{self.owner}/{self.repo}/releases/assets/{asset_id}"
        headers = {"Accept": "application/octet-stream"}

        request = self.client.stream(
            "GET",
            url,
            follow_redirects=True,
            headers=headers,
        )

        with request as response:
            for data in stream_progress(response):
                file.write(data)

    def _as_json(self, response):
        data = response.json()
        logging.debug(
            "\n%s",
            textwrap.indent(json.dumps(data, indent=4), "    "),
        )
        assert response.status_code == 200
        return data


def main():
    with httpx.Client(auth=AUTH, base_url=BASE, headers=HEADERS) as client:
        requester = ReleaseRequester(client, OWNER, REPO)

        release = requester.get_release()
        release_id = release["id"]
        assets = requester.get_release_assets(release_id)
        if not assets:
            return print("no assets available")

        asset = assets[0]
        asset_name = asset["name"]
        with open(asset_name, "xb") as f:
            print(f"Downloading {asset_name}")
            requester.download_asset_to(f, asset["id"])
