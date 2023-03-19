from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, BinaryIO

import httpx
from pydantic import BaseModel

from .http import stream_progress

if TYPE_CHECKING:
    from ..database.cache import ResponseCache

log = logging.getLogger(__name__)


class Release(BaseModel):
    """Represents a release for a repository."""
    class Config:
        extras = "allow"

    assets: list[ReleaseAsset]
    id: int
    name: str


class ReleaseAsset(BaseModel):
    """An asset for a given release."""
    class Config:
        extras = "allow"

    id: int
    name: str


Release.update_forward_refs()


class ReleaseClient:
    """Handles retrieval of releases and assets.

    :param client:
        The client to use for making requests. This should be created from
        :py:func:`create_client()`.
    :param cache:
        The cache to fetch and store responses in.

    """

    JSON_HEADERS = {"Accept": "application/vnd.github+json"}

    def __init__(
        self,
        *,
        client: httpx.Client,
        cache: ResponseCache,
    ):
        self.client = client
        self.cache = cache

    def get_release_by_tag(self, owner: str, repo: str, tag: str) -> Release:
        """Gets a specific release from the repository by tag.

        The returned result may be cached.

        """
        response = self._cached_request(
            "GET",
            f"/repos/{owner}/{repo}/releases/tags/{tag}",
            headers=self.JSON_HEADERS,
        )
        return Release(**response)

    def get_latest_release(self, owner: str, repo: str) -> Release:
        """Gets the repository's latest release.

        The returned result may be cached.

        """
        response = self._cached_request(
            "GET",
            f"/repos/{owner}/{repo}/releases/latest",
            headers=self.JSON_HEADERS,
        )
        return Release(**response)

    def download_asset_to(self, file: BinaryIO, owner: str, repo: str, asset_id: int) -> None:
        """Downloads an asset to the given file.

        Unlike the other methods, this will always make an HTTP request.

        """
        request = self.client.stream(
            "GET",
            f"/repos/{owner}/{repo}/releases/assets/{asset_id}",
            follow_redirects=True,
            headers={"Accept": "application/octet-stream"},
        )

        with request as response:
            for data in stream_progress(response):
                file.write(data)

    def _cached_request(self, method: str, url: str, *args, **kwargs) -> Any:
        """Requests a potentially cached JSON response from the given endpoint.

        Extra arguments are passed to :py:meth:`httpx.Client.request()`.

        """
        key = self._get_cache_key(method, url)
        data = self.cache.get(key)
        cache_hit = data is not None

        if not cache_hit:
            response = self.client.request(method, url, *args, **kwargs)
            response.raise_for_status()

            data = response.json()
            assert data is not None
            self.cache.set(key, data)

        log.debug(
            "%s (%s)",
            key,
            "cache hit" if cache_hit else "cache miss",
        )
        return data

    @staticmethod
    def _get_cache_key(method: str, url: str) -> str:
        """Creates a cache identifier for the given method and url."""
        return f"{method} {url}"
