from __future__ import annotations

from typing import TYPE_CHECKING, ContextManager, Iterator, Protocol

if TYPE_CHECKING:
    import httpx


class Stream(Protocol):
    def __len__(self) -> int:
        """Returns the total size of the stream."""
        ...

    def __iter__(self) -> Iterator[bytes]:
        """Returns an iterator of bytes."""
        ...

    def progress(self) -> int:
        """Returns the number of bytes yielded by the iterator.

        This should not exceed the value returned by :py:meth:`__len__`.

        """
        ...


class Streamable(ContextManager, Protocol):
    def __enter__(self) -> Stream:
        ...


class ResponseStream(Stream):
    def __init__(self, response: httpx.Response) -> None:
        self.response = response

    def __len__(self) -> int:
        return int(self.response.headers["Content-Length"])

    def __iter__(self) -> Iterator[bytes]:
        return self.response.iter_bytes()

    def progress(self) -> int:
        return self.response.num_bytes_downloaded


class ResponseStreamable(Streamable):
    def __init__(
        self,
        request: ContextManager[httpx.Response],
        *,
        raise_for_status: bool = True,
    ) -> None:
        self.request = request
        self.raise_for_status = raise_for_status

    def __enter__(self) -> ResponseStream:
        response = self.request.__enter__()

        if self.raise_for_status:
            response.raise_for_status()

        return ResponseStream(response)

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool | None:
        return self.request.__exit__(exc_type, exc_val, exc_tb)
