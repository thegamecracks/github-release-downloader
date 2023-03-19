from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import httpx

    from .release import ReleaseClient
    from ..database.cache import ResponseCache


class BaseClient:
    """The base client for making API requests to GitHub.

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

    def get_release_client(self) -> ReleaseClient:
        from .release import ReleaseClient

        return ReleaseClient(self)

    def cached_request(self, method: str, url: str, *args, **kwargs) -> Any:
        """Requests a potentially cached JSON response from the given endpoint.

        Extra arguments are passed to :py:meth:`httpx.Client.request()`.

        """
        key = self._get_cache_key(method, url)
        data = self.cache.get(key)

        if data is None:
            response = self.client.request(method, url, *args, **kwargs)
            response.raise_for_status()

            data = response.json()
            assert data is not None
            self.cache.set(key, data)

        return data

    @staticmethod
    def _get_cache_key(method: str, url: str) -> str:
        """Creates a cache identifier for the given method and url."""
        return f"{method} {url}"
