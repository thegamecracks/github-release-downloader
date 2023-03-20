from __future__ import annotations

from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    from ..client.protocols import Stream


def stream_progress(stream: Stream) -> Iterator[bytes]:
    """Yields bytes from a stream while displaying a progress bar."""
    from tqdm import tqdm

    progress = tqdm(total=len(stream), unit="B", unit_scale=True)
    last = stream.progress()
    for data in stream:
        new = stream.progress()
        progress.update(new - last)
        last = new
        yield data
