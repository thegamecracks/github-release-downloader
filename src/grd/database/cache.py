import contextlib
import datetime
from contextvars import ContextVar
from typing import Any, Callable, Generator, TypeVar

from sqlalchemy import delete
from sqlalchemy.orm import Session, sessionmaker

from .models import Response

T = TypeVar("T")

_bucket: ContextVar[set[str]] = ContextVar("_current_bucket")
"""Contains a set of keys that have been accessed by the cache in the current context."""


class ResponseCache:
    """Manages caching of responses.

    :param sessionmaker: The sessionmaker to use for fetching from cache.
    :param expires_after:
        The amount of time before a cache entry expires.
        If None, entries will never expire.
    :param bucket_predicate:
        A function that is called when an exception occurs
        inside the :py:meth:`bucket()` context manager.
        If it returns True, the bucket will not invalidate the cache.

    """

    def __init__(
        self,
        sessionmaker: sessionmaker[Session],
        *,
        bucket_predicate: Callable[[Exception], bool] | None = None,
        expires_after: datetime.timedelta | None = None,
    ) -> None:
        self.sessionmaker = sessionmaker
        self.expires_after = expires_after
        self.bucket_predicate = bucket_predicate

    @contextlib.contextmanager
    def bucket(self) -> Generator[set[str], None, None]:
        """Returns a context manager that can be used to encapsulate
        any accessed cache keys into a set.

        If an :py:exc:`Exception` occurs while the manager is open,
        all associated keys will be deleted from the cache unless
        :py:attr:`bucket_predicate` is not None and returns a truthy value.

        :py:exc:`BaseException`s are assumed to be part of control
        flow (like :py:exc:`KeyboardInterrupt`) and will not trigger
        cache invalidation.

        """
        keys: set[str] = set()
        token = _bucket.set(keys)
        try:
            yield keys
        except Exception as e:
            pred = self.bucket_predicate
            if pred is None or not pred(e):
                self.discard(*keys)
            raise
        finally:
            _bucket.reset(token)

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

    def discard(self, *keys: str) -> None:
        """Discards a set of keys from the cache."""
        query = delete(Response).where(Response.key.in_(keys))
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

            self._add_bucket_key(key)
            return response.value

    def set(self, key: str, value: Any) -> None:
        """Sets a cached response for the given key."""
        with self.sessionmaker.begin() as session:
            response = Response(
                created_at=datetime.datetime.now(),
                key=key,
                value=value,
            )
            session.merge(response)

        self._add_bucket_key(key)

    def _add_bucket_key(self, key: str) -> None:
        bucket = _bucket.get(None)
        if bucket is not None:
            bucket.add(key)

    def _get_expiry_date(self) -> datetime.datetime | None:
        if self.expires_after is None:
            return None
        return datetime.datetime.now().astimezone() - self.expires_after
