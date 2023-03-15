import datetime
from typing import Any

from sqlalchemy import delete
from sqlalchemy.orm import Session, sessionmaker

from .models import Response


class ResponseCache:
    """Manages caching of responses.

    :param sessionmaker: The sessionmaker to use for fetching from cache.
    :param expires_after:
        The amount of time before a cache entry expires.
        If None, entries will never expire.

    """

    def __init__(
        self,
        sessionmaker: sessionmaker[Session],
        expires_after: datetime.timedelta | None = None,
    ) -> None:
        self.sessionmaker = sessionmaker
        self.expires_after = expires_after

    def clear(self, *, expired: bool) -> None:
        """Clears the response cache.

        :param expired:
            If True, deletes all cached entries.
            Otherwise, only deletes entries that have expired.

        """
        expires_at = self._get_expiry_date()
        query = delete(Response)

        if expired and expires_at is None:
            return
        elif expired:
            query = query.where(Response.created_at < expires_at)

        with self.sessionmaker.begin() as session:
            session.execute(query)

    def get(self, key: str) -> Any | None:
        """Looks for a response in the cache."""
        expires_at = self._get_expiry_date()

        with self.sessionmaker.begin() as session:
            response = session.get(Response, key)
            if response is None:
                return None
            elif expires_at is not None and response.created_at < expires_at:
                return None
            return response.value

    def set(self, key: str, value: str) -> None:
        """Sets a cached response for the given key."""
        with self.sessionmaker.begin() as session:
            response = Response(
                created_at=datetime.datetime.now(),
                key=key,
                value=value,
            )
            session.merge(response)

    def _get_expiry_date(self) -> datetime.datetime | None:
        if self.expires_after is None:
            return None
        return datetime.datetime.now().astimezone() - self.expires_after
