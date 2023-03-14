import json
import logging
import textwrap
from typing import Any, BinaryIO, Iterator

import httpx
from tqdm import tqdm


def stream_progress(response: httpx.Response) -> Iterator[bytes]:
    """Yields bytes from a response while displaying a progress bar."""
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
    """Handles making requests to GitHub."""

    JSON_HEADERS = {"Accept": "application/vnd.github+json"}

    def __init__(self, client: httpx.Client, owner: str, repo: str):
        self.client = client
        self.owner = owner
        self.repo = repo

    def get_release(self) -> dict:
        """Gets the repository's latest release."""
        response = self.client.get(
            f"/repos/{self.owner}/{self.repo}/releases/latest",
            headers=self.JSON_HEADERS,
        )
        return self._as_json(response)

    def get_release_assets(self, release_id: int) -> list[dict]:
        """Gets a list of assets for the given release ID."""
        response = self.client.get(
            f"/repos/{self.owner}/{self.repo}/releases/{release_id}/assets",
            headers=self.JSON_HEADERS,
        )
        return self._as_json(response)

    def download_asset_to(self, file: BinaryIO, asset_id: int) -> None:
        """Downloads an asset to the given file."""
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

    def _as_json(self, response: httpx.Response) -> Any:
        data = response.json()
        logging.debug(
            "\n%s",
            textwrap.indent(json.dumps(data, indent=4), "    "),
        )
        assert response.status_code == 200
        return data
