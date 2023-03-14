from typing import Iterator

import httpx
from tqdm import tqdm

BASE = "https://api.github.com"
HEADERS = {"X-GitHub-Api-Version": "2022-11-28"}


def create_client(auth: tuple[str, str]) -> httpx.Client:
    """Returns am :py:class:`httpx.Client` prepared for making GitHub requests."""
    return httpx.Client(auth=auth, base_url=BASE, headers=HEADERS)


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
