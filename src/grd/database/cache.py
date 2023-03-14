import datetime
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from .models import Response


class ResponseCache:
    """Manages caching of responses."""

    def __init__(self, sessionmaker: sessionmaker[Session]) -> None:
        self.sessionmaker = sessionmaker

    def get(self, key: str, *, after: datetime.datetime | None = None) -> Any | None:
        """Looks for a response in the cache.

        :param key: The key to use for the response cache.
        :param after:
            If the cached response was not created after the given datetime,
            None is returned instead.

        """
        if after is not None and after.tzinfo is None:
            after = after.astimezone()

        with self.sessionmaker.begin() as session:
            response = session.get(Response, key)
            if response is None:
                return None
            elif after is not None and response.created_at < after:
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
