import sys
from typing import Iterator

import httpx
from tqdm import tqdm

from .. import __qualname__, __version__, __url__

BASE = "https://api.github.com"
HEADERS = {
    "User-Agent": (
        f"{__qualname__}/{__version__} ({__url__}) "
        + "Python/{0.major}.{0.minor} ".format(sys.version_info)
        + f"httpx/{httpx.__version__}"
    ),
    "X-GitHub-Api-Version": "2022-11-28",
}


def create_client(*, token: str | None = None) -> httpx.Client:
    """Returns a :py:class:`httpx.Client` prepared for making GitHub requests."""
    headers = HEADERS.copy()
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"

    return httpx.Client(base_url=BASE, headers=headers)


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
