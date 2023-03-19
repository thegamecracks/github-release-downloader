from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:
    import httpx

    from .release import ReleaseClient
    from ..database.cache import ResponseCache
    from ..database.models import Response

log = logging.getLogger(__name__)

header_date_format = "%a, %d %b %Y %H:%M:%S %Z"


def _maybe_parse_datetime(s: str | None) -> datetime.datetime | None:
    if s is not None:
        dt = datetime.datetime.strptime(s, header_date_format)
        return dt.replace(tzinfo=datetime.timezone.utc)


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

    def cached_request(
        self,
        method: str,
        url: str,
        *args,
        headers: dict[str, Any] = {},
        **kwargs,
    ) -> Any:
        """Requests a potentially cached JSON response from the given endpoint.

        Extra arguments are passed to :py:meth:`httpx.Client.request()`.

        """
        key = self._get_cache_key(method, url)
        cache = self.cache.get(key)
        if cache is not None:
            self._add_cache_headers(headers, cache)

        response = self.client.request(method, url, *args, headers=headers, **kwargs)

        if response.status_code == 304:
            assert cache is not None
            return cache.value
        else:
            response.raise_for_status()

        data = response.json()
        self._update_cache(key, data, response.headers)

        return data

    def _update_cache(
        self,
        key: str,
        value: Any,
        headers: Mapping[str, str] = {},
    ) -> None:
        """Updates the cache for a particular response.

        Reference:
            https://docs.github.com/en/rest/overview/resources-in-the-rest-api#conditional-requests

        """
        date = _maybe_parse_datetime(headers.get("Last-Modified"))
        etag = headers.get("ETag")
        self.cache.set(key, value, modified_at=date, etag=etag)

    @staticmethod
    def _add_cache_headers(headers: dict[str, Any], cached: Response) -> None:
        """Mutates the headers according to the cached response to make it
        a conditional request.
        """
        if cached.etag is not None:
            log.debug("using ETag for conditional request")
            headers["If-None-Match"] = cached.etag
        elif cached.modified_at is not None:
            log.debug("using modified_at date for conditional request")
            headers["If-Modified-Since"] = cached.modified_at.strftime(header_date_format)
        else:
            log.debug("using created_at date for conditional request")
            headers["If-Modified-Since"] = cached.created_at.strftime(header_date_format)

    @staticmethod
    def _get_cache_key(method: str, url: str) -> str:
        """Creates a cache identifier for the given method and url."""
        return f"{method} {url}"
